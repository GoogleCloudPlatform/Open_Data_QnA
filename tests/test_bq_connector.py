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

"""Unit regression tests for BQConnector.retrieve_matches (b/565101328)."""

import importlib.util
import os
import sys
import types
import unittest
from unittest import mock

# Set up mocks for external packages to make tests 100% self-contained
for pkg in ["google", "google.cloud"]:
    if pkg not in sys.modules:
        m = types.ModuleType(pkg)
        m.__path__ = []
        sys.modules[pkg] = m

mock_bigquery = mock.MagicMock()


class MockScalarQueryParameter:
    """Mock implementation of bigquery.ScalarQueryParameter."""

    def __init__(self, name, type_, value):
        self.name = name
        self.type_ = type_
        self.value = value


class MockQueryJobConfig:
    """Mock implementation of bigquery.QueryJobConfig."""

    def __init__(self, query_parameters=None, **kwargs):
        self.query_parameters = query_parameters or []
        for k, v in kwargs.items():
            setattr(self, k, v)


mock_bigquery.ScalarQueryParameter = MockScalarQueryParameter
mock_bigquery.QueryJobConfig = MockQueryJobConfig
sys.modules["google.cloud.bigquery"] = mock_bigquery

for mod in [
    "pandas",
    "google.auth",
    "google.cloud.bigquery_connection_v1",
    "google.cloud.exceptions",
]:
    if mod not in sys.modules:
        sys.modules[mod] = mock.MagicMock()

# Load dbconnectors.core without running dbconnectors/__init__.py
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
core_spec = importlib.util.spec_from_file_location(
    "dbconnectors.core", os.path.join(REPO_ROOT, "dbconnectors", "core.py")
)
core_mod = importlib.util.module_from_spec(core_spec)
sys.modules["dbconnectors.core"] = core_mod
core_spec.loader.exec_module(core_mod)

db_pkg = types.ModuleType("dbconnectors")
db_pkg.DBConnector = core_mod.DBConnector
sys.modules["dbconnectors"] = db_pkg

# Load dbconnectors.BQConnector
bq_spec = importlib.util.spec_from_file_location(
    "dbconnectors.BQConnector",
    os.path.join(REPO_ROOT, "dbconnectors", "BQConnector.py"),
)
bq_mod = importlib.util.module_from_spec(bq_spec)
sys.modules["dbconnectors.BQConnector"] = bq_mod
bq_spec.loader.exec_module(bq_mod)

BQConnector = bq_mod.BQConnector


class TestBQConnectorRetrieveMatches(unittest.TestCase):
    """Tests for BQConnector retrieve_matches parameterization and security."""

    def setUp(self):
        self.mock_client = mock.MagicMock()
        with mock.patch("google.auth.default", return_value=(mock.MagicMock(), "test-project")):
            self.connector = BQConnector(
                project_id="test-project",
                region="us-central1",
                opendataqna_dataset="test_dataset",
                audit_log_table_name="audit_logs",
            )
        self.connector.client = self.mock_client

    def test_retrieve_matches_table_parameterization(self):
        """Verifies that retrieve_matches parameterizes user_grouping for table mode."""
        mock_df = mock.MagicMock()
        mock_df.__len__.return_value = 1
        mock_df.iterrows.return_value = iter([(0, {"tables_content": "table1 schema"})])
        mock_query_job = mock.MagicMock()
        mock_query_job.to_dataframe.return_value = mock_df
        self.mock_client.query_and_wait.return_value = mock_query_job

        user_grouping = "marketing_team"
        results = self.connector.retrieve_matches(
            mode="table",
            user_grouping=user_grouping,
            qe="[0.1, 0.2, 0.3]",
            similarity_threshold=0.7,
            limit=5,
        )

        self.mock_client.query_and_wait.assert_called_once()
        sql_arg, kwargs = self.mock_client.query_and_wait.call_args

        # Assert query uses @user_grouping parameter placeholder instead of string interpolation
        self.assertIn("WHERE user_grouping = @user_grouping", sql_arg[0])
        self.assertNotIn(f"WHERE user_grouping = '{user_grouping}'", sql_arg[0])

        # Assert job_config contains ScalarQueryParameter for user_grouping
        job_config = kwargs.get("job_config")
        self.assertIsNotNone(job_config)
        param_names = [p.name for p in job_config.query_parameters]
        self.assertIn("user_grouping", param_names)

        user_param = next(
            p for p in job_config.query_parameters if p.name == "user_grouping"
        )
        self.assertEqual(user_param.value, user_grouping)
        self.assertEqual(user_param.type_, "STRING")

    def test_retrieve_matches_sql_injection_payload_sanitized(self):
        """Verifies that SQL injection payload in user_grouping is not interpolated into SQL."""
        mock_df = mock.MagicMock()
        mock_df.__len__.return_value = 0
        mock_query_job = mock.MagicMock()
        mock_query_job.to_dataframe.return_value = mock_df
        self.mock_client.query_and_wait.return_value = mock_query_job

        malicious_payload = "marketing') OR 1=1; DROP TABLE embeddings; --"
        self.connector.retrieve_matches(
            mode="table",
            user_grouping=malicious_payload,
            qe="[0.1, 0.2, 0.3]",
            similarity_threshold=0.5,
            limit=10,
        )

        sql_arg, kwargs = self.mock_client.query_and_wait.call_args
        sql_query = sql_arg[0]

        # Raw query MUST NOT contain the malicious payload fragments
        self.assertNotIn("DROP TABLE", sql_query)
        self.assertNotIn("1=1", sql_query)
        self.assertIn("WHERE user_grouping = @user_grouping", sql_query)

        # The payload must be passed safely through query_parameters
        job_config = kwargs.get("job_config")
        user_param = next(
            p for p in job_config.query_parameters if p.name == "user_grouping"
        )
        self.assertEqual(user_param.value, malicious_payload)

    def test_retrieve_matches_column_and_example_modes(self):
        """Verifies that column and example modes also use parameterized queries."""
        mock_df = mock.MagicMock()
        mock_df.__len__.return_value = 0
        mock_query_job = mock.MagicMock()
        mock_query_job.to_dataframe.return_value = mock_df
        self.mock_client.query_and_wait.return_value = mock_query_job

        for mode, table_name in [
            ("column", "tablecolumn_details_embeddings"),
            ("example", "example_prompt_sql_embeddings"),
        ]:
            self.mock_client.query_and_wait.reset_mock()
            self.connector.retrieve_matches(
                mode=mode,
                user_grouping="sales",
                qe="[0.5]",
                similarity_threshold=0.8,
                limit=3,
            )

            sql_arg, kwargs = self.mock_client.query_and_wait.call_args
            self.assertIn(table_name, sql_arg[0])
            self.assertIn("WHERE user_grouping = @user_grouping", sql_arg[0])
            self.assertNotIn("WHERE user_grouping = 'sales'", sql_arg[0])

            job_config = kwargs.get("job_config")
            user_param = next(
                p
                for p in job_config.query_parameters
                if p.name == "user_grouping"
            )
            self.assertEqual(user_param.value, "sales")

    def test_retrieve_matches_invalid_mode_raises(self):
        """Verifies that an unsupported mode raises ValueError."""
        with self.assertRaises(ValueError):
            self.connector.retrieve_matches(
                mode="invalid_mode",
                user_grouping="test",
                qe="[]",
                similarity_threshold=0.5,
                limit=5,
            )


if __name__ == "__main__":
    unittest.main()
