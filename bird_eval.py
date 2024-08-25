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



import json
import re 
import os 
from google.cloud import bigquery
import asyncio
import pandas as pd
from pandas.testing import assert_frame_equal
from dbconnectors import bqconnector, pgconnector
from agents import DebugSQLAgent
from bird_kgq_context import retrieve_kgq_examples

from utilities import PROJECT_ID
import sqlite3
import json
from agents import EmbedderAgent, BuildSQLAgent, DebugSQLAgent, ValidateSQLAgent, ResponseAgent,VisualizeAgent





def retrieve_matches(project_id, dataset, opendataqna_dataset, mode, qe, similarity_threshold, limit): 
    """
    This function retrieves the most similar table_schema and column_schema.
    Modes can be either 'table', 'column', or 'example' 
    """
    matches = []
    
    if mode == 'column':
        # sql='''select base.content as columns_content from vector_search(TABLE `{}.column_details_embeddings`, "description_embeddings",
        # (SELECT {} as qe), top_k=> {}, distance_type=>"COSINE") where 1-distance > {} '''
        sql = '''select base.content as columns_content 
        from vector_search(TABLE `{}`, "content_embeddings", 
            (SELECT {} as qe), top_k => {}, distance_type => "COSINE") 
        where 1-distance > {} '''

    elif mode == 'example': 
        sql='''select base.example_user_question, base.example_generated_sql from vector_search ( TABLE `{}.example_prompt_sql_embeddings`, "embedding",
        (select {} as qe), top_k=> {}, distance_type=>"COSINE") where 1-distance > {} '''

    else: 
        ValueError("No valid mode. Must be either table, column, or example")
        name_txt = ''

    # results=bqconnector.client.query_and_wait(sql.format('{}.{}'.format(project_id, opendataqna_dataset),qe,limit,similarity_threshold)).to_dataframe()
    results = bqconnector.client.query_and_wait(
    sql.format(
        f'{project_id}.{opendataqna_dataset}.{dataset}',  # Include the variable here
        qe, 
        limit, 
        similarity_threshold
    )).to_dataframe()

    
    # CHECK RESULTS 
    if len(results) == 0:
        print(f"Did not find any results for {mode}. Adjust the query parameters.")
    else:
        print(f"Found {len(results)} similarity matches for {mode}.")

    if mode == 'column': 
        name_txt = '' 
        for _ ,r in results.iterrows():
            name_txt=name_txt+r["columns_content"]+"\n"

    elif mode == 'example': 
        name_txt = ''
        for _ , r in results.iterrows():
            example_user_question=r["example_user_question"]
            example_sql=r["example_generated_sql"]
            name_txt = name_txt + "\n Example_question: "+example_user_question+ "; Example_SQL: "+example_sql

    else: 
        ValueError("No valid mode. Must be either table, column, or example")
        name_txt = ''

    matches.append(name_txt)
    

    return matches



############################
###_____GENERATE SQL_____###
############################
def generate_sql(user_question,
                evidence,
                dataset,
                Embedder_model,
                SQLBuilder_model,
                num_column_matches = 10, 
                num_example_matches = 10, 
                example_similarity_threshold = 0.8, 
                column_similarity_threshold = 0.6,
                user_grouping = '', 
                temp = 0.4, 
                top_p = 1,
                top_k = 32, 
                EXAMPLES = False):


    try:
        opendataqna_dataset = 'ODQnA_Eval'
        DATA_SOURCE = 'bird'


        ## LOAD AGENTS 
        print("Loading Agents.")
        embedder = EmbedderAgent(Embedder_model) 
        SQLBuilder = BuildSQLAgent(SQLBuilder_model)


        final_sql='Not Generated Yet' # final generated SQL 



        embedded_question = embedder.create(user_question)


        if EXAMPLES: 
            similar_sql = retrieve_kgq_examples(dataset)

        else: similar_sql = "No similar SQLs provided..."

        print("\n\nGet Table and Column Schema: ")

        # Retrieve matching tables and columns
        column_matches =  retrieve_matches(PROJECT_ID, dataset, opendataqna_dataset, 'column', embedded_question, column_similarity_threshold, num_column_matches)
        column_matches = column_matches[0]

        print("\nRetrieved Similar Known Good Queries, Table Schema and Column Schema: \n" + '\n\nRetrieved Columns: \n' + str(column_matches) + '\n\nRetrieved Known Good Queries: \n' + str(similar_sql))
        
        
        # If similar table and column schemas found: 
        if len(column_matches.replace('Column name(type):','').replace(' ','')) > 0 :

            # GENERATE SQL
            print("\n\nBuild SQL: ")
            generated_sql, context_prompt = SQLBuilder.build_sql(DATA_SOURCE,evidence, user_grouping,user_question, None,"",column_matches,similar_sql,temperature=temp, top_p=top_p, top_k=top_k)
            final_sql=generated_sql
            final_sql = final_sql.split("SELECT ")[1]
            final_sql = "SELECT " + final_sql

            final_sql = final_sql.split("</FINAL_ANSWER>")[0]

            print("\nGenerated SQL : " + str(final_sql))
            
            # if 'unrelated_answer' in generated_sql :
            #     invalid_response=True
            #     final_sql="This is an unrelated question for this dataset"

            # # If agent assessment is valid, proceed with checks  
            # else:
            #     invalid_response=False

            #     if RUN_DEBUGGER: 
            #         generated_sql, invalid_response, AUDIT_TEXT = SQLDebugger.start_debugger(DATA_SOURCE,evidence, user_grouping, generated_sql, user_question, SQLChecker, '', column_matches, '', similar_sql, DEBUGGING_ROUNDS, LLM_VALIDATION) 

            #     final_sql=generated_sql


        # No matching table found 
        else:
            invalid_response=True
            print('No columns found in Vector ...')


    except Exception as e:
        final_sql="Error generating the SQL Please check the logs. "+str(e)
        invalid_response=True
        print("An Error occurred: ", e)
    

    return final_sql, column_matches, context_prompt





