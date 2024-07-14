#This agent generates google charts code for displaying charts on web application

#Generates two charts with elements "chart-div" and "chart-div-1"

#Code is in javascript

from abc import ABC
from vertexai.language_models import CodeChatModel
from vertexai.generative_models import GenerativeModel,HarmCategory,HarmBlockThreshold
from .core import Agent
from utilities import PROMPTS, format_prompt 
from agents import ValidateSQLAgent 
import pandas as pd
import json  


class VisualizeAgent(Agent, ABC):
    """
    An agent that generates JavaScript code for Google Charts based on user questions and SQL results.

    This agent analyzes the user's question and the corresponding SQL query results to determine suitable chart types. It then constructs JavaScript code that uses Google Charts to create visualizations based on the data.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "VisualizeAgent".
        model_id (str): The ID of the language model used for chart type suggestion and code generation.
        model: The language model instance.

    Methods:
        getChartType(user_question, generated_sql) -> str:
            Suggests the two most suitable chart types based on the user's question and the generated SQL query.

            Args:
                user_question (str): The natural language question asked by the user.
                generated_sql (str): The SQL query generated to answer the question.

            Returns:
                str: A JSON string containing two keys, "chart_1" and "chart_2", each representing a suggested chart type.

        getChartPrompt(user_question, generated_sql, chart_type, chart_div, sql_results) -> str:
            Creates a prompt for the language model to generate the JavaScript code for a specific chart.

            Args:
                user_question (str): The user's question.
                generated_sql (str): The generated SQL query.
                chart_type (str): The desired chart type (e.g., "Bar Chart", "Pie Chart").
                chart_div (str): The HTML element ID where the chart will be rendered.
                sql_results (str): The results of the SQL query in JSON format.

            Returns:
                str: The prompt for the language model to generate the chart code.

        generate_charts(user_question, generated_sql, sql_results) -> dict:
            Generates JavaScript code for two Google Charts based on the given inputs.

            Args:
                user_question (str): The user's question.
                generated_sql (str): The generated SQL query.
                sql_results (str): The results of the SQL query in JSON format.

            Returns:
                dict: A dictionary containing two keys, "chart_div" and "chart_div_1", each holding the generated JavaScript code for a chart.
    """


    agentType: str ="VisualizeAgent"

    def __init__(self):
        self.model_id = 'gemini-1.5-pro'
        self.model = GenerativeModel("gemini-1.5-pro-001")

    def getChartType(self,user_question, generated_sql):

        chart_type_prompt = PROMPTS['visualize_chart_type']

        chart_type_prompt = format_prompt(chart_type_prompt,
                                          user_question = user_question,
                                          generated_sql = generated_sql)

        chart_type=self.model.generate_content(chart_type_prompt, stream=False).candidates[0].text
        # print(chart_type)
        # chart_type = model.predict(map_prompt, max_output_tokens = 1024, temperature= 0.2).candidates[0].text
        return chart_type.replace("\n", "").replace("```", "").replace("json", "").replace("```html", "").replace("```", "").replace("js\n","").replace("json\n","").replace("python\n","").replace("javascript","")

    def getChartPrompt(self,user_question, generated_sql, chart_type, chart_div, sql_results):
        chart_prompt = PROMPTS['visualize_generate_chart_code']

        chart_prompt = format_prompt(chart_prompt,
                                     user_question = user_question,
                                     generated_sql = generated_sql,
                                     chart_type = chart_type,
                                     chart_div = chart_div,
                                     sql_results = sql_results)
        # print(f"Prompt to generate code for google charts visualization after formatting: \n{chart_prompt}")
        return chart_prompt

    def generate_charts(self,user_question,generated_sql,sql_results):
        chart_type = self.getChartType(user_question,generated_sql)
        # chart_type = chart_type.split(",")
        # chart_list = [x.strip() for x in chart_type]
        chart_json = json.loads(chart_type)
        chart_list =[chart_json['chart_1'],chart_json['chart_2']]
        print("Charts Suggested : " + str(chart_list))
        context_prompt=self.getChartPrompt(user_question,generated_sql,chart_list[0],"chart_div",sql_results)
        context_prompt_1=self.getChartPrompt(user_question,generated_sql,chart_list[1],"chart_div_1",sql_results)
        safety_settings: Optional[dict] = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        context_query = self.model.generate_content(context_prompt,safety_settings=safety_settings, stream=False)
        context_query_1 = self.model.generate_content(context_prompt_1,safety_settings=safety_settings, stream=False)
        google_chart_js={"chart_div":context_query.candidates[0].text.replace("```json", "").replace("```", "").replace("json", "").replace("```html", "").replace("```", "").replace("js","").replace("json","").replace("python","").replace("javascript",""),
                        "chart_div_1":context_query_1.candidates[0].text.replace("```json", "").replace("```", "").replace("json", "").replace("```html", "").replace("```", "").replace("js","").replace("json","").replace("python","").replace("javascript","")}

        return google_chart_js