# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



from abc import ABC
from .core import Agent 
import vertexai
from google.cloud.aiplatform import telemetry
from vertexai.generative_models import GenerationConfig
from utilities import PROJECT_ID, PG_REGION
vertexai.init(project=PROJECT_ID, location=PG_REGION)


class BuildSQLAgent(Agent, ABC):
    """
    An agent specialized in generating SQL queries for BigQuery or PostgreSQL databases.

    This agent analyzes user questions, available table schemas, and column descriptions to construct syntactically and semantically correct SQL queries. It adapts the query generation process based on the target database type (BigQuery or PostgreSQL).

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "BuildSQLAgent".

    Methods:
        build_sql(source_type, user_question, tables_schema, tables_detailed_schema, similar_sql, max_output_tokens=2048, temperature=0.4, top_p=1, top_k=32) -> str:
            Generates an SQL query based on the provided parameters.

            Args:
                source_type (str): The database type ("bigquery" or "postgresql").
                user_question (str): The question asked by the user.
                tables_schema (str): A description of the available tables and their columns.
                tables_detailed_schema (str): Detailed descriptions of the columns in the tables.
                similar_sql (str): Examples of similar SQL queries to guide the generation process.
                max_output_tokens (int, optional): Maximum number of tokens in the generated SQL. Defaults to 2048.
                temperature (float, optional): Controls the randomness of the generated output. Defaults to 0.4.
                top_p (float, optional): Nucleus sampling threshold for controlling diversity. Defaults to 1.
                top_k (int, optional): Consider the top k most probable tokens for sampling. Defaults to 32.

            Returns:
                str: The generated SQL query as a single-line string.
    """


    agentType: str = "BuildSQLAgent"

    def build_sql(self,source_type, user_question,tables_schema,tables_detailed_schema, similar_sql, max_output_tokens=2048, temperature=0.4, top_p=1, top_k=32): 
        not_related_msg=''
        if source_type=='bigquery':
            not_related_msg="select `Question is not related to the dataset` as unrelated_answer"
            context_prompt = f"""
            You are a BigQuery SQL guru. Write a SQL comformant query for Bigquery that answers the following question while using the provided context to correctly refer to the BigQuery tables and the needed column names.

            Guidelines:
            - Join as minimal tables as possible.
            - When joining tables ensure all join columns are the same data_type.
            - Analyze the database and the table schema provided as parameters and undestand the relations (column and table relations).
            - Use always SAFE_CAST. If performing a SAFE_CAST, use only Bigquery supported datatypes.
            - Always SAFE_CAST and then use aggregate functions
            - Don't include any comments in code.
            - Remove ```sql and ``` from the output and generate the SQL in single line.
            - Tables should be refered to using a fully qualified name with enclosed in ticks (`) e.g. `project_id.owner.table_name`.
            - Use all the non-aggregated columns from the "SELECT" statement while framing "GROUP BY" block.
            - Return syntactically and symantically correct SQL for BigQuery with proper relation mapping i.e project_id, owner, table and column relation.
            - Use ONLY the column names (column_name) mentioned in Table Schema. DO NOT USE any other column names outside of this.
            - Associate column_name mentioned in Table Schema only to the table_name specified under Table Schema.
            - Use SQL 'AS' statement to assign a new name temporarily to a table column or even a table wherever needed.
            - Table names are case sensitive. DO NOT uppercase or lowercase the table names.
            - Always enclose subqueries and union queries in brackets.
            - Refer to the examples provided below, if given.
            - Only answer questions relevant to the tables or columns listed in the table schema If a non-related question comes, answer exactly with : {not_related_msg}


            Here are some examples of user-question and SQL queries:
            {similar_sql}

            question:
            {user_question}

            Table Schema:
            {tables_schema}

            Column Description:
            {tables_detailed_schema}

            """
            # print(context_prompt)


        else: 

            not_related_msg='select \'Question is not related to the dataset\' as unrelated_answer from dual;'
        
            from dbconnectors import pg_specific_data_types
            pg_specific_data_types = pg_specific_data_types() 

            
            context_prompt = f"""

            You are an PostgreSQL SQL guru. Write a SQL comformant query for PostgreSQL that answers the following question while using the provided context to correctly refer to postgres tables and the needed column names.

            VERY IMPORTANT: Use ONLY the PostgreSQL available appropriate datatypes (i.e {pg_specific_data_types}) while casting the column in the SQL.
            IMPORTANT: In "FROM" and "JOIN" blocks always refer the table_name as schema.table_name.
            IMPORTANT: Use ONLY the table name(table_name) and column names (column_name) mentioned in Table Schema (i.e {tables_schema}). DO NOT USE any other column names outside of this.
            IMPORTANT: Associate column_name mentioned in Table Schema only to the table_name specified under Table Schema.
            NOTE: Use SQL 'AS' statement to assign a new name temporarily to a table column or even a table wherever needed.

            Guidelines:.
            - Only answer questions relevant to the tables or columns listed in the table schema If a non-related question comes, answer exactly: {not_related_msg}
            - Join as minimal tables as possible.
            - When joining tables ensure all join columns are the same data_type.
            - Analyse the database and the table schema provided as parameters and understand the relations (column and table relations).
            - Don't include any comments in code.
            - Remove ```sql and ``` from the output and generate the SQL in single line.
            - Tables should be refered to using a fully qualified name including owner and table name.
            - Use table_alias.column_name when referring to columns. Example: dept_id=hr.dept_id
            - Capitalize the table names on SQL "where" condition.
            - Use the columns from the "SELECT" statement while framing "GROUP BY" block.
            - Always refer the column-name with rightly mapped table-name as seen in the table schema.
            - Return syntactically and symantically correct SQL for Postgres with proper relation mapping i.e owner, table and column relation.
            - Refer to the examples provided i.e. {similar_sql}


            Here are some examples of user-question and SQL queries:
            {similar_sql}

            question:
            {user_question}

            Table Schema:
            {tables_schema}

            Column Description:
            {tables_detailed_schema}

            """
            # print(context_prompt)

        if 'gemini' in self.model_id:
            # Generation Config
            config = GenerationConfig(
                max_output_tokens=max_output_tokens, temperature=temperature, top_p=top_p, top_k=top_k
            )

            # Generate text
            with telemetry.tool_context_manager('opendataqna-buildsql'):
                context_query = self.model.generate_content(context_prompt, generation_config=config, stream=False)
                generated_sql = str(context_query.candidates[0].text)

        else:
            with telemetry.tool_context_manager('opendataqna-buildsql'):

                context_query = self.model.predict(context_prompt, max_output_tokens = max_output_tokens, temperature=temperature)
                generated_sql = str(context_query.candidates[0])

        print(generated_sql)

        return generated_sql