def execute_sql_on_sqlite(db_file, sql_query, table_info=None):
    """
    Executes an SQL query on a SQLite database file, handling table and column name mapping.

    Args:
        db_file: Path to the SQLite database file.
        sql_query: The SQL query to execute.
        table_info: Dictionary containing table and column information from dev_tables.json.

    Returns:
        The results of the query execution.
    """

    # 1. Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # # 2. Map table and column names in the SQL query
    # for table_name_original, table_name in zip(table_info["table_names_original"], table_info["table_names"]):
    #     sql_query = sql_query.replace(table_name_original, table_name)

    # for _, column_name_original, column_name in table_info["column_names"]:
    #     if column_name_original != "*" and column_name_original is not None:  # Handle '*' and potential None values
    #         sql_query = sql_query.replace(column_name_original, column_name)

    # 3. Execute the query
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
    
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
        conn.close()
        error_msg = ("Error: " + str(e))
        return error_msg

    # 4. Close the connection
    conn.close()
    return results





def compare_results(df1, df2):
    
    try:
        assert(df1==df2)
        return 1 

    except AssertionError as e:
        return 0



def evaluate_for_db(bird_data, db_id, SQLDebugger, loops, use_examples):
    """Evaluates SQL queries in BIRD benchmark for a given database ID."""
    results = []
    i = 0 

    # Embedder_model='vertex'
    # SQLBuilder_model= 'gemini-1.5-pro'
    # num_column_matches = 20 
    # num_example_matches = 10 
    # example_similarity_threshold = 0.8 
    # column_similarity_threshold = 0.6
    # user_grouping = ''
    # temp = 0
    # top_p = 1
    # top_k = 32  



    base_dir = 'eval/dev/dev_databases/'
    database_dir = os.path.join(base_dir, db_id, db_id+'.sqlite')

    for example in bird_data:
    
        #if i>=10: break 

        # Running evals for the specified dataset 
        if example["db_id"] == db_id:
            result_entry = {
                "dataset": example["db_id"],
                "question_id": example["question_id"],
                "question": example["question"],
                "difficulty": example["difficulty"],
                "evidence": example["evidence"],
                "golden_sql": example["SQL"],  # Original SQL
                "generated_sql": None,         # Placeholder for generated SQL
                "ran_debugger": None, 
                "retrieved_columns": None, 
                "debugging_rounds": None,
                "debugged_sql_1": None, 
                "debugged_sql_2": None, 
                "debugged_sql_3": None, 
                "debugged_sql_4": None, 
                "debugged_sql_5": None, 
                "final_sql_valid": None,
                "execution_accuracy": None,      # Placeholder for accuracy
                "error_msg": None, 
                "debugged_sql": None
            }

            question = example["question"]
            evidence = example["evidence"]

            sql_query = example["SQL"]

            golden_result = execute_sql_on_sqlite(database_dir, sql_query)
            
            # # Rewrite SQL so we can execute against BQ 
            # new_sql_query = rewrite_table_names(sql_query, db_id)

            result_entry["golden_result"] = str(golden_result)


            try:
                print("Running Open Data QnA Pipeline")
                final_sql, column_matches, context_prompt = generate_sql(question,
                                                evidence,
                                                db_id, 
                                                Embedder_model=Embedder_model,
                                                SQLBuilder_model= SQLBuilder_model,
                                                num_column_matches = num_column_matches, 
                                                num_example_matches = num_example_matches, 
                                                example_similarity_threshold = example_similarity_threshold, 
                                                column_similarity_threshold = column_similarity_threshold,
                                                user_grouping = '', 
                                                temp = temp, 
                                                top_p = top_p,
                                                top_k = top_k,  
                                                EXAMPLES = use_examples)
                
                result_entry["generated_sql"] = final_sql


                # result_entry["prompt"] = context_prompt

                odqna_result = execute_sql_on_sqlite(database_dir, final_sql)


                # Run Debugger if Error 
                debug_runs = 0 

                if "Error" in odqna_result: 
                    chat_session = SQLDebugger.init_chat('bird','','',column_matches,'')

                while "Error" in odqna_result and debug_runs <= loops: 
                    
                    print("Debugging SQL.")
                    result_entry["ran_debugger"] = True 
                    result_entry["debugging_rounds"] = debug_runs 
                    odqna_result = SQLDebugger.rewrite_sql_chat(evidence, chat_session, final_sql, question, odqna_result)

                    odqna_result = odqna_result.split("SELECT ")[1]
                    odqna_result = "SELECT " + odqna_result

                    odqna_result = odqna_result.split("</FINAL_ANSWER>")[0]

                    print(odqna_result)
                    result_entry["debugged_sql"] = odqna_result

                    item = f"debugged_sql_{debug_runs}"
                    result_entry[item] = odqna_result 


                    # Rerun 
                    odqna_result = execute_sql_on_sqlite(database_dir, odqna_result)

                    debug_runs += 1     


                result_entry["odqna_result"] = str(odqna_result)




                # Calculate Accuracy 

                result = compare_results(golden_result, odqna_result)

                # execution_accuracy = result['accuracy'] * 100
                # print(f"Accuracy: ", execution_accuracy)

                # if result['mismatched_rows']:
                #     print("Mismatched rows at positions:", result['mismatched_rows'])
                # if result['different_columns']:
                #     print("Columns with differences:", result['different_columns'])


                result_entry["execution_accuracy"] = result


                results.append(result_entry)

                i+=1 



            except Exception as e: 
                result_entry["valid"] = False
                result_entry["error_msg"] = str(e)      

                results.append(result_entry)          

                i+=1 


    return results


                                                # Embedder_model=Embedder_model,
                                                # SQLBuilder_model= SQLBuilder_model,
                                                # num_column_matches = num_column_matches, 
                                                # num_example_matches = num_example_matches, 
                                                # example_similarity_threshold = example_similarity_threshold, 
                                                # column_similarity_threshold = column_similarity_threshold,
                                                # user_grouping = '', 
                                                # temp = temp, 
                                                # top_p = top_p,
                                                # top_k = top_k,  



