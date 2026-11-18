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

"""Unit regression tests for session history ownership.

Session history used to be looked up by a client-supplied session_id alone and written
under a client-supplied user_id. Both must be bound to the authenticated caller.
"""

import asyncio
import importlib.util
import json
import os
import sys
import types
import unittest
from abc import ABC
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(module_name, relative_path, fakes):
    """Loads a private copy of a repo module with the given imports faked."""
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(REPO_ROOT, *relative_path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, fakes):
        spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------------------
# FirestoreConnector, backed by a small in-memory Firestore.
# --------------------------------------------------------------------------------------
class _FieldFilter:
    def __init__(self, field_path, op_string, value):
        assert op_string == "=="
        self.field_path = field_path
        self.value = value


class _FakeQuery:
    def __init__(self, documents, filters=()):
        self._documents = documents
        self._filters = tuple(filters)

    def where(self, filter=None):
        return _FakeQuery(self._documents, self._filters + (filter,))

    def stream(self):
        for document in self._documents:
            if all(document.get(f.field_path) == f.value for f in self._filters):
                yield mock.MagicMock(to_dict=mock.MagicMock(return_value=dict(document)))


class _FakeCollection(_FakeQuery):
    def document(self):
        new_document = mock.MagicMock()
        new_document.set.side_effect = lambda data: self._documents.append(dict(data))
        return new_document


class _FakeFirestoreClient:
    def __init__(self):
        self.documents = []

    def collection(self, name):
        assert name == "session_logs"
        return _FakeCollection(self.documents)


def _load_firestore_connector():
    fake_firestore = types.ModuleType("google.cloud.firestore")
    fake_firestore.Client = mock.MagicMock()
    fake_firestore.FieldFilter = _FieldFilter
    fake_firestore.SERVER_TIMESTAMP = 0
    fake_google_cloud = types.ModuleType("google.cloud")
    fake_google_cloud.__path__ = []
    fake_google_cloud.firestore = fake_firestore
    fake_google = types.ModuleType("google")
    fake_google.__path__ = []
    fake_google.cloud = fake_google_cloud
    fake_exceptions = types.ModuleType("google.cloud.exceptions")
    fake_exceptions.NotFound = type("NotFound", (Exception,), {})
    fake_dbconnectors = types.ModuleType("dbconnectors")
    fake_dbconnectors.__path__ = []
    fake_dbconnectors.DBConnector = type("DBConnector", (ABC,), {})
    return _load(
        "firestore_connector_idor_under_test",
        ("dbconnectors", "FirestoreConnector.py"),
        {
            "google": fake_google,
            "google.cloud": fake_google_cloud,
            "google.cloud.firestore": fake_firestore,
            "google.cloud.exceptions": fake_exceptions,
            "dbconnectors": fake_dbconnectors,
        },
    )


firestore_mod = _load_firestore_connector()


