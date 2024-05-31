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


import asyncio
import argparse

from agents import EmbedderAgent, BuildSQLAgent, DebugSQLAgent, ValidateSQLAgent, ResponseAgent,VisualizeAgent
from utilities import (PROJECT_ID, PG_REGION, BQ_REGION, EXAMPLES, LOGGING, VECTOR_STORE,
                       BQ_OPENDATAQNA_DATASET_NAME)
from dbconnectors import bqconnector, pgconnector
from embeddings.store_embeddings import add_sql_embedding

Visualize=VisualizeAgent()


#Based on VECTOR STORE in config.ini initialize vector connector and region
if VECTOR_STORE=='bigquery-vector':
    region=BQ_REGION
    vector_connector = bqconnector
    call_await = False

elif VECTOR_STORE == 'cloudsql-pgvector':
    region=PG_REGION
    vector_connector = pgconnector
    call_await=True

else: 
    raise ValueError("Please specify a valid Data Store. Supported are either 'bigquery-vector' or 'cloudsql-pgvector'")



############################
#_____GET ALL DATABASES_____#
############################
def get_all_databases():
    """Retrieves a list of all distinct databases (with source type) from the vector store.

    This function queries the vector store (BigQuery or PostgreSQL) to fetch a list of 
    unique databases, including their source type. The source type indicates whether 
    the database is a BigQuery dataset or a PostgreSQL schema.

    Returns:
        tuple: A tuple containing two elements:
            - result (str or list): A JSON-formatted string containing the list of databases and their source types,
                                 or an error message if an exception occurs.
            - invalid_response (bool): A flag indicating whether an error occurred during retrieval (True)
                                      or if the response is valid (False).

    Raises:
        Exception: If there is an issue connecting to or querying the vector store.
                   The exception message will be included in the returned `result`.
    """
    
    try:
        if VECTOR_STORE=='bigquery-vector': 
            final_sql=f'''SELECT
    DISTINCT CONCAT(table_schema,'-',source_type) AS table_schema
    FROM
        `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.table_details_embeddings`'''

        else:
            final_sql="""SELECT
    DISTINCT CONCAT(table_schema,'-',source_type) AS table_schema
    FROM
    table_details_embeddings"""
        result = vector_connector.retrieve_df(final_sql)
        result = result.to_json(orient='records')
        invalid_response=False

    except Exception as e:
        result="Issue was encountered while extracting databases in vector store:: "  + str(e)
        invalid_response=True
    return result,invalid_response


############################
#_____GET SOURCE TYPE_____##
############################
def get_source_type(user_database):
    """Retrieves the source type of a specified database from the vector store.

    This function queries the vector store (BigQuery or PostgreSQL) to determine whether the
    given database is a BigQuery dataset ('bigquery') or a PostgreSQL schema ('postgres').

    Args:
        user_database (str): The name of the database to look up.

    Returns:
        tuple: A tuple containing two elements:
            - result (str): The source type of the database ('bigquery' or 'postgres'), or an error message if not found or an exception occurs.
            - invalid_response (bool): A flag indicating whether an error occurred during retrieval (True) or if the response is valid (False).

    Raises:
        Exception: If there is an issue connecting to or querying the vector store. The exception message will be included in the returned `result`.
    """
    try: 
        if VECTOR_STORE=='bigquery-vector': 
            sql=f'''SELECT
        DISTINCT source_type AS table_schema
        FROM
        `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.table_details_embeddings`
        where table_schema='{user_database}' '''

        else:
            sql=f'''SELECT
        DISTINCT source_type AS table_schema
        FROM
        table_details_embeddings where table_schema='{user_database}' '''
        
        result = vector_connector.retrieve_df(sql)
        result = (str(result.iloc[0, 0])).lower() 
        invalid_response=False
    except Exception as e:
        result="Error at finding the datasource :: "+str(e)
        invalid_response=True
    return result,invalid_response



