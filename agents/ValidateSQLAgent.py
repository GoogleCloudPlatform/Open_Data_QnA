import json 
from abc import ABC
from .core import Agent
from utilities import PROMPTS, format_prompt 



class ValidateSQLAgent(Agent, ABC):
    """
    An agent that validates the syntax and semantic correctness of SQL queries.

    This agent leverages a language model (currently Gemini) to analyze a given SQL query against a provided database schema. It assesses whether the query is valid according to a set of predefined guidelines and generates a JSON response indicating the validity status and any potential errors.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "ValidateSQLAgent".

    Methods:
        check(user_question, tables_schema, columns_schema, generated_sql) -> dict:
            Determines the validity of an SQL query and identifies potential errors.

            Args:
                user_question (str): The original question posed by the user (used for context).
                tables_schema (str): A description of the database tables and their relationships.
                columns_schema (str): Detailed descriptions of the columns within the tables.
                generated_sql (str): The SQL query to be validated.

            Returns:
                dict: A JSON-formatted dictionary with the following keys:
                    - "valid": A boolean value indicating whether the query is valid or not.
                    - "errors": A string describing any errors found in the query (empty if valid).
    """


    agentType: str = "ValidateSQLAgent"

    def check(self,source_type, user_question, tables_schema, columns_schema, generated_sql):
        
        context_prompt = PROMPTS['validatesql']
        context_prompt = format_prompt(context_prompt,
                                       source_type = source_type,
                                       user_question = user_question,
                                       tables_schema = tables_schema, 
                                       columns_schema = columns_schema,
                                       generated_sql=generated_sql)

        # print(f"Prompt to Validate SQL after formatting: \n{context_prompt}")
        
        if "gemini" in self.model_id:
            context_query = self.model.generate_content(context_prompt, stream=False)
            generated_sql = str(context_query.candidates[0].text)

        else:
            context_query = self.model.predict(context_prompt, max_output_tokens = 8000, temperature=0)
            generated_sql = str(context_query.candidates[0])


        json_syntax_result = json.loads(str(generated_sql).replace("```json","").replace("```",""))

        # print('\n SQL Syntax Validity:' + str(json_syntax_result['valid']))
        # print('\n SQL Syntax Error Description:' +str(json_syntax_result['errors']) + '\n')
        
        return json_syntax_result