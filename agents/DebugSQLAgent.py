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

from vertexai.language_models import CodeChatModel
from vertexai.generative_models import GenerativeModel

from .core import Agent
import pandas as pd
import json  
from dbconnectors import pgconnector, bqconnector



class DebugSQLAgent(Agent, ABC):
    """
    An agent designed to debug and refine SQL queries for BigQuery or PostgreSQL databases.

    This agent interacts with a chat-based language model (CodeChat or Gemini) to iteratively troubleshoot SQL queries. It receives feedback in the form of error messages and uses the model's capabilities to generate alternative queries that address the identified issues. The agent strives to maintain the original intent of the query while ensuring its syntactic and semantic correctness.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "DebugSQLAgent".
        chat_model_id (str): The ID of the chat model to use for debugging. Valid options are:
            - "codechat-bison-32k"
            - "gemini-1.0-pro" 
            - "gemini-ultra"

    Methods:
        init_chat(source_type, tables_schema, tables_detailed_schema, sql_example) -> ChatSession:
            Initializes a chat session with the chosen chat model.

            Args:
                source_type (str): The database type ("bigquery" or "postgresql").
                tables_schema (str): A description of the available tables and their columns.
                tables_detailed_schema (str): Detailed descriptions of the columns in the tables.
                sql_example (str, optional): An example SQL query for reference. Defaults to "-No examples provided..-".

            Returns:
                ChatSession: The initiated chat session object.

        rewrite_sql_chat(chat_session, question, error_df) -> str:
            Generates an alternative SQL query based on the chat session, original query, and error message.

            Args:
                chat_session (ChatSession): The active chat session.
                question (str): The original SQL query.
                error_df (pandas.DataFrame): The error message as a DataFrame.

            Returns:
                str: The rewritten SQL query.

        start_debugger(source_type, query, user_question, SQLChecker, tables_schema, tables_detailed_schema, AUDIT_TEXT, similar_sql, DEBUGGING_ROUNDS, LLM_VALIDATION) -> Tuple[str, bool, str]:
            Initiates the debugging process and iteratively refines the SQL query.

            Args:
                source_type (str): The database type ("bigquery" or "postgresql").
                query (str): The initial SQL query to debug.
                user_question (str): The user's original question for reference.
                SQLChecker: An object to validate the SQL syntax.
                tables_schema (str): Table schema information.
                tables_detailed_schema (str): Detailed column descriptions.
                AUDIT_TEXT (str): Textual audit trail of the debugging process.
                similar_sql (str, optional): Example SQL queries. Defaults to "-No examples provided..-".
                DEBUGGING_ROUNDS (int, optional): Maximum debugging attempts. Defaults to 2.
                LLM_VALIDATION (bool, optional): Whether to use LLM for syntax validation. Defaults to True.

            Returns:
                Tuple[str, bool, str]:
                    - The final refined SQL query (or the original if unchanged).
                    - A boolean indicating if the final query is considered invalid.
                    - The updated AUDIT_TEXT with debugging steps.
    """


    agentType: str = "DebugSQLAgent"

    def __init__(self, chat_model_id = 'gemini-1.0-pro'): 
        self.chat_model_id = chat_model_id
        # self.model = CodeChatModel.from_pretrained("codechat-bison-32k")


    def init_chat(self,source_type, tables_schema,tables_detailed_schema,sql_example="-No examples provided..-"):
        if source_type in ('bigquery'):
            context_prompt = f"""
            You are an BigQuery SQL guru. This session is trying to troubleshoot an BigQuery SQL query.  As the user provides versions of the query and the errors returned by BigQuery,
            return a new alternative SQL query that fixes the errors. It is important that the query still answer the original question.


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
            - Refer to the examples provided i.e. {sql_example}

        Parameters:
        - table metadata: {tables_schema}
        - column metadata: {tables_detailed_schema}
        - SQL example: {sql_example}

        """

        else:
            context_prompt = f"""

            You are an Postgres SQL guru. This session is trying to troubleshoot an Postgres SQL query.  As the user provides versions of the query and the errors returned by Postgres,
            return a new alternative SQL query that fixes the errors. It is important that the query still answer the original question.

            Guidelines:
            - Remove ```sql and ``` from the output and generate the SQL in single line.
            - Rewritten SQL can't be igual to the original one.
            - Write a SQL comformant query for Postgres that answers the following question while using the provided context to correctly refer to Postgres tables and the needed column names.
            - All column_name in the query must exist in the table_name.
            - If a join includes d.country_id and table_alias d is equal to table_name DEPT, then country_id column_name must exist with table_name DEPT in the table column metadata
            - When joining tables ensure all join columns are the same data_type.
            - Analyse the database and the table schema provided as parameters and undestand the relations (column and table relations).
            - Don't include any comments in code.
            - Tables should be refered to using a fully qualified name including owner and table name.
            - Use table_alias.column_name when referring to columns. Example: dept_id=hr.dept_id
            - Capitalize the table names on SQL "where" condition.
            - Use the columns from the "SELECT" statement while framing "GROUP BY" block.
            - Always refer the column-name with rightly mapped table-name as seen in the table schema.
            - Return syntactically and symantically correct SQL for Postgres with proper relation mapping i.e owner, table and column relation.
            - Use only column names listed in the column metadata.
            - Always ensure to refer the table as schema.table_name.
            - Refer to the examples provided i.e. {sql_example}

        Parameters:
        - table metadata: {tables_schema}
        - column metadata: {tables_detailed_schema}
        - SQL example: {sql_example}

        """
        
        if self.chat_model_id == 'codechat-bison-32k':
            chat_model = CodeChatModel.from_pretrained("codechat-bison-32k")
            chat_session = chat_model.start_chat(context=context_prompt)
        elif self.chat_model_id == 'gemini-1.0-pro':
            chat_model = GenerativeModel("gemini-1.0-pro-001")
            chat_session = chat_model.start_chat(response_validation=False)
            chat_session.send_message(context_prompt)
        elif self.chat_model_id == 'gemini-ultra':
            chat_model = GenerativeModel("gemini-1.0-ultra-001")
            chat_session = chat_model.start_chat(response_validation=False)
            chat_session.send_message(context_prompt)
        else:
            raise ValueError('Invalid chat_model_id')
        
        return chat_session


    def rewrite_sql_chat(self, chat_session, sql, question, error_df):


        context_prompt = f"""
            What is an alternative SQL statement to address the error mentioned below?
            Present a different SQL from previous ones. It is important that the query still answer the original question.
            All columns selected must be present on tables mentioned on the join section.
            Avoid repeating suggestions.

            Original SQL:
            {sql}

            Original Question: 
            {question}

            Error:
            {error_df}

            """

        if self.chat_model_id =='codechat-bison-32k':
            response = chat_session.send_message(context_prompt)
            resp_return = (str(response.candidates[0])).replace("```sql", "").replace("```", "")
        elif self.chat_model_id =='gemini-1.0-pro':
            response = chat_session.send_message(context_prompt, stream=False)
            resp_return = (str(response.text)).replace("```sql", "").replace("```", "")
        elif self.chat_model_id == 'gemini-ultra':
            response = chat_session.send_message(context_prompt, stream=False)
            resp_return = (str(response.text)).replace("```sql", "").replace("```", "")
        else:
            raise ValueError('Invalid chat_model_id')

        return resp_return


    def start_debugger  (self,
                        source_type,
                        query,
                        user_question, 
                        SQLChecker,
                        tables_schema, 
                        tables_detailed_schema,
                        AUDIT_TEXT, 
                        similar_sql="-No examples provided..-", 
                        DEBUGGING_ROUNDS = 2,
                        LLM_VALIDATION=True):
        i = 0  
        STOP = False 
        invalid_response = False 
        chat_session = self.init_chat(source_type,tables_schema,tables_detailed_schema,similar_sql)
        sql = query.replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ","")

        AUDIT_TEXT=AUDIT_TEXT+"\n\nEntering the debugging steps!"
        while (not STOP):

            # Check if LLM Validation is enabled 
            if LLM_VALIDATION: 
                # sql = query.replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ","")
                json_syntax_result = SQLChecker.check(user_question,tables_schema,tables_detailed_schema, sql) 

            else: 
                json_syntax_result['valid'] = True 

            if json_syntax_result['valid'] is True:
                # Testing SQL Execution
                if LLM_VALIDATION: 
                    AUDIT_TEXT=AUDIT_TEXT+"\nGenerated SQL is syntactically correct as per LLM Validation!"
                
                else: 
                    AUDIT_TEXT=AUDIT_TEXT+"\nLLM Validation is deactivated. Jumping directly to dry run execution."

                # print(AUDIT_TEXT)
                if source_type=='bigquery':
                    connector=bqconnector
                else:
                    connector=pgconnector
                    
                correct_sql, exec_result_df = connector.test_sql_plan_execution(sql)
                print("exec_result_df:" + exec_result_df)
                if not correct_sql:
                        AUDIT_TEXT=AUDIT_TEXT+"\nGenerated SQL failed on execution! Here is the feedback from bigquery dryrun/ explain plan:  \n" + str(exec_result_df)
                        rewrite_result = self.rewrite_sql_chat(chat_session, sql, user_question, exec_result_df)
                        print('\n Rewritten and Cleaned SQL: ' + str(rewrite_result))
                        AUDIT_TEXT=AUDIT_TEXT+"\nRewritten and Cleaned SQL: \n' + str({rewrite_result})"
                        sql = str(rewrite_result).replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ","")

                else: STOP = True
            else:
                print(f'\nGenerated qeury failed on syntax check as per LLM Validation!\nError Message from LLM:  {json_syntax_result} \nRewriting the query...')
                AUDIT_TEXT=AUDIT_TEXT+'\nGenerated qeury failed on syntax check as per LLM Validation! \nError Message from LLM:  '+ str(json_syntax_result) + '\nRewriting the query...'
                
                syntax_err_df = pd.read_json(json.dumps(json_syntax_result))
                rewrite_result=self.rewrite_sql_chat(chat_session, sql, user_question, exec_result_df)
                print(rewrite_result)
                AUDIT_TEXT=AUDIT_TEXT+'\n Rewritten SQL: ' + str(rewrite_result)
                sql=str(rewrite_result).replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ","")
            i+=1
            if i > DEBUGGING_ROUNDS:
                AUDIT_TEXT=AUDIT_TEXT+ "Exceeded the number of iterations for correction!"
                AUDIT_TEXT=AUDIT_TEXT+ "The generated SQL can be invalid!"
                STOP = True
                invalid_response=True
            # After the while is completed
        if i > DEBUGGING_ROUNDS:
            invalid_response=True
        # print(AUDIT_TEXT)
        return sql, invalid_response, AUDIT_TEXT