############################
###_____GENERATE SQL_____###
############################
async def generate_sql(user_question,
                user_database,  
                RUN_DEBUGGER,
                DEBUGGING_ROUNDS, 
                LLM_VALIDATION,
                Embedder_model,
                SQLBuilder_model,
                SQLChecker_model,
                SQLDebugger_model,
                num_table_matches,
                num_column_matches,
                table_similarity_threshold,
                column_similarity_threshold,
                example_similarity_threshold,
                num_sql_matches):
    """Generates an SQL query based on a user's question and database.

    This asynchronous function orchestrates a pipeline to generate an SQL query from a natural language question.
    It leverages various agents for embedding, SQL building, validation, and debugging.

    Args:
        user_question (str): The user's natural language question.
        user_database (str): The name of the database to query.
        RUN_DEBUGGER (bool): Whether to run the SQL debugger.
        DEBUGGING_ROUNDS (int): The number of debugging rounds to perform.
        LLM_VALIDATION (bool): Whether to use LLM for validation.
        Embedder_model (str): The name of the embedding model.
        SQLBuilder_model (str): The name of the SQL builder model.
        SQLChecker_model (str): The name of the SQL checker model.
        SQLDebugger_model (str): The name of the SQL debugger model.
        num_table_matches (int): The number of table matches to retrieve.
        num_column_matches (int): The number of column matches to retrieve.
        table_similarity_threshold (float): The similarity threshold for table matching.
        column_similarity_threshold (float): The similarity threshold for column matching.
        example_similarity_threshold (float): The similarity threshold for example matching.
        num_sql_matches (int): The number of similar SQL queries to retrieve.

    Returns:
        tuple: A tuple containing:
            - final_sql (str): The final generated SQL query, or an error message if generation failed.
            - invalid_response (bool): True if the response is invalid (e.g., due to an error), False otherwise.
    """

    try:
        ## LOAD AGENTS 
        print("Loading Agents.")
        embedder = EmbedderAgent(Embedder_model) 
        SQLBuilder = BuildSQLAgent(SQLBuilder_model)
        SQLChecker = ValidateSQLAgent(SQLChecker_model)
        SQLDebugger = DebugSQLAgent(SQLDebugger_model)

        found_in_vector = 'N' # if an exact query match was found 
        final_sql='Not Generated Yet' # final generated SQL 
        process_step='Not Started'
        error_msg=''
        corrected_sql = ''


        DATA_SOURCE,src_invalid = get_source_type(user_database)
        
        if src_invalid:
            raise ValueError(DATA_SOURCE)

        #vertexai.init(project=PROJECT_ID, location=region)
        #aiplatform.init(project=PROJECT_ID, location=region)

        print("Source selected as : "+ str(DATA_SOURCE) + "\nSchema or Dataset Name is : "+ str(user_database))
        print("Vector Store selected as : "+ str(VECTOR_STORE))

        # Reset AUDIT_TEXT
        AUDIT_TEXT = 'Creating embedding for given question'
        # Fetch the embedding of the user's input question 
        embedded_question = embedder.create(user_question)

        

        AUDIT_TEXT = AUDIT_TEXT + "\nUser Question : " + str(user_question) + "\nUser Database : " + str(user_database)
        process_step = "\n\nGet Exact Match: "

        # Look for exact matches in known questions IF kgq is enabled 
        if EXAMPLES: 
            exact_sql_history = vector_connector.getExactMatches(user_question) 

        else: exact_sql_history = None 

        # If exact user query has been found, retrieve the SQL and skip Generation Pipeline 
        if exact_sql_history is not None:
            found_in_vector = 'Y' 
            final_sql = exact_sql_history
            invalid_response = False
            AUDIT_TEXT = AUDIT_TEXT + "\nExact match has been found! Going to retreive the SQL query from cache and serve!"


        else:
            # No exact match found. Proceed looking for similar entries in db IF kgq is enabled 
            if EXAMPLES: 
                AUDIT_TEXT = AUDIT_TEXT +  process_step + "\nNo exact match found in query cache, retreiving revelant schema and known good queries for few shot examples using similarity search...."
                process_step = "\n\nGet Similar Match: "
                if call_await:
                    similar_sql = await vector_connector.getSimilarMatches('example', user_database, embedded_question, num_sql_matches, example_similarity_threshold)
                else:
                    similar_sql = vector_connector.getSimilarMatches('example', user_database, embedded_question, num_sql_matches, example_similarity_threshold)

            else: similar_sql = "No similar SQLs provided..."

            process_step = "\n\nGet Table and Column Schema: "
            # Retrieve matching tables and columns
            if call_await: 
                table_matches =  await vector_connector.getSimilarMatches('table', user_database, embedded_question, num_table_matches, table_similarity_threshold)
                column_matches =  await vector_connector.getSimilarMatches('column', user_database, embedded_question, num_column_matches, column_similarity_threshold)
            else:
                table_matches =  vector_connector.getSimilarMatches('table', user_database, embedded_question, num_table_matches, table_similarity_threshold)
                column_matches =  vector_connector.getSimilarMatches('column', user_database, embedded_question, num_column_matches, column_similarity_threshold)

            AUDIT_TEXT = AUDIT_TEXT +  process_step + "\nRetrieved Similar Known Good Queries, Table Schema and Column Schema: \n" + '\nRetrieved Tables: \n' + str(table_matches) + '\n\nRetrieved Columns: \n' + str(column_matches) + '\n\nRetrieved Known Good Queries: \n' + str(similar_sql)
            
            
            # If similar table and column schemas found: 
            if len(table_matches.replace('Schema(values):','').replace(' ','')) > 0 or len(column_matches.replace('Column name(type):','').replace(' ','')) > 0 :

                # GENERATE SQL
                process_step = "\n\nBuild SQL: "
                generated_sql = SQLBuilder.build_sql(DATA_SOURCE,user_question,table_matches,column_matches,similar_sql)
                final_sql=generated_sql
                AUDIT_TEXT = AUDIT_TEXT + process_step +  "\nGenerated SQL : " + str(generated_sql)
                
                if 'unrelated_answer' in generated_sql :
                    invalid_response=True

                # If agent assessment is valid, proceed with checks  
                else:
                    invalid_response=False

                    if RUN_DEBUGGER: 
                        generated_sql, invalid_response, AUDIT_TEXT = SQLDebugger.start_debugger(DATA_SOURCE, generated_sql, user_question, SQLChecker, table_matches, column_matches, AUDIT_TEXT, similar_sql, DEBUGGING_ROUNDS, LLM_VALIDATION) 
                        # AUDIT_TEXT = AUDIT_TEXT + '\n Feedback from Debugger: \n' + feedback_text

                    final_sql=generated_sql
                    AUDIT_TEXT = AUDIT_TEXT + "\nFinal SQL after Debugger: \n" +str(final_sql)


            # No matching table found 
            else:
                invalid_response=True
                print('No tables found in Vector ...')
                AUDIT_TEXT = AUDIT_TEXT + "\nNo tables have been found in the Vector DB. The question cannot be answered with the provide data source!"

        # print(f'\n\n AUDIT_TEXT: \n {AUDIT_TEXT}')
    
        if LOGGING: 
            bqconnector.make_audit_entry(DATA_SOURCE, user_database, SQLBuilder_model, user_question, final_sql, found_in_vector, "", process_step, error_msg,AUDIT_TEXT)  


    except Exception as e:
        error_msg=str(e)
        final_sql="Error generating the SQL Please check the logs. "+str(e)
        invalid_response=True
        AUDIT_TEXT="Exception at SQL generation"


    return final_sql,invalid_response


