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

"""Unit tests for user_grouping SQL injection remediation and validation (b/565094378)."""

import asyncio
import importlib.util
import json
import os
import sys
import types
import unittest
from unittest import mock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Hermetic mocks for flask if not present
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

    mock_flask_mod.Flask = MockFlask
    mock_flask_mod.request = MockRequest()
    mock_flask_mod.jsonify = mock_jsonify
    mock_flask_mod.Response = MockResponse
    mock_flask_mod.render_template = mock.MagicMock()
    sys.modules["flask"] = mock_flask_mod

for mod in [
    "pandas",
    "flask_cors",
    "asyncpg",
    "pgvector",
    "pgvector.asyncpg",
    "pg8000",
    "pg8000.exceptions",
    "google.cloud.sql.connector",
    "google.auth",
    "sqlalchemy",
    "sqlalchemy.sql",
    "numpy",
    "langchain_community",
    "langchain_community.embeddings",
]:
    if mod not in sys.modules:
        sys.modules[mod] = mock.MagicMock()

# Mock google.cloud and google.cloud.bigquery
mock_bigquery = mock.MagicMock()


class MockScalarQueryParameter:
    """Mock implementation of bigquery.ScalarQueryParameter."""

    def __init__(self, name, type_, value):
        self.name = name
        self.type_ = type_
        self.value = value


class MockArrayQueryParameter:
    """Mock implementation of bigquery.ArrayQueryParameter."""

    def __init__(self, name, array_type, values):
        self.name = name
        self.array_type = array_type
        self.values = values


class MockQueryJobConfig:
    """Mock implementation of bigquery.QueryJobConfig."""

    def __init__(self, query_parameters=None, **kwargs):
        self.query_parameters = query_parameters or []
        for k, v in kwargs.items():
            setattr(self, k, v)


mock_bigquery.ScalarQueryParameter = MockScalarQueryParameter
mock_bigquery.ArrayQueryParameter = MockArrayQueryParameter
mock_bigquery.QueryJobConfig = MockQueryJobConfig

mock_google = types.ModuleType("google")
mock_google.__path__ = []
mock_gc = types.ModuleType("google.cloud")
mock_gc.__path__ = []
mock_gc.bigquery = mock_bigquery
mock_gc.bigquery_connection_v1 = mock.MagicMock()
mock_gc.exceptions = mock.MagicMock()

mock_google.cloud = mock_gc
sys.modules["google"] = mock_google
sys.modules["google.cloud"] = mock_gc
sys.modules["google.cloud.bigquery"] = mock_bigquery
sys.modules["google.cloud.bigquery_connection_v1"] = mock_gc.bigquery_connection_v1
sys.modules["google.cloud.exceptions"] = mock_gc.exceptions

# Mock firebase_admin
mock_firebase_admin = mock.MagicMock()
mock_auth = mock.MagicMock()
mock_firebase_admin.auth = mock_auth
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock.MagicMock()
sys.modules["firebase_admin.auth"] = mock_auth

# Mock DBConnector core
core_spec = importlib.util.spec_from_file_location(
    "dbconnectors.core", os.path.join(REPO_ROOT, "dbconnectors", "core.py")
)
core_mod = importlib.util.module_from_spec(core_spec)
sys.modules["dbconnectors.core"] = core_mod
core_spec.loader.exec_module(core_mod)

db_pkg = types.ModuleType("dbconnectors")
db_pkg.DBConnector = core_mod.DBConnector
db_pkg.bqconnector = mock.MagicMock()
db_pkg.pgconnector = mock.MagicMock()
db_pkg.firestoreconnector = mock.MagicMock()
sys.modules["dbconnectors"] = db_pkg

# Load BQConnector
bq_spec = importlib.util.spec_from_file_location(
    "dbconnectors.BQConnector", os.path.join(REPO_ROOT, "dbconnectors", "BQConnector.py")
)
bq_mod = importlib.util.module_from_spec(bq_spec)
sys.modules["dbconnectors.BQConnector"] = bq_mod
bq_spec.loader.exec_module(bq_mod)
BQConnector = bq_mod.BQConnector

# Load PgConnector
pg_spec = importlib.util.spec_from_file_location(
    "dbconnectors.PgConnector", os.path.join(REPO_ROOT, "dbconnectors", "PgConnector.py")
)
pg_mod = importlib.util.module_from_spec(pg_spec)
sys.modules["dbconnectors.PgConnector"] = pg_mod
pg_spec.loader.exec_module(pg_mod)
PgConnector = pg_mod.PgConnector

