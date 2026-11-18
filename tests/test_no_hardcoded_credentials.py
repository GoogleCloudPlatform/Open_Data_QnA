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

"""Regression tests that keep credentials out of the repository.

Database passwords used to be committed as defaults in config.ini, env_setup.py, the
notebooks and Terraform, and the Flutter app shipped the Firebase configuration of live
projects. These tests fail if a credential-shaped value comes back.
"""

import configparser
import importlib.util
import json
import os
import plistlib
import re
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A string literal assigned to a password variable, in Python or inside notebook JSON.
PASSWORD_LITERAL = re.compile(r"""(?i)\bpg_password\s*=\s*\\?["'][^"'\\\s<][^"'\\]*""")
# The shape of a Google API key.
GOOGLE_API_KEY = re.compile(r"AIza[0-9A-Za-z_\-]{35}")


def _read(*relative_path):
    with open(os.path.join(REPO_ROOT, *relative_path), encoding="utf-8") as source:
        return source.read()


class TestConfigIniTemplate(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(REPO_ROOT, "config.ini"))

    def test_no_password_is_committed(self):
        self.assertEqual(self.config["PGCLOUDSQL"]["pg_password"], "")

    def test_no_project_is_committed(self):
        self.assertEqual(self.config["GCP"]["project_id"], "")


class TestPasswordComesFromTheEnvironment(unittest.TestCase):
    """utilities reads PG_PASSWORD from the environment before config.ini."""

    def setUp(self):
        # utilities locates config.ini through the working directory, so give it a
        # scratch project root with its own config.ini.
        self.project_dir = tempfile.mkdtemp(prefix="odqna_config_test_")
        self.addCleanup(shutil.rmtree, self.project_dir, ignore_errors=True)
        os.mkdir(os.path.join(self.project_dir, "agents"))
        with open(os.path.join(self.project_dir, "prompts.yaml"), "w", encoding="utf-8") as prompts:
            prompts.write("{}\n")
        original_dir = os.getcwd()
        self.addCleanup(os.chdir, original_dir)

    def _load_utilities(self, file_password, env_password):
        config = configparser.ConfigParser()
        config.read(os.path.join(REPO_ROOT, "config.ini"))
        config["PGCLOUDSQL"]["pg_password"] = file_password
        with open(os.path.join(self.project_dir, "config.ini"), "w", encoding="utf-8") as config_file:
            config.write(config_file)
        os.chdir(self.project_dir)

        fake_yaml = types.ModuleType("yaml")
        fake_yaml.safe_load = lambda stream: {}
        environment = {key: value for key, value in os.environ.items() if key != "PG_PASSWORD"}
        if env_password is not None:
            environment["PG_PASSWORD"] = env_password

        spec = importlib.util.spec_from_file_location(
            "utilities_credentials_under_test", os.path.join(REPO_ROOT, "utilities", "__init__.py"))
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {"yaml": fake_yaml}), \
                mock.patch.dict(os.environ, environment, clear=True):
            spec.loader.exec_module(module)
        return module.PG_PASSWORD

    def test_environment_variable_is_used(self):
        self.assertEqual(self._load_utilities(file_password="", env_password="from-env"), "from-env")

    def test_environment_variable_wins_over_config_file(self):
        self.assertEqual(self._load_utilities(file_password="from-file", env_password="from-env"), "from-env")

    def test_config_file_still_works_without_the_environment_variable(self):
        self.assertEqual(self._load_utilities(file_password="from-file", env_password=None), "from-file")

    def test_nothing_configured_means_no_password_rather_than_a_default(self):
        self.assertEqual(self._load_utilities(file_password="", env_password=None), "")


