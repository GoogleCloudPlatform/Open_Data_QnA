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
from opendataqna import run_pipeline
import asyncio
import pandas as pd
from pandas.testing import assert_frame_equal


from utilities import PROJECT_ID

# Load the BIRD benchmark data
with open("eval/dev/dev.json", "r") as f:
    bird_data = json.load(f)




def rewrite_table_names(sql_query, db_id):
    """
    Rewrites table names in a SQL query to include project, dataset, and table identifiers.
    Handles both FROM and INNER JOIN clauses.

    Args:
        sql_query (str): The SQL query to modify.
        PROJECT_ID (str): The Google Cloud Project ID.
        db_id (str): The BigQuery dataset ID.

    Returns:
        str: The modified SQL query with rewritten table names.
    """

    # Pattern to match table names after FROM or INNER JOIN
    pattern = r"(FROM|INNER\s+JOIN)\s+(\w+)"

    # Function to perform the replacement for each match
    def replace_table_name(match):
        clause, table_name = match.groups()
        return f"{clause} `{PROJECT_ID}.{db_id}.{table_name}`"

    # Apply the replacement using re.sub
    sql_query = re.sub(pattern, replace_table_name, sql_query)

    return sql_query



def compare_bigquery_results(df1, df2):
    """Compares two DataFrames from BigQuery results.

    Args:
        df1 (pandas.DataFrame): The first DataFrame.
        df2 (pandas.DataFrame): The second DataFrame.

    Returns:
        dict: A dictionary containing accuracy, mismatched rows, and columns with differences.
    """
    
    try:
        assert_frame_equal(df1, df2)
        return {"accuracy": 1.0, "mismatched_rows": None, "different_columns": None}
    except AssertionError as e:
        mismatch_info = e.args[0]  # No need to split on newlines anymore
        if "shape mismatch" in mismatch_info:
            # Handle shape mismatch
            left_shape = mismatch_info.split('[left]:')[1].split('\n')[0].strip()
            right_shape = mismatch_info.split('[right]:')[1].split('\n')[0].strip()
            return {
                "accuracy": 0.0, 
                "mismatched_rows": None,  # Shape mismatch affects all rows
                "different_columns": None,
                "shape_mismatch": f"Left: {left_shape}, Right: {right_shape}"
            }
        else:
            # Handle row-wise mismatches (same logic as before)
            mismatched_rows = [
                int(x.split(' at position ')[1][:-1]) 
                for x in mismatch_info.split('\n') 
                if "Mismatch in row" in x
            ]
            different_columns = [
                x.split(' ')[3] 
                for x in mismatch_info.split('\n') 
                if 'column' in x
            ]
            accuracy = 1.0 - (len(mismatched_rows) / len(df1))
            return {
                "accuracy": accuracy, 
                "mismatched_rows": mismatched_rows, 
                "different_columns": different_columns
            }



def evaluate_for_db(db_id, client):
    """Evaluates SQL queries in BIRD benchmark for a given database ID."""
    results = []
    i = 0 



    for example in bird_data:
    
        if i>=2: break 

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
                "retrieved_table": None, 
                "valid": None,
                "execution_accuracy": None,      # Placeholder for accuracy
                "error_msg": None
            }

            question = example["question"]
            evidence = example["evidence"]

            sql_query = example["SQL"]
            
            # Rewrite SQL so we can execute against BQ 
            new_sql_query = rewrite_table_names(sql_query, db_id)



            try:
                print("Executing golden SQL.")
                job = client.query(new_sql_query)
                df1 = job.result().to_dataframe()

                print("Running Open Data QnA Pipeline")
                final_sql, response, _resp = asyncio.run(run_pipeline(question,
                                                evidence,
                                                db_id, 
                                                RUN_DEBUGGER=True,
                                                EXECUTE_FINAL_SQL=True,
                                                DEBUGGING_ROUNDS = 2, 
                                                LLM_VALIDATION=True,
                                                Embedder_model='vertex',
                                                SQLBuilder_model= 'gemini-1.5-pro-001',
                                                SQLChecker_model= 'gemini-1.0-pro',
                                                SQLDebugger_model= 'gemini-1.0-pro',
                                                Responder_model= 'gemini-1.0-pro',
                                                num_table_matches = 5,
                                                num_column_matches = 10,
                                                table_similarity_threshold = 0.3,
                                                column_similarity_threshold = 0.3, 
                                                example_similarity_threshold = 0.3, 
                                                num_sql_matches=3))
                
                result_entry["generated_sql"] = final_sql

                print("Executing Open Data QnA SQL")
                job = client.query(final_sql)
                df2 = job.result().to_dataframe()
                result_entry["valid"] = True

                result = compare_bigquery_results(df1, df2)

                execution_accuracy = result['accuracy'] * 100
                print(f"Accuracy: ", execution_accuracy)

                if result['mismatched_rows']:
                    print("Mismatched rows at positions:", result['mismatched_rows'])
                if result['different_columns']:
                    print("Columns with differences:", result['different_columns'])


                result_entry["execution_accuracy"] = execution_accuracy

                results.append(result_entry)

                i+=1 

            except Exception as e:
                result_entry["valid"] = False
                result_entry["error_msg"] = str(e)      

                results.append(result_entry)          
                # results.append({"question": question, "error": str(e), "correct": False})

                i+=1 

    return results



client = bigquery.Client(project=PROJECT_ID)
db_id_to_evaluate = 'california_schools'  # Change to your desired DB

evaluation_results = evaluate_for_db(db_id_to_evaluate, client)

# Save results to CSV

run = 'gemini_1.5_with_evidence_with_debugger'


csv_file_path = f"eval/results/{run}.csv"
df = pd.DataFrame(evaluation_results)

if os.path.isfile(csv_file_path):
    df.to_csv(csv_file_path, mode="a", header=False, index=False)
else:
    df.to_csv(csv_file_path, index=False)