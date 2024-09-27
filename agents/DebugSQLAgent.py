from abc import ABC

import vertexai
from vertexai.language_models import CodeChatModel
from vertexai.generative_models import GenerativeModel,GenerationConfig
from google.cloud.aiplatform import telemetry
from dbconnectors import bqconnector # pgconnector removed
from utilities import PROMPTS, format_prompt
from .core import Agent
import pandas as pd
import json  

from utilities import PROJECT_ID, BQ_REGION
vertexai.init(project=PROJECT_ID, location=BQ_REGION)


class DebugSQLAgent(Agent, ABC):
    """
    An agent designed to debug and refine SQL queries for BigQuery or PostgreSQL databases.

    This agent interacts with a chat-based language model (CodeChat or Gemini) to iteratively troubleshoot SQL queries. It receives feedback in the form of error messages and uses the model's capabilities to generate alternative queries that address the identified issues. The agent strives to maintain the original intent of the query while ensuring its syntactic and semantic correctness.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "DebugSQLAgent".
        model_id (str): The ID of the chat model to use for debugging. Valid options are:
            - "codechat-bison-32k"
            - "gemini-1.0-pro" 
            - "gemini-ultra"

    Methods:
        init_chat(source_type, tables_schema, columns_schema, sql_example) -> ChatSession:
            Initializes a chat session with the chosen chat model.

            Args:
                source_type (str): The database type ("bigquery" or "postgresql").
                tables_schema (str): A description of the available tables and their columns.
                columns_schema (str): Detailed descriptions of the columns in the tables.
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

        start_debugger(source_type, query, user_question, SQLChecker, tables_schema, columns_schema, AUDIT_TEXT, similar_sql, DEBUGGING_ROUNDS, LLM_VALIDATION) -> Tuple[str, bool, str]:

            Args:
                source_type (str): The database type ("bigquery" or "postgresql").
                query (str): The initial SQL query to debug.
                user_question (str): The user's original question for reference.
                SQLChecker: An object to validate the SQL syntax.
                tables_schema (str): Table schema information.
                columns_schema (str): Detailed column descriptions.
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

    def __init__(self, model_id = 'gemini-1.5-pro'):
        super().__init__(model_id=model_id) 


    def init_chat(self,source_type,user_grouping, tables_schema,columns_schema,similar_sql="-No examples provided..-"):

        if f'usecase_{source_type}_{user_grouping}' in PROMPTS:
            usecase_context = PROMPTS[f'usecase_{source_type}_{user_grouping}']
        else:
            usecase_context = "No extra context for the usecase is provided"
            
        context_prompt = PROMPTS[f'debugsql_{source_type}']

        context_prompt = format_prompt(context_prompt,
                                       usecase_context = usecase_context,
                                       similar_sql=similar_sql, 
                                       tables_schema=tables_schema, 
                                       columns_schema = columns_schema)

        # print(f"Prompt to Debug SQL after formatting: \n{context_prompt}")
        
        if self.model_id == 'codechat-bison-32k':
            with telemetry.tool_context_manager('opendataqna-debugsql-v2'):

                chat_session = self.model.start_chat(context=context_prompt)
        elif 'gemini' in self.model_id:
            with telemetry.tool_context_manager('opendataqna-debugsql-v2'):

                chat_session = self.model.start_chat(response_validation=False)
                chat_session.send_message(context_prompt)
        else:
            raise ValueError('Invalid Chat Model Specified')
        
        return chat_session


    def rewrite_sql_chat(self, chat_session, sql, question, error_df):


        context_prompt = f"""
            What is an alternative SQL statement to address the error mentioned below?
            Present a different SQL from previous ones. It is important that the query still answer the original question.
            All columns selected must be present on tables mentioned on the join section.
            Avoid repeating suggestions.

            <Original SQL>
            {sql}
            </Original SQL>

            <Original Question>
            {question}
            </Original Question>

            <Error Message>
            {error_df}
            </Error Message>

            """

        if self.model_id =='codechat-bison-32k':
            with telemetry.tool_context_manager('opendataqna-debugsql-v2'):
                response = chat_session.send_message(context_prompt)
                resp_return = (str(response.candidates[0])).replace("```sql", "").replace("```", "")
        elif 'gemini' in self.model_id:
            with telemetry.tool_context_manager('opendataqna-debugsql-v2'):
                response = chat_session.send_message(context_prompt, stream=False)
                resp_return = (str(response.text)).replace("```sql", "").replace("```", "")
        else:
            raise ValueError('Invalid Model Id')

        return resp_return


    def start_debugger  (self,
                        source_type,
                        user_grouping,
                        query,
                        user_question, 
                        SQLChecker,
                        tables_schema, 
                        columns_schema,
                        AUDIT_TEXT, 
                        similar_sql="-No examples provided..-", 
                        DEBUGGING_ROUNDS = 2,
                        LLM_VALIDATION=False):
        i = 0  
        STOP = False 
        invalid_response = False 
        chat_session = self.init_chat(source_type,user_grouping,tables_schema,columns_schema,similar_sql)
        sql = query.replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ","")

        AUDIT_TEXT=AUDIT_TEXT+"\n\nEntering the debugging steps!"
        while (not STOP):

            json_syntax_result={ "valid":True, "errors":"None"}
            # Check if LLM Validation is enabled 
            if LLM_VALIDATION: 
                # sql = query.replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ","")
                json_syntax_result = SQLChecker.check(source_type,user_question,tables_schema,columns_schema, sql) 

            else: 
                json_syntax_result['valid'] = True
                AUDIT_TEXT=AUDIT_TEXT+"\nLLM Validation is deactivated. Jumping directly to dry run execution."
 

            if json_syntax_result['valid'] is True:
                AUDIT_TEXT=AUDIT_TEXT+"\nGenerated SQL is syntactically correct as per LLM Validation!"
                   
                # print(AUDIT_TEXT)
                if source_type=='bigquery':
                    connector=bqconnector
                else:
                    connector=pgconnector
                    
                correct_sql, exec_result_df = connector.test_sql_plan_execution(sql)
                
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
                rewrite_result=self.rewrite_sql_chat(chat_session, sql, user_question, syntax_err_df)
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
        return sql, invalid_response, AUDIT_TEXT