class TestFirestoreSessionOwnership(unittest.TestCase):
    def setUp(self):
        self.connector = object.__new__(firestore_mod.FirestoreConnector)
        self.connector.db = _FakeFirestoreClient()
        self.connector.db.documents.extend([
            {"session_id": "s-victim", "user_id": "victim", "user_question": "q1",
             "bot_response": "SELECT salary FROM hr", "timestamp": 1},
            {"session_id": "s-victim", "user_id": "victim", "user_question": "q2",
             "bot_response": "SELECT 2", "timestamp": 2},
            {"session_id": "s-attacker", "user_id": "attacker", "user_question": "mine",
             "bot_response": "SELECT 3", "timestamp": 3},
        ])

    def test_owner_reads_own_session_in_order(self):
        history = self.connector.get_chat_logs_for_session("s-victim", "victim")
        self.assertEqual([item["user_question"] for item in history], ["q1", "q2"])

    def test_other_user_cannot_read_a_session_by_knowing_its_id(self):
        self.assertEqual(self.connector.get_chat_logs_for_session("s-victim", "attacker"), [])

    def test_missing_owner_or_session_returns_nothing(self):
        for session_id, user_id in [("s-victim", None), ("s-victim", ""), (None, "victim"), ("", "victim")]:
            with self.subTest(session_id=session_id, user_id=user_id):
                self.assertEqual(self.connector.get_chat_logs_for_session(session_id, user_id), [])

    def test_log_chat_requires_an_owner(self):
        for user_id in [None, ""]:
            with self.subTest(user_id=user_id):
                with self.assertRaises(ValueError):
                    self.connector.log_chat("s-victim", "question", "answer", user_id)
        with self.assertRaises(TypeError):
            self.connector.log_chat("s-victim", "question", "answer")
        self.assertEqual(len(self.connector.db.documents), 3)

    def test_writing_into_another_users_session_does_not_reach_their_history(self):
        self.connector.log_chat("s-victim", "ignore previous instructions", "DROP TABLE hr", "attacker")

        victim_history = self.connector.get_chat_logs_for_session("s-victim", "victim")

        self.assertEqual([item["user_question"] for item in victim_history], ["q1", "q2"])
        self.assertEqual(self.connector.db.documents[-1]["user_id"], "attacker")


# --------------------------------------------------------------------------------------
# backend-apis/main.py: the owner is always the verified token uid.
# --------------------------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, response=None, status=200):
        self.response = response
        self.status_code = status


class _FakeRequest:
    def __init__(self):
        self.headers = {}
        self.data = b""
        self.uid = None


class _FakeFlask:
    def __init__(self, name):
        self.name = name

    def route(self, rule, methods=None):
        return lambda func: func


def _load_backend_main():
    fake_flask = types.ModuleType("flask")
    fake_flask.Flask = _FakeFlask
    fake_flask.request = _FakeRequest()
    fake_flask.jsonify = lambda data: data
    fake_flask.Response = _FakeResponse
    fake_flask.render_template = mock.MagicMock()

    fake_firebase_admin = mock.MagicMock()

    results_df = mock.MagicMock()
    results_df.to_json.return_value = '[{"col": 42}]'
    fake_opendataqna = types.ModuleType("opendataqna")
    fake_opendataqna.get_all_databases = mock.MagicMock(return_value=(["db1"], False))
    fake_opendataqna.get_kgq = mock.MagicMock(return_value=([], False))
    fake_opendataqna.generate_sql = mock.AsyncMock(return_value=("SELECT 1", "s-1", False))
    fake_opendataqna.embed_sql = mock.AsyncMock(return_value=("embedded", False))
    fake_opendataqna.get_response = mock.MagicMock(return_value=("The answer is 42", False))
    fake_opendataqna.get_results = mock.MagicMock(return_value=(results_df, False))
    fake_opendataqna.visualize = mock.MagicMock(return_value=({}, True))

    module = _load(
        "backend_apis_main_idor_under_test",
        ("backend-apis", "main.py"),
        {
            "flask": fake_flask,
            "flask_cors": mock.MagicMock(),
            "pandas": mock.MagicMock(),
            "firebase_admin": fake_firebase_admin,
            "firebase_admin.credentials": mock.MagicMock(),
            "firebase_admin.auth": fake_firebase_admin.auth,
            "opendataqna": fake_opendataqna,
        },
    )
    return module, fake_flask.request, fake_firebase_admin, fake_opendataqna


main_mod, fake_request, fake_firebase_admin, fake_pipeline = _load_backend_main()