### CONFIGS 
Embedder_model='vertex'
# models = ['gemini-1.5-pro', 'gemini-1.5-flash']
models = ['gemini-1.5-pro']

# SQLBuilder_model= 'gemini-1.5-pro'
# SQLDebugger = DebugSQLAgent('gemini-1.5-pro')


num_column_matches = 500
num_example_matches = 10 
example_similarity_threshold = 0 
column_similarity_threshold = 0
user_grouping = ''

temp = 0.5
top_p = 0.3
top_k = 10  

loops = 3

use_examples = True 

# settings = {
#     "topP1": {
#         "top_p": 0.3, 
#         "top_k": 30
#     },
#     "topP2": {
#         "top_p": 0.6, 
#         "top_k": 30
#     },
#     "topP3": {
#         "top_p": 0.9, 
#         "top_k": 30
#     },
#     "topK1": {
#         "top_p": 0.1, 
#         "top_k": 1
#     },
#     "topK2": {
#         "top_p": 0.1, 
#         "top_k": 10
#     },
#     "topK3": {
#         "top_p": 0.1, 
#         "top_k": 60
#     }
# }

# for setting in settings: 
#     top_p = settings[setting]["top_p"]
#     top_k = settings[setting]["top_k"]  

for model in models: 
    SQLBuilder_model= model
    SQLDebugger = DebugSQLAgent(model)

    # Load the BIRD benchmark data
    with open("eval/dev/dev.json", "r") as f:
        bird_data = json.load(f)

    datasets = ['california_schools','card_games', 'codebase_community', 'debit_card_specializing', 'financial', 'superhero', 'toxicology', 'european_football_2', 'formula_1', 'thrombosis_prediction', 'student_club']  
    # datasets = ['superhero', 'student_club']

    for dataset in datasets:
        evaluation_results = evaluate_for_db(bird_data, dataset, SQLDebugger, loops, use_examples)

        # Save results to CSV

        run = f'FINAL_{dataset}_{SQLBuilder_model}_{num_column_matches}_{column_similarity_threshold}_{temp}_{top_p}_{top_k}_contentEmbeddings'


        csv_file_path = f"eval/results/{run}.csv"
        df = pd.DataFrame(evaluation_results)

        if os.path.isfile(csv_file_path):
            df.to_csv(csv_file_path, mode="a", header=False, index=False)
        else:
            df.to_csv(csv_file_path, index=False)

        print(f"Finished eval for {dataset}")