class TestNoPasswordLiteralsInCode(unittest.TestCase):
    def test_python_setup_has_no_password_literal(self):
        self.assertIsNone(PASSWORD_LITERAL.search(_read("env_setup.py")))

    def test_notebooks_have_no_password_literal(self):
        for notebook in ["1_Setup_OpenDataQnA.ipynb", "0_CopyDataToCloudSqlPG.ipynb"]:
            with self.subTest(notebook=notebook):
                text = _read("notebooks", notebook)
                json.loads(text)
                self.assertIsNone(PASSWORD_LITERAL.search(text))

    def test_docs_have_no_password_literal(self):
        self.assertIsNone(re.search(r"(?i)pg_password\s*=\s*[\w\"']", _read("docs", "config_guide.md")))

    def test_the_pattern_recognises_a_password_literal(self):
        for line in ["pg_password = 'hunter2'", 'PG_PASSWORD = "hunter2"', '"pg_password = \'hunter2\'\\n",']:
            with self.subTest(line=line):
                self.assertIsNotNone(PASSWORD_LITERAL.search(line))
        for line in ["pg_password = PG_PASSWORD", "pg_password = getpass.getpass('Password: ')",
                     '# pg_password = "<a strong password>"']:
            with self.subTest(line=line):
                self.assertIsNone(PASSWORD_LITERAL.search(line))


class TestTerraformHasNoFixedPasswords(unittest.TestCase):
    def test_pg_password_variable_is_sensitive_and_has_no_usable_default(self):
        variables = _read("terraform", "variables.tf")
        block = re.search(r'variable "pg_password" \{(.*?)\n\}', variables, re.DOTALL)
        self.assertIsNotNone(block)
        self.assertRegex(block.group(1), r'default\s*=\s*""')
        self.assertRegex(block.group(1), r"sensitive\s*=\s*true")

    def test_database_passwords_are_not_string_literals(self):
        pg_vector = _read("terraform", "pg-vector.tf")
        self.assertRegex(pg_vector, r"root_password\s*=\s*random_password\.pg_root\.result")
        self.assertRegex(pg_vector, r"\n\s*password\s*=\s*local\.pg_password")
        self.assertIsNone(re.search(r'(?m)^\s*(root_)?password\s*=\s*"', pg_vector))

    def test_empty_variable_falls_back_to_a_generated_password(self):
        self.assertRegex(
            _read("terraform", "locals.tf"),
            r'pg_password\s*=\s*var\.pg_password != "" \? var\.pg_password : random_password\.pg_user\.result',
        )

    def test_sample_tfvars_sets_no_password(self):
        self.assertIsNone(re.search(r'(?m)^\s*pg_password\s*=', _read("terraform", "terraform.tfvars.sample")))


class TestFlutterAppShipsNoLiveFirebaseProject(unittest.TestCase):
    FLUTTER = ("frontend", "frontend-flutter")

    def test_no_api_keys(self):
        for relative_path in [
            self.FLUTTER + ("lib", "firebase_options.dart"),
            self.FLUTTER + ("android", "app", "google-services.json"),
            self.FLUTTER + ("ios", "Runner", "GoogleService-Info.plist"),
        ]:
            with self.subTest(path="/".join(relative_path)):
                self.assertIsNone(GOOGLE_API_KEY.search(_read(*relative_path)))

    def test_dart_options_are_placeholders(self):
        options = _read(*self.FLUTTER, "lib", "firebase_options.dart")
        self.assertEqual(set(re.findall(r"apiKey: '([^']*)'", options)), {"YOUR_FIREBASE_API_KEY"})
        self.assertEqual(set(re.findall(r"projectId: '([^']*)'", options)), {"YOUR_PROJECT_ID"})

    def test_android_config_is_a_placeholder_and_still_valid_json(self):
        services = json.loads(_read(*self.FLUTTER, "android", "app", "google-services.json"))
        self.assertEqual(services["project_info"]["project_id"], "YOUR_PROJECT_ID")
        self.assertEqual(services["client"][0]["api_key"], [{"current_key": "YOUR_FIREBASE_API_KEY"}])

    def test_ios_config_is_a_placeholder_and_still_a_valid_plist(self):
        with open(os.path.join(REPO_ROOT, *self.FLUTTER, "ios", "Runner", "GoogleService-Info.plist"), "rb") as plist:
            info = plistlib.load(plist)
        self.assertEqual(info["API_KEY"], "YOUR_FIREBASE_API_KEY")
        self.assertEqual(info["PROJECT_ID"], "YOUR_PROJECT_ID")


if __name__ == "__main__":
    unittest.main()