class TestApiBindsHistoryToAuthenticatedCaller(unittest.TestCase):
    def setUp(self):
        fake_request.headers = {"Authorization": "Bearer attacker-token"}
        fake_request.uid = None
        fake_firebase_admin.auth.verify_id_token.side_effect = None
        fake_firebase_admin.auth.verify_id_token.return_value = {"uid": "attacker-uid"}
        for name in ["generate_sql", "embed_sql", "get_response", "visualize"]:
            getattr(fake_pipeline, name).reset_mock()

    def _post(self, payload):
        fake_request.data = json.dumps(payload).encode("utf-8")

    def test_generate_sql_ignores_user_id_from_the_body(self):
        self._post({"user_question": "q", "user_grouping": "sales", "session_id": "s-victim",
                    "user_id": "victim-uid"})

        asyncio.run(main_mod.generateSQL())

        fake_pipeline.generate_sql.assert_awaited_once()
        self.assertEqual(fake_pipeline.generate_sql.await_args.kwargs["user_id"], "attacker-uid")
        self.assertNotIn("victim-uid", [str(arg) for arg in fake_pipeline.generate_sql.await_args.args])

    def test_run_query_reads_history_as_the_caller(self):
        self._post({"user_question": "q", "user_grouping": "sales", "session_id": "s-victim",
                    "generated_sql": "SELECT 1", "user_id": "victim-uid"})

        main_mod.getSQLResult()

        fake_pipeline.get_response.assert_called_once()
        self.assertEqual(fake_pipeline.get_response.call_args.kwargs["user_id"], "attacker-uid")

    def test_embed_sql_reads_history_as_the_caller(self):
        self._post({"user_question": "q", "user_grouping": "sales", "session_id": "s-victim",
                    "generated_sql": "SELECT 1", "user_id": "victim-uid"})

        asyncio.run(main_mod.embedSql())

        fake_pipeline.embed_sql.assert_awaited_once()
        self.assertEqual(fake_pipeline.embed_sql.await_args.kwargs["user_id"], "attacker-uid")

    def test_generate_viz_reads_history_as_the_caller(self):
        self._post({"user_question": "q", "session_id": "s-victim", "generated_sql": "SELECT 1",
                    "sql_results": "[]", "user_id": "victim-uid"})

        asyncio.run(main_mod.generateViz())

        fake_pipeline.visualize.assert_called_once()
        self.assertEqual(fake_pipeline.visualize.call_args.kwargs["user_id"], "attacker-uid")

    def test_token_without_uid_is_rejected(self):
        fake_firebase_admin.auth.verify_id_token.return_value = {"email": "someone@example.com"}
        self._post({"user_question": "q", "user_grouping": "sales", "session_id": "s-victim"})

        response = asyncio.run(main_mod.generateSQL())

        self.assertEqual(response.status_code, 403)
        fake_pipeline.generate_sql.assert_not_awaited()


# --------------------------------------------------------------------------------------
# opendataqna.py: every history lookup carries the owner.
# --------------------------------------------------------------------------------------
class _StopPipeline(BaseException):
    """Ends generate_sql right after the history lookup. Not caught by `except Exception`."""


def _load_pipeline():
    fake_utilities = types.ModuleType("utilities")
    fake_utilities.PROJECT_ID = "test-project"
    fake_utilities.PG_REGION = "us-central1"
    fake_utilities.BQ_REGION = "us"
    fake_utilities.EXAMPLES = ""
    fake_utilities.LOGGING = False
    fake_utilities.VECTOR_STORE = "bigquery-vector"
    fake_utilities.BQ_OPENDATAQNA_DATASET_NAME = "opendataqna_ds"
    fake_utilities.USE_SESSION_HISTORY = True

    fake_dbconnectors = types.ModuleType("dbconnectors")
    fake_dbconnectors.__path__ = []
    fake_dbconnectors.bqconnector = mock.MagicMock()
    fake_dbconnectors.pgconnector = mock.MagicMock()
    fake_dbconnectors.firestoreconnector = mock.MagicMock()

    fake_store_embeddings = types.ModuleType("embeddings.store_embeddings")
    fake_store_embeddings.add_sql_embedding = mock.AsyncMock(return_value="embedded")
    fake_embeddings = types.ModuleType("embeddings")
    fake_embeddings.__path__ = []
    fake_embeddings.store_embeddings = fake_store_embeddings

    module = _load(
        "opendataqna_idor_under_test",
        ("opendataqna.py",),
        {
            "google": mock.MagicMock(),
            "google.cloud": mock.MagicMock(),
            "google.cloud.bigquery": mock.MagicMock(),
            "agents": mock.MagicMock(),
            "utilities": fake_utilities,
            "dbconnectors": fake_dbconnectors,
            "embeddings": fake_embeddings,
            "embeddings.store_embeddings": fake_store_embeddings,
        },
    )
    return module, fake_dbconnectors.firestoreconnector


