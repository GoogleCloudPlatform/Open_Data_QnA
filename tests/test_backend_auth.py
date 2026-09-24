# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit regression tests for backend API authentication and SQL execution safety (b/565097433)."""

import importlib.util
import json
import os
import sys
import types
import unittest
from unittest import mock

# Set up lightweight hermetic mocks for Flask and third-party dependencies if not installed
if "flask" not in sys.modules:
    mock_flask_mod = types.ModuleType("flask")

    class MockResponse:
        def __init__(self, response=None, status=200):
            self.response = response
            self.status_code = status

        def get_json(self):
            if isinstance(self.response, str):
                try:
                    return json.loads(self.response)
                except Exception:
                    return None
            return self.response

    class MockRequest:
        def __init__(self):
            self.headers = {}
            self.data = b""
            self.uid = None

    class MockFlask:
        def __init__(self, name):
            self.name = name
            self.routes = {}

        def route(self, rule, methods=None):
            def decorator(func):
                self.routes[rule] = func
                return func
            return decorator

    def mock_jsonify(data):
        resp = MockResponse(response=json.dumps(data), status=200)
        resp._data = data
        resp.get_json = lambda: resp._data
        return resp

    mock_request = MockRequest()
    mock_flask_mod.Flask = MockFlask
    mock_flask_mod.request = mock_request
    mock_flask_mod.jsonify = mock_jsonify
    mock_flask_mod.Response = MockResponse
    mock_flask_mod.render_template = mock.MagicMock()
    sys.modules["flask"] = mock_flask_mod

for mod in ["pandas", "flask_cors"]:
    if mod not in sys.modules:
        sys.modules[mod] = mock.MagicMock()

# Mock firebase_admin before importing main
mock_firebase_admin = mock.MagicMock()
mock_auth = mock.MagicMock()
mock_firebase_admin.auth = mock_auth
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock.MagicMock()
sys.modules["firebase_admin.auth"] = mock_auth

# Mock opendataqna module
mock_opendataqna = types.ModuleType("opendataqna")
mock_opendataqna.get_all_databases = mock.MagicMock(return_value=(["db1"], False))
mock_opendataqna.get_kgq = mock.MagicMock(return_value=([], False))
mock_opendataqna.generate_sql = mock.AsyncMock(return_value=("SELECT 1", "session_123", False))
mock_opendataqna.embed_sql = mock.AsyncMock(return_value=("embedded", False))
mock_opendataqna.get_response = mock.MagicMock(return_value=("The answer is 42", False))
mock_results_df = mock.MagicMock()
mock_results_df.to_json.return_value = '[{"col": 42}]'
mock_opendataqna.get_results = mock.MagicMock(return_value=(mock_results_df, False))
mock_opendataqna.visualize = mock.MagicMock(return_value=("chart_js", False))
sys.modules["opendataqna"] = mock_opendataqna

# Dynamically import backend-apis/main.py
main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend-apis", "main.py"))
spec = importlib.util.spec_from_file_location("backend_apis_main", main_path)
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)