############################
###_____GET RESULTS_____####
############################
def get_results(user_database, final_sql, invalid_response=False, EXECUTE_FINAL_SQL=True):
    """Executes the final SQL query (if valid) and retrieves the results.

    This function first determines the data source (BigQuery or PostgreSQL) based on the provided database name.
    If the SQL query is valid and execution is enabled, it fetches the results using the appropriate connector.

    Args:
        user_database (str): The name of the database to query.
        final_sql (str): The final SQL query to execute.
        invalid_response (bool, optional): A flag indicating whether the SQL query is invalid. Defaults to False.
        EXECUTE_FINAL_SQL (bool, optional): Whether to execute the final SQL query. Defaults to True.

    Returns:
        tuple: A tuple containing:
            - result_df (pandas.DataFrame or str): The results of the SQL query as a DataFrame, or an error message if the query is invalid or execution failed.
            - invalid_response (bool): True if the response is invalid (e.g., due to an error), False otherwise.

    Raises:
        ValueError: If the data source is invalid or not supported.
        Exception: If there's an error executing the SQL query or retrieving the results.
    """
    
    try:

        DATA_SOURCE,src_invalid = get_source_type(user_database)
        
        if not src_invalid:
            ## SET DATA SOURCE 
            if DATA_SOURCE=='bigquery':
                src_connector = bqconnector
            else: 
                src_connector = pgconnector
        else:
            raise ValueError(DATA_SOURCE)

        if not invalid_response:
            try: 
                if EXECUTE_FINAL_SQL is True:
                        final_exec_result_df=src_connector.retrieve_df(final_sql.replace("```sql","").replace("```","").replace("EXPLAIN ANALYZE ",""))
                        result_df = final_exec_result_df
                        


                else:  # Do not execute final SQL
                        print("Not executing final SQL since EXECUTE_FINAL_SQL variable is False\n ")
                        result_df = "Please enable the Execution of the final SQL so I can provide an answer" 
                        
            except ValueError: 
                result_df= "Error has been encountered :: " + str(e)
                invalid_response=True
                
        else:  # Do not execute final SQL
            result_df = "Not executing final SQL as it is invalid, please debug!"
            
    except Exception as e: 
        print(f"An error occured. Aborting... Error Message: {e}")
        result_df="Error has been encountered :: " + str(e)
        invalid_response=True

    return result_df,invalid_response