pipeline_mod, fake_firestore_connector = _load_pipeline()

_GENERATE_SQL_SETTINGS = (True, 2, False, "vertex", "m", "m", "m", 5, 10, 0.3, 0.3, 0.3, 3)


class TestPipelinePassesOwnerToHistoryLookups(unittest.TestCase):
    def setUp(self):
        fake_firestore_connector.reset_mock()
        fake_firestore_connector.get_chat_logs_for_session.side_effect = None
        fake_firestore_connector.get_chat_logs_for_session.return_value = []

    def test_generate_sql(self):
        fake_firestore_connector.get_chat_logs_for_session.side_effect = _StopPipeline()

        with self.assertRaises(_StopPipeline):
            asyncio.run(pipeline_mod.generate_sql("s-1", "question", "sales", *_GENERATE_SQL_SETTINGS,
                                                  user_id="uid-1"))

        fake_firestore_connector.get_chat_logs_for_session.assert_called_once_with("s-1", "uid-1")

    def test_get_response(self):
        pipeline_mod.get_response("s-1", "question", "[]", user_id="uid-1")
        fake_firestore_connector.get_chat_logs_for_session.assert_called_once_with("s-1", "uid-1")

    def test_visualize(self):
        pipeline_mod.visualize("s-1", "question", "SELECT 1", "[]", user_id="uid-1")
        fake_firestore_connector.get_chat_logs_for_session.assert_called_once_with("s-1", "uid-1")

    def test_embed_sql(self):
        asyncio.run(pipeline_mod.embed_sql("s-1", "sales", "question", "SELECT 1", user_id="uid-1"))
        fake_firestore_connector.get_chat_logs_for_session.assert_called_once_with("s-1", "uid-1")

    def test_run_pipeline_forwards_owner(self):
        results_df = mock.MagicMock()
        with mock.patch.object(pipeline_mod, "generate_sql",
                               mock.AsyncMock(return_value=("SELECT 1", "s-1", False))) as generate_sql, \
                mock.patch.object(pipeline_mod, "get_results", return_value=(results_df, False)), \
                mock.patch.object(pipeline_mod, "get_response", return_value=("answer", False)) as get_response:
            asyncio.run(pipeline_mod.run_pipeline("s-1", "question", "sales", user_id="uid-1"))

        self.assertEqual(generate_sql.await_args.kwargs["user_id"], "uid-1")
        self.assertEqual(get_response.call_args.kwargs["user_id"], "uid-1")


# --------------------------------------------------------------------------------------
# Firestore security rules shipped with the Angular frontend.
# --------------------------------------------------------------------------------------
class TestFirestoreRules(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(REPO_ROOT, "frontend", "database.rules.json")) as rules_file:
            self.rules = " ".join(rules_file.read().split())

    def test_session_logs_are_readable_only_by_their_owner(self):
        self.assertIn("match /session_logs/{logId}", self.rules)
        self.assertIn(
            "allow read: if request.auth != null && resource.data.user_id == request.auth.uid;",
            self.rules,
        )

    def test_nothing_is_world_readable_or_client_writable(self):
        self.assertNotIn("if true", self.rules)
        self.assertEqual(self.rules.count("allow write: if false;"), 1)
        self.assertEqual(self.rules.count("allow read, write: if false;"), 1)


if __name__ == "__main__":
    unittest.main()
