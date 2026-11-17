# Generates structured JSON Google Charts specifications for web and mobile clients.
# Never emits executable JavaScript.

from abc import ABC
import json
import math
import re
from typing import Any

from google.cloud.aiplatform import telemetry
import vertexai
from vertexai.generative_models import GenerativeModel, HarmBlockThreshold, HarmCategory

from .core import Agent
from utilities import PG_REGION, PROJECT_ID, PROMPTS, format_prompt

vertexai.init(project=PROJECT_ID, location=PG_REGION)

ALLOWED_CHART_TYPES: dict[str, str] = {
    "BarChart": "corechart",
    "ColumnChart": "corechart",
    "LineChart": "corechart",
    "AreaChart": "corechart",
    "PieChart": "corechart",
    "ScatterChart": "corechart",
    "BubbleChart": "corechart",
    "Histogram": "corechart",
    "ComboChart": "corechart",
    "SteppedAreaChart": "corechart",
    "Table": "table",
    "GeoChart": "geochart",
}

_CHART_TYPE_ALIASES: dict[str, str] = {
    "barchart": "BarChart",
    "bar chart": "BarChart",
    "bar": "BarChart",
    "bullet chart": "BarChart",
    "columnchart": "ColumnChart",
    "column chart": "ColumnChart",
    "column": "ColumnChart",
    "linechart": "LineChart",
    "line chart": "LineChart",
    "line": "LineChart",
    "areachart": "AreaChart",
    "area chart": "AreaChart",
    "area": "AreaChart",
    "piechart": "PieChart",
    "pie chart": "PieChart",
    "pie": "PieChart",
    "donut chart": "PieChart",
    "scatterchart": "ScatterChart",
    "scatter chart": "ScatterChart",
    "scatter plot": "ScatterChart",
    "scatter": "ScatterChart",
    "bubblechart": "BubbleChart",
    "bubble chart": "BubbleChart",
    "bubble": "BubbleChart",
    "histogram": "Histogram",
    "combochart": "ComboChart",
    "combo chart": "ComboChart",
    "steppedareachart": "SteppedAreaChart",
    "stepped area chart": "SteppedAreaChart",
    "table": "Table",
    "text": "Table",
    "score card": "Table",
    "scorecard": "Table",
    "text or score card": "Table",
    "geochart": "GeoChart",
    "geo chart": "GeoChart",
    "map chart": "GeoChart",
    "map": "GeoChart",
}

DEFAULT_SAFETY_SETTINGS: dict[Any, Any] = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


def _strip_code_fences(text: str) -> str:
    """Strips surrounding markdown code fences without corrupting inner JSON text."""
    if not isinstance(text, str):
        raise ValueError("Expected string response from language model.")
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def normalize_chart_type(raw_chart_type: Any) -> str:
    """Normalizes and validates a Google Charts constructor name against ALLOWED_CHART_TYPES."""
    if not isinstance(raw_chart_type, str) or not raw_chart_type.strip():
        raise ValueError("chartType must be a non-empty string.")
    candidate = raw_chart_type.strip()
    if candidate in ALLOWED_CHART_TYPES:
        return candidate
    normalized_key = re.sub(r"\s+", " ", candidate.lower())
    if normalized_key in _CHART_TYPE_ALIASES:
        return _CHART_TYPE_ALIASES[normalized_key]
    raise ValueError(f"Unsupported chartType: {candidate!r}")


def _is_safe_cell_value(val: Any) -> bool:
    """Ensures chart data cells are strictly JSON primitive scalars (no nested objects/arrays/NaN)."""
    if val is None or isinstance(val, (str, bool, int)):
        return True
    if isinstance(val, float):
        return math.isfinite(val)
    return False


def _sanitize_options(raw_options: Any) -> dict[str, Any]:
    """Builds a sanitized Google Charts options dictionary with allowHtml forced to False."""
    safe_options: dict[str, Any] = {
        "width": 600,
        "height": 300,
        "allowHtml": False,
    }
    if not isinstance(raw_options, dict):
        return safe_options

    title = raw_options.get("title")
    if isinstance(title, str):
        safe_options["title"] = title[:300]

    for dim_key, default_dim in (("width", 600), ("height", 300)):
        dim_val = raw_options.get(dim_key)
        if isinstance(dim_val, (int, float)) and not isinstance(dim_val, bool):
            bounded = int(dim_val)
            if 100 <= bounded <= 4000:
                safe_options[dim_key] = bounded
            else:
                safe_options[dim_key] = default_dim

    if isinstance(raw_options.get("isStacked"), bool):
        safe_options["isStacked"] = raw_options["isStacked"]

    pie_hole = raw_options.get("pieHole")
    if isinstance(pie_hole, (int, float)) and not isinstance(pie_hole, bool):
        if 0.0 <= float(pie_hole) <= 1.0:
            safe_options["pieHole"] = float(pie_hole)

    for axis_key in ("hAxis", "vAxis", "legend"):
        axis_val = raw_options.get(axis_key)
        if isinstance(axis_val, dict):
            safe_axis: dict[str, Any] = {}
            if axis_key in ("hAxis", "vAxis") and isinstance(axis_val.get("title"), str):
                safe_axis["title"] = axis_val["title"][:200]
            text_style = axis_val.get("textStyle")
            if isinstance(text_style, dict):
                font_size = text_style.get("fontSize")
                if isinstance(font_size, (int, float)) and not isinstance(font_size, bool):
                    if 4 <= int(font_size) <= 48:
                        safe_axis["textStyle"] = {"fontSize": int(font_size)}
            if safe_axis:
                safe_options[axis_key] = safe_axis

    bar_val = raw_options.get("bar")
    if isinstance(bar_val, dict):
        group_width = bar_val.get("groupWidth")
        if isinstance(group_width, str) and re.fullmatch(r"\d{1,3}%", group_width.strip()):
            safe_options["bar"] = {"groupWidth": group_width.strip()}

    # Never allow HTML rendering in Google Visualization Table or tooltips.
    safe_options["allowHtml"] = False
    return safe_options