def get_response(user_question,result_df,Responder_model='gemini-1.0-pro'):
    try:
        Responder = ResponseAgent(Responder_model)
        _resp=Responder.run(user_question, result_df)
        invalid_response=False
    except Exception as e: 
        print(f"An error occured. Aborting... Error Message: {e}")
        _resp= "Error has been encountered :: " + str(e)
        invalid_response=True

    return _resp,invalid_response

############################
###_____RUN PIPELINE_____###
############################
async def run_pipeline(user_question,
                user_database,
                RUN_DEBUGGER=True,
                EXECUTE_FINAL_SQL=True,
                DEBUGGING_ROUNDS = 2, 
                LLM_VALIDATION=True,
                Embedder_model='vertex',
                SQLBuilder_model= 'gemini-1.5-pro',
                SQLChecker_model= 'gemini-1.0-pro',
                SQLDebugger_model= 'gemini-1.0-pro',
                Responder_model= 'gemini-1.0-pro',
                num_table_matches = 5,
                num_column_matches = 10,
                table_similarity_threshold = 0.3,
                column_similarity_threshold = 0.3, 
                example_similarity_threshold = 0.3, 
                num_sql_matches=3): 
    """Orchestrates the end-to-end SQL generation and response pipeline.

    This asynchronous function manages the entire process of generating an SQL query from a user's question,
    executing the query (if valid), and formulating a natural language response based on the results.

    Args:
        user_question (str): The user's natural language question.
        user_database (str): The name of the database to query.
        RUN_DEBUGGER (bool, optional): Whether to run the SQL debugger. Defaults to True.
        EXECUTE_FINAL_SQL (bool, optional): Whether to execute the final SQL query. Defaults to True.
        DEBUGGING_ROUNDS (int, optional): The number of debugging rounds to perform. Defaults to 2.
        LLM_VALIDATION (bool, optional): Whether to use LLM for validation. Defaults to True.
        Embedder_model (str, optional): The name of the embedding model. Defaults to 'vertex'.
        SQLBuilder_model (str, optional): The name of the SQL builder model. Defaults to 'gemini-1.5-pro'.
        SQLChecker_model (str, optional): The name of the SQL checker model. Defaults to 'gemini-1.0-pro'.
        SQLDebugger_model (str, optional): The name of the SQL debugger model. Defaults to 'gemini-1.0-pro'.
        Responder_model (str, optional): The name of the responder model. Defaults to 'gemini-1.0-pro'.
        num_table_matches (int, optional): The number of table matches to retrieve. Defaults to 5.
        num_column_matches (int, optional): The number of column matches to retrieve. Defaults to 10.
        table_similarity_threshold (float, optional): The similarity threshold for table matching. Defaults to 0.3.
        column_similarity_threshold (float, optional): The similarity threshold for column matching. Defaults to 0.3.
        example_similarity_threshold (float, optional): The similarity threshold for example matching. Defaults to 0.3.
        num_sql_matches (int, optional): The number of similar SQL queries to retrieve. Defaults to 3.

    Returns:
        tuple: A tuple containing:
            - final_sql (str): The final generated SQL query, or an error message if generation failed.
            - results_df (pandas.DataFrame or str): The results of the SQL query as a DataFrame, or an error message if the query is invalid or execution failed.
            - _resp (str): The generated natural language response based on the results, or an error message if response generation failed.
    """
    

    final_sql, invalid_response = await generate_sql(user_question,
                user_database,
                RUN_DEBUGGER,
                DEBUGGING_ROUNDS, 
                LLM_VALIDATION,
                Embedder_model,
                SQLBuilder_model,
                SQLChecker_model,
                SQLDebugger_model,
                num_table_matches,
                num_column_matches,
                table_similarity_threshold,
                column_similarity_threshold,
                example_similarity_threshold,
                num_sql_matches)

    if not invalid_response:
        results_df, invalid_response = get_results(user_database, 
                                    final_sql,
                                    invalid_response=invalid_response,
                                    EXECUTE_FINAL_SQL=EXECUTE_FINAL_SQL)

        if not invalid_response:
            _resp,invalid_response=get_response(user_question,results_df.to_json(orient='records'),Responder_model=Responder_model)
        else:
            _resp=results_df
    else:
        results_df=final_sql
        _resp=final_sql

    return final_sql, results_df, _resp


