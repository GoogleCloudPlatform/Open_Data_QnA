# Copyright 2024 Google LLC
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

"""Tests ensuring least-privilege IAM configuration and secure Cloud Run deployment."""

import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IAM_TF_PATH = os.path.join(REPO_ROOT, "terraform", "iam.tf")
VARIABLES_TF_PATH = os.path.join(REPO_ROOT, "terraform", "variables.tf")
BACKEND_DEPLOY_SH_PATH = os.path.join(REPO_ROOT, "terraform", "scripts", "backend-deployment.sh")
BACKEND_README_PATH = os.path.join(REPO_ROOT, "backend-apis", "README.md")


class TestIamLeastPrivilege(unittest.TestCase):
    """Verifies that IAM configuration strictly follows the principle of least privilege."""

    def test_iam_tf_avoids_overprivileged_roles(self):
        """Ensure terraform/iam.tf does not assign bigquery.admin or datastore.owner."""
        self.assertTrue(os.path.exists(IAM_TF_PATH), f"{IAM_TF_PATH} must exist")
        with open(IAM_TF_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn(
            "roles/bigquery.admin",
            content,
            "terraform/iam.tf must not assign over-privileged 'roles/bigquery.admin'",
        )
        self.assertNotIn(
            "roles/datastore.owner",
            content,
            "terraform/iam.tf must not assign over-privileged 'roles/datastore.owner'",
        )

    def test_iam_tf_assigns_least_privilege_roles(self):
        """Ensure terraform/iam.tf assigns least-privilege roles to genai_cloudrun_service_account."""
        with open(IAM_TF_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        required_roles = [
            "roles/bigquery.jobUser",
            "roles/bigquery.dataEditor",
            "roles/datastore.user",
            "roles/cloudsql.client",
            "roles/aiplatform.user",
        ]
        for role in required_roles:
            with self.subTest(role=role):
                self.assertIn(
                    role,
                    content,
                    f"terraform/iam.tf must include least-privilege role '{role}'",
                )

    def test_iam_tf_guards_unauthenticated_invoker(self):
        """Ensure allUsers Cloud Run invoker binding is guarded by allow_unauthenticated_invoker."""
        with open(IAM_TF_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the google_cloud_run_service_iam_member "invoker" block
        pattern = r'resource\s+"google_cloud_run_service_iam_member"\s+"invoker"\s*\{([^}]+)\}'
        match = re.search(pattern, content)
        self.assertIsNotNone(match, "google_cloud_run_service_iam_member 'invoker' block must exist")
        invoker_block = match.group(1)

        self.assertIn(
            "var.allow_unauthenticated_invoker",
            invoker_block,
            "Invoker resource must be guarded by var.allow_unauthenticated_invoker",
        )

    def test_variables_tf_defaults_unauthenticated_invoker_to_false(self):
        """Ensure terraform/variables.tf defines allow_unauthenticated_invoker defaulting to false."""
        self.assertTrue(os.path.exists(VARIABLES_TF_PATH), f"{VARIABLES_TF_PATH} must exist")
        with open(VARIABLES_TF_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'variable\s+"allow_unauthenticated_invoker"\s*\{([^}]+)\}'
        match = re.search(pattern, content)
        self.assertIsNotNone(match, "variable 'allow_unauthenticated_invoker' must be defined")
        var_block = match.group(1)

        self.assertIsNotNone(
            re.search(r"default\s*=\s*false", var_block),
            "allow_unauthenticated_invoker must default to false",
        )

    def test_backend_deployment_script_no_allow_unauthenticated(self):
        """Ensure backend-deployment.sh deploys with --no-allow-unauthenticated."""
        self.assertTrue(os.path.exists(BACKEND_DEPLOY_SH_PATH), f"{BACKEND_DEPLOY_SH_PATH} must exist")
        with open(BACKEND_DEPLOY_SH_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn(
            "--allow-unauthenticated",
            content.replace("--no-allow-unauthenticated", ""),
            "backend-deployment.sh must not contain '--allow-unauthenticated'",
        )
        self.assertIn(
            "--no-allow-unauthenticated",
            content,
            "backend-deployment.sh must contain '--no-allow-unauthenticated'",
        )

    def test_backend_readme_recommends_least_privilege_roles(self):
        """Ensure backend-apis/README.md does not recommend overprivileged roles."""
        self.assertTrue(os.path.exists(BACKEND_README_PATH), f"{BACKEND_README_PATH} must exist")
        with open(BACKEND_README_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("roles/bigquery.admin", content)
        self.assertNotIn("roles/datastore.owner", content)
        self.assertIn("roles/bigquery.jobUser", content)
        self.assertIn("roles/bigquery.dataEditor", content)
        self.assertIn("roles/datastore.user", content)
        self.assertIn("--no-allow-unauthenticated", content)


if __name__ == "__main__":
    unittest.main()
