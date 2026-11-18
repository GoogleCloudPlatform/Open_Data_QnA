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

"""Unit regression tests for the PostgreSQL dry run of LLM-generated SQL.

PgConnector.test_sql_plan_execution must only *plan* the candidate statement. It used to
wrap it in EXPLAIN ANALYZE, which executes the statement, side effects included.
"""

import importlib.util
import os
import sys
import types
import unittest
from abc import ABC
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _FakeRow:
    def __init__(self, data):
        self._data = data

    def __str__(self):
        return "\n".join(f"{key}    {value}" for key, value in self._data.items())


class _FakeFrame:
    """Just enough of pandas.DataFrame for test_sql_plan_execution."""

    def __init__(self, data=None, index=None):
        self.data = dict(data or {})

    @property
    def empty(self):
        return not self.data

    @property
    def iloc(self):
        return [_FakeRow(self.data)]


def _load_pg_connector_module():
    """Loads a private copy of PgConnector.py with every third-party import faked."""
    fake_pandas = types.ModuleType("pandas")
    fake_pandas.DataFrame = _FakeFrame
    fake_pandas.read_sql = mock.MagicMock()

    fake_sqlalchemy = types.ModuleType("sqlalchemy")
    fake_sqlalchemy.create_engine = mock.MagicMock()
    fake_sqlalchemy_sql = types.ModuleType("sqlalchemy.sql")
    fake_sqlalchemy_sql.text = lambda statement: statement

    fake_utilities = types.ModuleType("utilities")
    fake_utilities.root_dir = REPO_ROOT

    fake_dbconnectors = types.ModuleType("dbconnectors")
    fake_dbconnectors.__path__ = []
    fake_dbconnectors.DBConnector = type("DBConnector", (ABC,), {})

    fakes = {
        "asyncpg": mock.MagicMock(),
        "google": mock.MagicMock(),
        "google.cloud": mock.MagicMock(),
        "google.cloud.sql": mock.MagicMock(),
        "google.cloud.sql.connector": mock.MagicMock(),
        "pgvector": mock.MagicMock(),
        "pgvector.asyncpg": mock.MagicMock(),
        "pg8000": mock.MagicMock(),
        "pg8000.exceptions": mock.MagicMock(),
        "pandas": fake_pandas,
        "sqlalchemy": fake_sqlalchemy,
        "sqlalchemy.sql": fake_sqlalchemy_sql,
        "utilities": fake_utilities,
        "dbconnectors": fake_dbconnectors,
    }
    spec = importlib.util.spec_from_file_location(
        "pg_connector_dry_run_under_test",
        os.path.join(REPO_ROOT, "dbconnectors", "PgConnector.py"),
    )
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, fakes):
        spec.loader.exec_module(module)
    return module


pg_mod = _load_pg_connector_module()


class TestSingleStatementForDryRun(unittest.TestCase):
    """The parser-free single statement check that runs before the dry run."""

    def test_accepts_one_statement_and_strips_trailing_terminators(self):
        for candidate, expected in [
            ("SELECT 1", "SELECT 1"),
            ("  SELECT 1;  ", "SELECT 1"),
            ("SELECT 1;;\n;", "SELECT 1"),
            ("WITH t AS (SELECT 1 AS a) SELECT a FROM t;", "WITH t AS (SELECT 1 AS a) SELECT a FROM t"),
        ]:
            with self.subTest(candidate=candidate):
                statement, error = pg_mod._single_statement_for_dry_run(candidate)
                self.assertIsNone(error)
                self.assertEqual(statement, expected)

    def test_rejects_stacked_statements(self):
        for candidate in [
            "SELECT 1; DELETE FROM users",
            "SELECT 1; COMMIT; DELETE FROM users",
            "SELECT 1;DROP TABLE users;",
            "SELECT 1; -- trailing comment",
        ]:
            with self.subTest(candidate=candidate):
                statement, error = pg_mod._single_statement_for_dry_run(candidate)
                self.assertIsNone(statement)
                self.assertIn("single SQL statement", error)

    def test_rejects_empty_or_non_string_input(self):
        for candidate in [None, "", "   ", ";", " ; ; ", 42, ["SELECT 1"]]:
            with self.subTest(candidate=candidate):
                statement, error = pg_mod._single_statement_for_dry_run(candidate)
                self.assertIsNone(statement)
                self.assertTrue(error)