# Mock utilities, agents, and embeddings to load real opendataqna.py and store_embeddings.py
mock_utilities = types.ModuleType("utilities")
mock_utilities.PROJECT_ID = "test-project"
mock_utilities.PG_REGION = "us-central1"
mock_utilities.BQ_REGION = "us"
mock_utilities.EXAMPLES = ""
mock_utilities.LOGGING = False
mock_utilities.VECTOR_STORE = "bigquery-vector"
mock_utilities.BQ_OPENDATAQNA_DATASET_NAME = "opendataqna_ds"
mock_utilities.USE_SESSION_HISTORY = False
mock_utilities.root_dir = "/tmp"
mock_utilities.EMBEDDING_MODEL = "text-embedding-004"
mock_utilities.PG_INSTANCE = "inst"
mock_utilities.PG_DATABASE = "db"
mock_utilities.PG_USER = "user"
mock_utilities.PG_PASSWORD = "pass"
sys.modules["utilities"] = mock_utilities

mock_embedder_instance = mock.MagicMock()
mock_embedder_instance.create.return_value = [0.1, 0.2, 0.3]
mock_agents = types.ModuleType("agents")
for agent_name in ["BuildSQLAgent", "DebugSQLAgent", "ValidateSQLAgent", "ResponseAgent", "VisualizeAgent"]:
    setattr(mock_agents, agent_name, mock.MagicMock())
mock_agents.EmbedderAgent = mock.MagicMock(return_value=mock_embedder_instance)
sys.modules["agents"] = mock_agents

# Load real store_embeddings module
store_emb_spec = importlib.util.spec_from_file_location(
    "real_store_embeddings", os.path.join(REPO_ROOT, "embeddings", "store_embeddings.py")
)
real_store_embeddings = importlib.util.module_from_spec(store_emb_spec)
store_emb_spec.loader.exec_module(real_store_embeddings)

mock_emb = types.ModuleType("embeddings")
mock_store_emb = types.ModuleType("embeddings.store_embeddings")
mock_store_emb.add_sql_embedding = mock.AsyncMock()
mock_emb.store_embeddings = mock_store_emb
sys.modules["embeddings"] = mock_emb
sys.modules["embeddings.store_embeddings"] = mock_store_emb

# Load real opendataqna module
odq_spec = importlib.util.spec_from_file_location(
    "real_opendataqna", os.path.join(REPO_ROOT, "opendataqna.py")
)
real_opendataqna = importlib.util.module_from_spec(odq_spec)
odq_spec.loader.exec_module(real_opendataqna)

# Set up mock opendataqna for backend-apis/main.py
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

# Import backend-apis/main.py
main_path = os.path.abspath(os.path.join(REPO_ROOT, "backend-apis", "main.py"))
spec = importlib.util.spec_from_file_location("backend_apis_main_sqli", main_path)
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)


class TestUserGroupingValidation(unittest.TestCase):
    """Tests identifier validation for user_grouping and user_database."""

    def test_valid_user_grouping_identifiers(self):
        valid_cases = [
            "MovieExplorer-bigquery",
            "retail",
            "dataset_123",
            "project-123.dataset_name",
            "my_schema",
            "A",
            "test-group.sub_group",
        ]
        for name in valid_cases:
            with self.subTest(name=name):
                self.assertTrue(main_mod.is_valid_user_grouping(name))
                self.assertTrue(real_opendataqna.is_valid_user_grouping(name))

    def test_invalid_user_grouping_sql_injection_payloads(self):
        malicious_cases = [
            "' UNION SELECT 1, 2, 3 --",
            "retail'; DROP TABLE table_details_embeddings; --",
            "' OR '1'='1",
            "dataset' --",
            "dataset; SELECT * FROM credentials;",
            'dataset" OR 1=1',
            "<script>alert(1)</script>",
            "../../path/traversal",
            "dataset name with spaces",
            "dataset\nnewline",
            "",
            None,
            12345,
            "a" * 150,  # exceeds max length
        ]
        for payload in malicious_cases:
            with self.subTest(payload=payload):
                self.assertFalse(main_mod.is_valid_user_grouping(payload))
                self.assertFalse(real_opendataqna.is_valid_user_grouping(payload))