def validate_chart_spec(raw_spec: Any) -> dict[str, Any]:
    """Parses and validates a structured JSON chart specification.

    Rejects raw JavaScript strings, unknown chart constructors, non-primitive cell
    values, mismatched row lengths, and unsafe options such as allowHtml=True.
    """
    if isinstance(raw_spec, str):
        cleaned = _strip_code_fences(raw_spec)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("Chart specification must be valid JSON, not executable code.") from exc
    elif isinstance(raw_spec, dict):
        parsed = raw_spec
    else:
        raise ValueError("Chart specification must be a JSON object.")

    if not isinstance(parsed, dict):
        raise ValueError("Chart specification root must be a JSON object.")

    chart_type = normalize_chart_type(parsed.get("chartType"))

    raw_columns = parsed.get("columns")
    if not isinstance(raw_columns, list) or len(raw_columns) == 0:
        raise ValueError("Chart specification 'columns' must be a non-empty list.")

    columns: list[str] = []
    for col in raw_columns:
        if isinstance(col, str) and col.strip():
            columns.append(col.strip()[:200])
        elif isinstance(col, dict) and isinstance(col.get("label"), str) and col["label"].strip():
            columns.append(col["label"].strip()[:200])
        else:
            raise ValueError("Each column in 'columns' must be a non-empty string.")

    raw_rows = parsed.get("rows")
    if not isinstance(raw_rows, list):
        raise ValueError("Chart specification 'rows' must be a list of row arrays.")

    rows: list[list[Any]] = []
    expected_len = len(columns)
    for row in raw_rows:
        if not isinstance(row, list) or len(row) != expected_len:
            raise ValueError(
                f"Each row in 'rows' must be a list matching column count ({expected_len})."
            )
        sanitized_row: list[Any] = []
        for cell in row:
            if not _is_safe_cell_value(cell):
                raise ValueError("Chart data cells must be primitive JSON scalars.")
            sanitized_row.append(cell)
        rows.append(sanitized_row)

    options = _sanitize_options(parsed.get("options"))

    return {
        "chartType": chart_type,
        "columns": columns,
        "rows": rows,
        "options": options,
    }


class VisualizeAgent(Agent, ABC):
    """An agent that generates structured JSON Google Charts specifications."""

    agentType: str = "VisualizeAgent"

    def __init__(self):
        self.model_id = "gemini-1.5-pro"
        self.model = GenerativeModel("gemini-1.5-pro-001")
        self.safety_settings = dict(DEFAULT_SAFETY_SETTINGS)

    def getChartType(self, user_question, generated_sql):
        chart_type_prompt = PROMPTS["visualize_chart_type"]
        chart_type_prompt = format_prompt(
            chart_type_prompt,
            user_question=user_question,
            generated_sql=generated_sql,
        )
        response = self.model.generate_content(
            chart_type_prompt,
            safety_settings=self.safety_settings,
            stream=False,
        )
        return _strip_code_fences(response.candidates[0].text)

    def getChartPrompt(self, user_question, generated_sql, chart_type, chart_div, sql_results):
        chart_prompt = PROMPTS["visualize_generate_chart_code"]
        return format_prompt(
            chart_prompt,
            user_question=user_question,
            generated_sql=generated_sql,
            chart_type=chart_type,
            chart_div=chart_div,
            sql_results=sql_results,
        )

    def generate_charts(self, user_question, generated_sql, sql_results):
        chart_type_raw = self.getChartType(user_question, generated_sql)
        chart_json = json.loads(chart_type_raw)
        chart_list = [
            normalize_chart_type(chart_json["chart_1"]),
            normalize_chart_type(chart_json["chart_2"]),
        ]
        print("Charts Suggested : " + str(chart_list))
        context_prompt = self.getChartPrompt(
            user_question, generated_sql, chart_list[0], "chart_div", sql_results
        )
        context_prompt_1 = self.getChartPrompt(
            user_question, generated_sql, chart_list[1], "chart_div_1", sql_results
        )

        with telemetry.tool_context_manager("opendataqna-visualize-v2"):
            context_query = self.model.generate_content(
                context_prompt, safety_settings=self.safety_settings, stream=False
            )
            context_query_1 = self.model.generate_content(
                context_prompt_1, safety_settings=self.safety_settings, stream=False
            )

        return {
            "chart_div": validate_chart_spec(context_query.candidates[0].text),
            "chart_div_1": validate_chart_spec(context_query_1.candidates[0].text),
        }