class TestSqlPlanExecutionIsPlanOnly(unittest.TestCase):
    """test_sql_plan_execution must never ask PostgreSQL to execute the candidate."""

    def setUp(self):
        self.events = []
        self.connection = mock.MagicMock()
        self.connection.execute.side_effect = lambda statement: self.events.append(("execute", statement))
        self.connection.rollback.side_effect = lambda: self.events.append(("rollback",))

        pool = mock.MagicMock()
        pool.connect.return_value.__enter__.return_value = self.connection
        pool.connect.return_value.__exit__.return_value = False

        self.connector = object.__new__(pg_mod.PgConnector)
        self.connector.pool = pool

        self.read_sql_result = _FakeFrame({"QUERY PLAN": "Seq Scan on users"})
        self.read_sql_error = None

        def fake_read_sql(statement, con=None):
            self.events.append(("read_sql", statement))
            self.assertIs(con, self.connection)
            if self.read_sql_error is not None:
                raise self.read_sql_error
            return self.read_sql_result

        patcher = mock.patch.object(pg_mod.pd, "read_sql", side_effect=fake_read_sql)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _sent_to_database(self):
        return [event[1] for event in self.events if event[0] in ("execute", "read_sql")]

    def test_plans_without_analyze_inside_a_read_only_transaction(self):
        correct_sql, _ = self.connector.test_sql_plan_execution("SELECT * FROM users;")

        self.assertTrue(correct_sql)
        self.assertEqual(
            self.events,
            [
                ("execute", "SET TRANSACTION READ ONLY"),
                ("read_sql", "EXPLAIN (ANALYZE FALSE) SELECT * FROM users"),
                ("rollback",),
            ],
        )

    def test_never_sends_explain_analyze(self):
        for candidate in [
            "SELECT nextval('seq') FROM generate_series(1, 50)",
            "DELETE FROM users WHERE 1=1",
            "ANALYZE DELETE FROM users",
            "(ANALYZE) DELETE FROM users",
        ]:
            with self.subTest(candidate=candidate):
                self.events.clear()
                self.connector.test_sql_plan_execution(candidate)
                for statement in self._sent_to_database():
                    self.assertNotIn("EXPLAIN ANALYZE", statement.upper())
                    self.assertFalse(statement.upper().startswith("EXPLAIN (ANALYZE)"))
                self.assertEqual(self.events[1][1], "EXPLAIN (ANALYZE FALSE) " + candidate)

    def test_stacked_statements_never_reach_the_database(self):
        for candidate in [
            "SELECT 1; DELETE FROM users",
            "SELECT 1; COMMIT; DELETE FROM users",
        ]:
            with self.subTest(candidate=candidate):
                self.events.clear()
                correct_sql, feedback = self.connector.test_sql_plan_execution(candidate)

                self.assertFalse(correct_sql)
                self.assertEqual(self.events, [])
                self.connector.pool.connect.assert_not_called()
                self.assertIn("single SQL statement", str(feedback.iloc[0]))

    def test_database_error_is_reported_and_transaction_rolled_back(self):
        self.read_sql_error = RuntimeError('column "nope" does not exist')

        correct_sql, feedback = self.connector.test_sql_plan_execution("SELECT nope FROM users")

        self.assertFalse(correct_sql)
        self.assertTrue(str(feedback.iloc[0]).startswith("Error. Message"))
        self.assertIn("does not exist", str(feedback.iloc[0]))
        self.assertEqual(self.events[-1], ("rollback",))

    def test_empty_candidate_is_rejected_without_a_connection(self):
        correct_sql, _ = self.connector.test_sql_plan_execution("   ")

        self.assertFalse(correct_sql)
        self.connector.pool.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