class TestApiUserGroupingRejection(unittest.TestCase):
    """Tests API rejection of SQL injection payloads in user_grouping."""

    def setUp(self):
        self.app = main_mod.app
        sys.modules["flask"].request.headers = {"Authorization": "Bearer valid-token"}
        mock_auth.verify_id_token.return_value = {"uid": "user_sec_test"}
        mock_opendataqna.get_results.reset_mock()
        mock_opendataqna.get_kgq.reset_mock()
        mock_opendataqna.generate_sql.reset_mock()
        mock_opendataqna.embed_sql.reset_mock()

    def test_run_query_rejects_sql_injection_in_user_grouping(self):
        payloads = [
            "' UNION SELECT 1 --",
            "test'; DROP TABLE users; --",
            "db' OR '1'='1",
            "db; DELETE FROM audit_log;",
        ]
        run_query_handler = self.app.routes["/run_query"]

        for payload in payloads:
            with self.subTest(payload=payload):
                sys.modules["flask"].request.data = json.dumps({
                    "user_question": "What is the total sales?",
                    "user_grouping": payload,
                    "generated_sql": "SELECT sum(sales) FROM sales_table",
                    "session_id": "sess_sqli",
                }).encode("utf-8")

                resp = run_query_handler()
                status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
                self.assertEqual(status_code, 400)
                mock_opendataqna.get_results.assert_not_called()

    def test_run_query_accepts_valid_user_grouping(self):
        run_query_handler = self.app.routes["/run_query"]
        sys.modules["flask"].request.data = json.dumps({
            "user_question": "What is the total sales?",
            "user_grouping": "retail-dataset",
            "generated_sql": "SELECT sum(sales) FROM sales_table",
            "session_id": "sess_sqli",
        }).encode("utf-8")

        resp = run_query_handler()
        data = resp.get_json()
        self.assertEqual(data.get("ResponseCode"), 200)
        mock_opendataqna.get_results.assert_called_once_with(
            "retail-dataset", "SELECT sum(sales) FROM sales_table"
        )

    def test_get_known_sql_rejects_sql_injection_in_user_grouping(self):
        handler = self.app.routes["/get_known_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_grouping": "' UNION SELECT * FROM example_prompt_sql_embeddings --"
        }).encode("utf-8")

        resp = handler()
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.get_kgq.assert_not_called()

    def test_get_results_rejects_sql_injection_in_user_database(self):
        handler = self.app.routes["/get_results"]
        sys.modules["flask"].request.data = json.dumps({
            "user_question": "test",
            "user_database": "' UNION SELECT 1 --"
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)

    def test_generate_sql_rejects_sql_injection_in_user_grouping(self):
        handler = self.app.routes["/generate_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_question": "What is total revenue?",
            "user_grouping": "' UNION SELECT 'bigquery' --",
            "session_id": "sess_123"
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.generate_sql.assert_not_called()

    def test_generate_sql_accepts_valid_user_grouping(self):
        handler = self.app.routes["/generate_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_question": "What is total revenue?",
            "user_grouping": "valid_dataset",
            "session_id": "sess_123"
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        data = resp.get_json()
        self.assertEqual(data.get("ResponseCode"), 200)
        mock_opendataqna.generate_sql.assert_called_once()

    def test_embed_sql_rejects_sql_injection_in_user_grouping(self):
        handler = self.app.routes["/embed_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_grouping": "' UNION SELECT * FROM example_prompt_sql_embeddings --",
            "user_question": "What is the total sales?",
            "generated_sql": "SELECT sum(sales) FROM sales_table",
            "session_id": "sess_embed",
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.embed_sql.assert_not_called()

    def test_embed_sql_rejects_invalid_user_question(self):
        handler = self.app.routes["/embed_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_grouping": "valid_ds",
            "user_question": "   ",
            "generated_sql": "SELECT sum(sales) FROM sales_table",
            "session_id": "sess_embed",
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.embed_sql.assert_not_called()

    def test_embed_sql_rejects_invalid_generated_sql(self):
        handler = self.app.routes["/embed_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_grouping": "valid_ds",
            "user_question": "What is the revenue?",
            "generated_sql": "   ",
            "session_id": "sess_embed",
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.embed_sql.assert_not_called()

    def test_embed_sql_rejects_prohibited_generated_sql(self):
        handler = self.app.routes["/embed_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_grouping": "valid_ds",
            "user_question": "What is the revenue?",
            "generated_sql": "DROP TABLE example_prompt_sql_embeddings;",
            "session_id": "sess_embed",
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        status_code = resp[1] if isinstance(resp, tuple) else resp.status_code
        self.assertEqual(status_code, 400)
        mock_opendataqna.embed_sql.assert_not_called()

    def test_embed_sql_accepts_valid_payload(self):
        handler = self.app.routes["/embed_sql"]
        sys.modules["flask"].request.data = json.dumps({
            "user_grouping": "valid_ds",
            "user_question": "What is total revenue?",
            "generated_sql": "SELECT sum(revenue) FROM orders",
            "session_id": "sess_embed",
        }).encode("utf-8")

        resp = handler()
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
        data = resp.get_json()
        self.assertEqual(data.get("ResponseCode"), 201)
        mock_opendataqna.embed_sql.assert_called_once()



class TestOpenDataQnAQueryParameterization(unittest.TestCase):
    """Tests parameterized query generation in opendataqna.py."""

    def test_opendataqna_get_source_type_rejects_malicious_input(self):
        result, is_invalid = real_opendataqna.get_source_type("' UNION SELECT 'bigquery' --")
        self.assertTrue(is_invalid)
        self.assertEqual(result, "Invalid user_grouping format")

        result, is_invalid = real_opendataqna.get_source_type("db; DROP TABLE tbl;")
        self.assertTrue(is_invalid)
        self.assertEqual(result, "Invalid user_grouping format")

    def test_opendataqna_get_source_type_uses_parameterized_query(self):
        with mock.patch.object(real_opendataqna, "vector_connector") as mock_vc:
            mock_df = mock.MagicMock()
            mock_df.iloc = mock.MagicMock()
            mock_df.iloc.__getitem__.return_value = "bigquery"
            mock_vc.retrieve_df.return_value = mock_df

            result, is_invalid = real_opendataqna.get_source_type("valid_dataset")
            self.assertFalse(is_invalid)
            self.assertEqual(result, "bigquery")
            mock_vc.retrieve_df.assert_called_once()
            called_args, called_kwargs = mock_vc.retrieve_df.call_args

            sql_arg = called_args[0]
            # Ensure SQL uses parameter placeholder rather than direct string interpolation
            self.assertIn("@user_grouping", sql_arg)
            self.assertNotIn("'valid_dataset'", sql_arg)
            self.assertIn("query_parameters", called_kwargs)
            params = called_kwargs["query_parameters"]
            self.assertEqual(params[0].value, "valid_dataset")

    def test_opendataqna_get_kgq_uses_parameterized_query(self):
        with mock.patch.object(real_opendataqna, "vector_connector") as mock_vc:
            mock_df = mock.MagicMock()
            mock_df.to_json.return_value = "[]"
            mock_vc.retrieve_df.return_value = mock_df

            result, is_invalid = real_opendataqna.get_kgq("valid_dataset")
            self.assertFalse(is_invalid)
            mock_vc.retrieve_df.assert_called_once()
            called_args, called_kwargs = mock_vc.retrieve_df.call_args

            sql_arg = called_args[0]
            self.assertIn("@user_grouping", sql_arg)
            self.assertNotIn("'valid_dataset'", sql_arg)
            self.assertIn("query_parameters", called_kwargs)


class TestConnectorParameterizedMethods(unittest.TestCase):
    """Tests retrieve_df and getExactMatches in BQConnector and PgConnector."""

    def test_bq_connector_retrieve_df_passes_job_config(self):
        with mock.patch.object(BQConnector, "getconn") as mock_getconn:
            mock_client = mock.MagicMock()
            mock_getconn.return_value = mock_client
            connector = BQConnector("proj", "reg", "ds", "audit")

            # Call without parameters
            connector.retrieve_df("SELECT 1")
            mock_client.query_and_wait.assert_called_with("SELECT 1", job_config=None)

            # Call with parameters
            params = [MockScalarQueryParameter("user_grouping", "STRING", "test_ds")]
            connector.retrieve_df("SELECT 1 WHERE x = @user_grouping", query_parameters=params)
            call_kwargs = mock_client.query_and_wait.call_args[1]
            self.assertIsNotNone(call_kwargs.get("job_config"))
            self.assertEqual(call_kwargs["job_config"].query_parameters, params)

    def test_bq_connector_get_exact_matches_parameterized(self):
        with mock.patch.object(BQConnector, "getconn") as mock_getconn:
            mock_client = mock.MagicMock()
            mock_df = mock.MagicMock()
            mock_df.columns = ["col"]
            mock_df.__getitem__.return_value.count.return_value = 0
            mock_client.query_and_wait.return_value.to_dataframe.return_value = mock_df
            mock_getconn.return_value = mock_client
            connector = BQConnector("proj", "reg", "ds", "audit")

            malicious_query = 'test" OR "1"="1'
            connector.getExactMatches(malicious_query)
            mock_client.query_and_wait.assert_called_once()
            called_sql = mock_client.query_and_wait.call_args[0][0]
            called_job_config = mock_client.query_and_wait.call_args[1].get("job_config")

            self.assertIn("@query", called_sql)
            self.assertNotIn(malicious_query, called_sql)
            self.assertIsNotNone(called_job_config)

    def test_pg_connector_retrieve_df_passes_params(self):
        with mock.patch("dbconnectors.PgConnector.create_engine") as mock_engine:
            mock_pool = mock.MagicMock()
            mock_engine.return_value = mock_pool
            with mock.patch("pandas.read_sql") as mock_read_sql:
                connector = PgConnector("proj", "reg", "inst", "db", "user", "pass")
                connector.retrieve_df("SELECT 1 WHERE x = :user_grouping", params={"user_grouping": "ds1"})
                mock_read_sql.assert_called_once()
                call_kwargs = mock_read_sql.call_args[1]
                self.assertEqual(call_kwargs.get("params"), {"user_grouping": "ds1"})


class TestBigQueryAddSqlEmbeddingSecurity(unittest.TestCase):
    """Tests parameterization and security of add_sql_embedding when using BigQuery."""

    def test_add_sql_embedding_bigquery_uses_parameterized_queries(self):
        mock_client = mock.MagicMock()
        with mock.patch.object(real_store_embeddings.bigquery, "Client", return_value=mock_client):
            malicious_database = "sales_db' OR '1'='1"
            malicious_question = 'What is total sales?" OR ""="" --'
            malicious_sql = 'SELECT * FROM sales; DROP TABLE example_prompt_sql_embeddings; --'

            result = asyncio.run(
                real_store_embeddings.add_sql_embedding(
                    malicious_question, malicious_sql, malicious_database
                )
            )
            self.assertEqual(result, 1)

            calls = mock_client.query_and_wait.call_args_list
            self.assertEqual(len(calls), 3)

            # Call 1: CREATE TABLE IF NOT EXISTS
            # Call 2: DELETE query
            delete_sql, delete_kwargs = calls[1][0][0], calls[1][1]
            self.assertIn("@database", delete_sql)
            self.assertIn("@user_question", delete_sql)
            self.assertNotIn(malicious_database, delete_sql)
            self.assertNotIn(malicious_question, delete_sql)

            delete_job_config = delete_kwargs.get("job_config")
            self.assertIsNotNone(delete_job_config)
            delete_params = {p.name: p.value for p in delete_job_config.query_parameters}
            self.assertEqual(delete_params.get("database"), malicious_database)
            self.assertEqual(delete_params.get("user_question"), malicious_question)

            # Call 3: INSERT query
            insert_sql, insert_kwargs = calls[2][0][0], calls[2][1]
            self.assertIn("@database", insert_sql)
            self.assertIn("@user_question", insert_sql)
            self.assertIn("@generated_sql", insert_sql)
            self.assertIn("@embedding", insert_sql)
            self.assertNotIn(malicious_database, insert_sql)
            self.assertNotIn(malicious_question, insert_sql)
            self.assertNotIn(malicious_sql, insert_sql)

            insert_job_config = insert_kwargs.get("job_config")
            self.assertIsNotNone(insert_job_config)
            insert_params = {p.name: getattr(p, "value", getattr(p, "values", None)) for p in insert_job_config.query_parameters}
            self.assertEqual(insert_params.get("database"), malicious_database)
            self.assertEqual(insert_params.get("user_question"), malicious_question)
            self.assertEqual(insert_params.get("generated_sql"), malicious_sql)
            self.assertEqual(insert_params.get("embedding"), [0.1, 0.2, 0.3])


class TestOpenDataQnAEmbedSqlGuards(unittest.TestCase):
    """Tests defensive input validation in real_opendataqna.embed_sql."""

    def test_embed_sql_rejects_invalid_inputs(self):
        # Invalid user_grouping
        res, is_err = asyncio.run(real_opendataqna.embed_sql("sess", "invalid grouping' --", "question", "SELECT 1"))
        self.assertTrue(is_err)
        self.assertIn("Invalid user_grouping", res)

        # Invalid user_question
        res, is_err = asyncio.run(real_opendataqna.embed_sql("sess", "valid_grouping", "   ", "SELECT 1"))
        self.assertTrue(is_err)
        self.assertIn("Invalid user_question", res)

        # Invalid generate_sql
        res, is_err = asyncio.run(real_opendataqna.embed_sql("sess", "valid_grouping", "question", ""))
        self.assertTrue(is_err)
        self.assertIn("Invalid generate_sql", res)


if __name__ == "__main__":
    unittest.main()