############################
#####_____GET KGQ_____######
############################
def get_kgq(user_database):
    """Retrieves known good SQL queries (KGQs) for a specific database from the vector store.

    This function queries the vector store (BigQuery or PostgreSQL) to fetch a limited number of
    distinct user questions and their corresponding generated SQL queries that are relevant to the
    specified database. These KGQs can be used as examples or references for generating new SQL queries.

    Args:
        user_database (str): The name of the database for which to retrieve KGQs.

    Returns:
        tuple: A tuple containing two elements:
            - result (str): A JSON-formatted string containing the list of KGQs (user questions and SQL queries),
                            or an error message if an exception occurs.
            - invalid_response (bool): A flag indicating whether an error occurred during retrieval (True)
                                      or if the response is valid (False).

    Raises:
        Exception: If there is an issue connecting to or querying the vector store.
                   The exception message will be included in the returned `result`.
    """  
    try:
        if VECTOR_STORE=='bigquery-vector': 
            sql=f'''SELECT distinct
        example_user_question,
        example_generated_sql 
        FROM
        `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.example_prompt_sql_embeddings`
        where table_schema='{user_database}'  LIMIT 5 '''

        else:
            sql="""select distinct
        example_user_question,
        example_generated_sql 
        from example_prompt_sql_embeddings
        where table_schema = '{user_database}' LIMIT 5""".format(user_database=user_database)

        result = vector_connector.retrieve_df(sql)
        result = result.to_json(orient='records')
        invalid_response = False

    except Exception as e:
        result="Issue was encountered while extracting known good sqls in vector store:: "  + str(e)
        invalid_response=True
    return result,invalid_response


############################
####_____EMBED SQL_____#####
############################
async def embed_sql(user_database,user_question,generate_sql):
    """Embeds a generated SQL query into the vector store as an example.

    This asynchronous function takes a user's question, a generated SQL query, and a database name as input.
    It calls the `add_sql_embedding` function to create an embedding of the SQL query and store it in the vector store,
    potentially for future reference as a known good query (KGQ).

    Args:
        user_database (str): The name of the database associated with the query.
        user_question (str): The user's original question.
        generate_sql (str): The SQL query generated from the user's question.

    Returns:
        tuple: A tuple containing two elements:
            - embedded (str or None): The embedded SQL query if successful, or an error message if an exception occurs.
            - invalid_response (bool): A flag indicating whether an error occurred during embedding (True)
                                      or if the response is valid (False).

    Raises:
        Exception: If there is an issue with the embedding process.
                   The exception message will be included in the returned `embedded` value.
    """ 
    try:
        embedded = await add_sql_embedding(user_question, generate_sql,user_database)
        invalid_response=False

    except Exception as e: 
        embedded="Issue was encountered while embedding the SQL as example."  + str(e)
        invalid_response=True

    return embedded,invalid_response