class TestBackendAuthAndSqlSafety(unittest.TestCase):
    """Tests authentication enforcement and query sanitization on backend APIs."""

    def setUp(self):
        self.app = main_mod.app
        sys.modules["flask"].request.headers = {}
        sys.modules["flask"].request.data = b""
        sys.modules["flask"].request.uid = None
        mock_auth.reset_mock()
        mock_auth.verify_id_token.side_effect = None
        mock_opendataqna.get_results.reset_mock()

    def test_is_safe_query_allows_select(self):
        safe_queries = [
            "SELECT * FROM dataset.table",
            "select count(*) from users where age > 18",
            "WITH recent AS (SELECT id FROM orders) SELECT * FROM recent",
            "```sql\nSELECT col FROM tbl\n```",
            "EXPLAIN SELECT 1",
            "/* Comment */ SELECT col FROM table WHERE x = 1 -- inline comment",
        ]
        for query in safe_queries:
            with self.subTest(query=query):
                is_safe, reason = main_mod.is_safe_query(query)
                self.assertTrue(is_safe, f"Query '{query}' should be safe, but failed with: {reason}")

    def test_is_safe_query_rejects_destructive_dml_ddl(self):
        dangerous_queries = [
            ("DROP TABLE users", "DROP"),
            ("DELETE FROM users WHERE 1=1", "DELETE"),
            ("UPDATE accounts SET balance = 0", "UPDATE"),
            ("INSERT INTO logs VALUES ('evil')", "INSERT"),
            ("ALTER TABLE users DROP COLUMN email", "ALTER"),
            ("TRUNCATE TABLE audit_log", "TRUNCATE"),
            ("CREATE TABLE backdoor (id INT)", "CREATE"),
            ("GRANT ALL ON dataset TO user", "GRANT"),
            ("SELECT * FROM users; DROP TABLE users;", "DROP"),
            ("EXEC sp_executesql 'evil'", "EXEC"),
            ("CALL my_procedure()", "CALL"),
        ]
        for query, expected_keyword in dangerous_queries:
            with self.subTest(query=query):
                is_safe, reason = main_mod.is_safe_query(query)
                self.assertFalse(is_safe, f"Query '{query}' should have been rejected")
                self.assertIn("Prohibited SQL operation", reason)

    def test_is_safe_query_rejects_non_select(self):
        invalid_queries = [
            "",
            None,
            "12345",
            "SHOW TABLES",
            "DESCRIBE users",
        ]
        for query in invalid_queries:
            with self.subTest(query=query):
                is_safe, reason = main_mod.is_safe_query(query)
                self.assertFalse(is_safe, f"Query '{query}' should be rejected")

    def test_verify_auth_header_missing_returns_401(self):
        sys.modules["flask"].request.headers = {}
        resp, uid = main_mod._verify_auth_header()
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 401)
        self.assertIsNone(uid)

    def test_verify_auth_header_malformed_returns_401(self):
        for bad_header in ["Bearer", "Basic token123", "Bearer a b c", "Invalid"]:
            with self.subTest(bad_header=bad_header):
                sys.modules["flask"].request.headers = {"Authorization": bad_header}
                resp, uid = main_mod._verify_auth_header()
                self.assertIsNotNone(resp)
                self.assertEqual(resp.status_code, 401)
                self.assertIsNone(uid)

    def test_verify_auth_header_invalid_token_returns_403(self):
        sys.modules["flask"].request.headers = {"Authorization": "Bearer bad-token"}
        mock_auth.verify_id_token.side_effect = Exception("Token expired or invalid signature")
        resp, uid = main_mod._verify_auth_header()
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 403)
        self.assertIsNone(uid)

    def test_verify_auth_header_valid_token_success(self):
        sys.modules["flask"].request.headers = {"Authorization": "Bearer valid-token-xyz"}
        mock_auth.verify_id_token.return_value = {"uid": "user_456"}
        resp, uid = main_mod._verify_auth_header()
        self.assertIsNone(resp)
        self.assertEqual(uid, "user_456")

    def test_run_query_unauthenticated_rejected(self):
        """Calling /run_query without Authorization header returns 401."""
        sys.modules["flask"].request.headers = {}
        run_query_handler = self.app.routes["/run_query"]
        resp = run_query_handler()
        self.assertEqual(resp.status_code, 401)
        mock_opendataqna.get_results.assert_not_called()

    def test_run_query_authenticated_destructive_sql_blocked(self):
        """Authenticated request with destructive SQL payload is blocked with 400 Bad Request."""
        sys.modules["flask"].request.headers = {"Authorization": "Bearer valid-token"}
        mock_auth.verify_id_token.return_value = {"uid": "user_123"}
        sys.modules["flask"].request.data = json.dumps({
            "user_question": "test",
            "user_grouping": "db",
            "generated_sql": "DROP TABLE users;",
            "session_id": "sess_1",
        }).encode("utf-8")

        run_query_handler = self.app.routes["/run_query"]
        resp = run_query_handler()
        # resp is either (json_resp, 400) or MockResponse with status_code=400
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.get_results.assert_not_called()

    def test_run_query_authenticated_valid_sql_success(self):
        """Authenticated request with valid read-only SQL query succeeds."""
        sys.modules["flask"].request.headers = {"Authorization": "Bearer valid-token"}
        mock_auth.verify_id_token.return_value = {"uid": "user_123"}
        sys.modules["flask"].request.data = json.dumps({
            "user_question": "How many records?",
            "user_grouping": "my_dataset",
            "generated_sql": "SELECT count(*) FROM my_dataset.records",
            "session_id": "sess_1",
        }).encode("utf-8")

        run_query_handler = self.app.routes["/run_query"]
        resp = run_query_handler()
        data = resp.get_json()
        self.assertEqual(data.get("ResponseCode"), 200)
        self.assertEqual(data.get("NaturalResponse"), "The answer is 42")
        mock_opendataqna.get_results.assert_called_once_with(
            "my_dataset", "SELECT count(*) FROM my_dataset.records"
        )

    def test_available_databases_requires_auth(self):
        """Calling /available_databases without Authorization header returns 401."""
        sys.modules["flask"].request.headers = {}
        handler = self.app.routes["/available_databases"]
        resp = handler()
        self.assertEqual(resp.status_code, 401)

        # With valid token:
        sys.modules["flask"].request.headers = {"Authorization": "Bearer valid-token"}
        mock_auth.verify_id_token.return_value = {"uid": "user_123"}
        resp = handler()
        self.assertEqual(resp.get_json().get("ResponseCode"), 200)


if __name__ == "__main__":
    unittest.main()
