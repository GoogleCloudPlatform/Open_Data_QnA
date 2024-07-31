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



import os 
from google.cloud import bigquery
from opendataqna import run_pipeline
import asyncio
import pandas as pd
from pandas.testing import assert_frame_equal
from google.cloud import bigquery
import google.api_core 
import sqlite3

from utilities import PROJECT_ID, EMBEDDING_MODEL
from agents import EmbedderAgent

embedder = EmbedderAgent(EMBEDDING_MODEL)



def get_embedding_chunked(textinput, batch_size): 
    for i in range(0, len(textinput), batch_size):
        request = [x["content"] for x in textinput[i : i + batch_size]]
        response = embedder.create(request) # Vertex Textmodel Embedder 

        # Store the retrieved vector embeddings for each chunk back.
        for x, e in zip(textinput[i : i + batch_size], response):
            x["content_embeddings"] = e

    # Store the generated embeddings in a pandas dataframe.
    out_df = pd.DataFrame(textinput)
    return out_df



def get_sample_values(db_path, table_name, column_name, num_samples=5):
    """
    Fetches the 'num_samples' most frequent values from the specified column in the table.

    Args:
        db_path: Path to the SQLite database file.
        table_name: Name of the table to query.
        column_name: The name of the column to sample from
        num_samples: Number of most frequent values to fetch (default 5).

    Returns:
        A list of the 'num_samples' most frequent values from the specified column
    """

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f"""
        SELECT `{column_name}` 
        FROM {table_name}
        WHERE `{column_name}` IS NOT NULL
        GROUP BY `{column_name}`
        ORDER BY COUNT(*) DESC
        LIMIT {num_samples};
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Extract the values from the result tuples
    sample_values = [row[0] for row in results]

    conn.close()

    return sample_values






######################################################
###_____SETUP VECTOR STORE DATASET ON BIGQUERY_____###
######################################################

schema = 'ODQnA_Eval'
client=bigquery.Client(project=PROJECT_ID)

print(f"Generating Big Query dataset {schema}")
dataset_ref = f"{PROJECT_ID}.{schema}"


# Create the dataset if it does not exist already
try:
    client.get_dataset(dataset_ref)
    print("Destination Dataset exists")
except google.api_core.exceptions.NotFound:
    print("Cannot find the dataset hence creating.......")
    dataset=bigquery.Dataset(dataset_ref)
    dataset.location='us-central1'
    client.create_dataset(dataset)
    print(str(dataset_ref)+" is created")



#############################################
###_____GENERATE EMBEDDINGS FROM FILE_____###
#############################################


# Generate embeddings for columns
# We are going to embed the .csv files provided for the tables in the Bird dev set. 
# For the RAG embeddings, we are taking the column and value descriptions and embedding them for retrieval. 

# Base directory
base_dir = 'eval/dev/dev_databases/'

# List of datasets to process
datasets = ['california_schools']

for dataset in datasets:
    print(f"Processing dataset: {dataset}")

    #Store column embeddings
    client.query_and_wait(f'''CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{schema}.{dataset}` (
                        table_schema string NOT NULL,
                        table_name string NOT NULL, 
                        column_name string NOT NULL,
                        description string NOT NULL,
                        content string, 
                        content_embeddings ARRAY<FLOAT64>,
                        description_embeddings ARRAY<FLOAT64>)''')



    # Construct the path to the CSV file
    database_dir = os.path.join(base_dir, dataset, 'database_description')
    db_dir = os.path.join(base_dir, dataset, dataset+'.sqlite')

    # Loop over the tables in the dataset 
    for filename in os.listdir(database_dir):
        if os.path.isfile(os.path.join(database_dir, filename)):
            table_name, _ = os.path.splitext(filename)  # Split filename and extension
 
            # Read the csv for the table 
            df = pd.read_csv(os.path.join(database_dir, filename))

            print("Loaded csv for table: ", table_name)

            # Concatenate the two description fields for embedding creation 
            df['concatenated_description'] = df['column_description'].astype(str) + ' ' + df['value_description'].astype(str)
            df['concatenated_description'] = df['concatenated_description'].astype(str).str.replace('nan', '', regex=False)

            
            embeddings = list() 

            # Embed the concatenated description field 
            for element in df['concatenated_description']: 
                embedding = embedder.create(element)
                embeddings.append(embedding)

            # df['description_embeddings'] = embeddings

            # Create original ODQnA descriptions for comparison 
            column_details_chunked = []

            for index, row in df.iterrows():

                column_name = str(row['original_column_name'])
                column_name = column_name.strip() 
                column_descr = str(row['concatenated_description'])
                data_type = str(row['data_format'])

                print("Grabbing sample values.")
                top5_sample_values = get_sample_values(db_dir, table_name, column_name)

                column_detailed_description=f"""
                Column Name: {column_name} |
                Table Name : {table_name} |
                Data type: {data_type} |
                Column description: {column_descr} |
                Column sample values: {top5_sample_values}
                """


                r = {"table_schema": dataset,"table_name": table_name,"column_name": column_name, "description": column_descr, "content": column_detailed_description}
                column_details_chunked.append(r)

            print("Creating embeddings.")
            column_details_embeddings = get_embedding_chunked(column_details_chunked, 10)

            column_details_embeddings['description_embeddings'] = embeddings


            print("done")
            
            # Load Dataframe to BQ Vector Store 
            client.load_table_from_dataframe(column_details_embeddings,f'{PROJECT_ID}.{schema}.{dataset}')