############################
#######_____MAIN_____#######
############################
if __name__ == '__main__': 
    # user_question = "How many movies have review ratings above 5?"
    # user_question="What are the top 5 cities with highest recalls?"
    # user_database='food' #user database is BQ_DATASET_NAME for BQ Source or PG_SCHEMA for PostgreSQL as source, add the value accordingly

    parser = argparse.ArgumentParser(description="Open Data QnA SQL Generation")
    parser.add_argument("--user_question", type=str, required=True, help="The user's question.")
    parser.add_argument("--user_database", type=str, required=True, help="The user database to query (BQ_DATASET_NAME for BQ Source or PG_SCHEMA for PostgreSQL as source, add the value accordingly)")

    # Optional Arguments for run_pipeline Parameters
    parser.add_argument("--run_debugger", action="store_true", help="Enable the debugger (default: False)")
    parser.add_argument("--execute_final_sql", action="store_true", help="Execute the final SQL (default: False)")
    parser.add_argument("--debugging_rounds", type=int, default=2, help="Number of debugging rounds (default: 2)")
    parser.add_argument("--llm_validation", action="store_true", help="Enable LLM validation (default: False)")
    parser.add_argument("--embedder_model", type=str, default='vertex', help="Embedder model name (default: 'vertex')")
    parser.add_argument("--sqlbuilder_model", type=str, default='gemini-1.0-pro', help="SQL builder model name (default: 'gemini-1.0-pro')")
    parser.add_argument("--sqlchecker_model", type=str, default='gemini-1.0-pro', help="SQL checker model name (default: 'gemini-1.0-pro')")
    parser.add_argument("--sqldebugger_model", type=str, default='gemini-1.0-pro', help="SQL debugger model name (default: 'gemini-1.0-pro')")
    parser.add_argument("--responder_model", type=str, default='gemini-1.0-pro', help="Responder model name (default: 'gemini-1.0-pro')")
    parser.add_argument("--num_table_matches", type=int, default=5, help="Number of table matches (default: 5)")
    parser.add_argument("--num_column_matches", type=int, default=10, help="Number of column matches (default: 10)")
    parser.add_argument("--table_similarity_threshold", type=float, default=0.1, help="Threshold for table similarity (default: 0.1)")
    parser.add_argument("--column_similarity_threshold", type=float, default=0.1, help="Threshold for column similarity (default: 0.1)")
    parser.add_argument("--example_similarity_threshold", type=float, default=0.1, help="Threshold for example similarity (default: 0.1)")
    parser.add_argument("--num_sql_matches", type=int, default=3, help="Number of SQL matches (default: 3)")

    args = parser.parse_args()

    # Use Argument Values in run_pipeline
    final_sql, response, _resp = asyncio.run(run_pipeline(
        args.user_question,
        args.user_database,
        RUN_DEBUGGER=args.run_debugger,
        EXECUTE_FINAL_SQL=args.execute_final_sql,
        DEBUGGING_ROUNDS=args.debugging_rounds,
        LLM_VALIDATION=args.llm_validation,
        Embedder_model=args.embedder_model,
        SQLBuilder_model=args.sqlbuilder_model,
        SQLChecker_model=args.sqlchecker_model,
        SQLDebugger_model=args.sqldebugger_model,
        Responder_model=args.responder_model,
        num_table_matches=args.num_table_matches,
        num_column_matches=args.num_column_matches,
        table_similarity_threshold=args.table_similarity_threshold,
        column_similarity_threshold=args.column_similarity_threshold,
        example_similarity_threshold=args.example_similarity_threshold,
        num_sql_matches=args.num_sql_matches
    ))

    # user_question = "How many +18 movies have a rating above 4?"

    # final_sql, response, _resp = asyncio.run(run_pipeline(user_question,
    #                                                 'imdb', 
    #                                                 RUN_DEBUGGER=True,
    #                                                 EXECUTE_FINAL_SQL=True,
    #                                                 DEBUGGING_ROUNDS = 2, 
    #                                                 LLM_VALIDATION=True,
    #                                                 Embedder_model='vertex',
    #                                                 SQLBuilder_model= 'gemini-1.0-pro',
    #                                                 SQLChecker_model= 'gemini-1.0-pro',
    #                                                 SQLDebugger_model= 'gemini-1.0-pro',
    #                                                 Responder_model= 'gemini-1.0-pro',
    #                                                 num_table_matches = 5,
    #                                                 num_column_matches = 10,
    #                                                 table_similarity_threshold = 0.1,
    #                                                 column_similarity_threshold = 0.1, 
    #                                                 example_similarity_threshold = 0.1, 
    #                                                 num_sql_matches=3))
    
    
    print("*"*50 +"\nGenerated SQL\n"+"*"*50+"\n"+final_sql)
    print("\n"+"*"*50 +"\nResults\n"+"*"*50)
    print(response)
    print("*"*50 +"\nNatural Response\n"+"*"*50+"\n"+_resp)