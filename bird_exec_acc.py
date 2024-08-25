
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


import pandas as pd 
import os 


# Specify the run parameters so we can read the correct files 
SQLBuilder_model = 'gemini-1.5-pro'

num_column_matches = 500
num_example_matches = 10 
example_similarity_threshold = 0.8 
column_similarity_threshold = 0
user_grouping = ''
temp = 0.5
top_p = 0.3
top_k = 10  

datasets = ['california_schools','card_games', 'codebase_community', 'debit_card_specializing', 'financial', 'superhero', 'toxicology', 'european_football_2', 'formula_1', 'thrombosis_prediction', 'student_club']  
# datasets = ['superhero', 'student_club']

for dataset in datasets: 
    
    result = {
        "dataset": dataset, 
        "model": SQLBuilder_model, 
        "num_column_matches": num_column_matches, 
        "column_similarity_threshold": column_similarity_threshold, 
        "temp": temp, 
        "top_p": top_p, 
        "top_k": top_k,
        "num_samples": None,  
        "average_accuracy": None 
    }   
    

    run = f'FINAL_{dataset}_{SQLBuilder_model}_{num_column_matches}_{column_similarity_threshold}_{temp}_{top_p}_{top_k}_contentEmbeddings'
    file_path = f"eval/results/{run}.csv"

    df = pd.read_csv(file_path)

    # Convert the "execution_accuracy" column to numeric, coercing non-numeric values to NaN
    df['execution_accuracy'] = pd.to_numeric(df['execution_accuracy'], errors='coerce')

    # Filter out rows where "execution_accuracy" is not 0 or 1
    df_filtered = df[(df['execution_accuracy'] == 0) | (df['execution_accuracy'] == 1)]

    # Calculate the average of the filtered "execution_accuracy" column
    average_accuracy = df_filtered['execution_accuracy'].mean()

    # Get the number of test examples used for eval 
    num_samples = len(df_filtered['execution_accuracy'])


    result["num_samples"] = num_samples
    result["average_accuracy"] = average_accuracy


    result_file = f"eval/results/config_results_{SQLBuilder_model}_{num_column_matches}_{column_similarity_threshold}_{temp}_{top_p}_{top_k}_contentEmbeddings.csv"

    result_df = pd.DataFrame([result])


    if os.path.isfile(result_file):
        result_df.to_csv(result_file, mode="a", header=False, index=False)
    else:
        result_df.to_csv(result_file, index=False)