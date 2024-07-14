
import asyncio
from google.cloud import bigquery
import google.api_core 

from embeddings import retrieve_embeddings, store_schema_embeddings, setup_kgq_table, load_kgq_df, store_kgq_embeddings

from utilities import ( PG_REGION, PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD, 
                        BQ_REGION, 
                       EXAMPLES, LOGGING, VECTOR_STORE, PROJECT_ID, 
                       BQ_OPENDATAQNA_DATASET_NAME) 
import subprocess
import time


if VECTOR_STORE == 'bigquery-vector':
    DATASET_REGION = BQ_REGION

elif VECTOR_STORE == 'cloudsql-pgvector':
    DATASET_REGION = PG_REGION
    
def setup_postgresql(pg_instance, pg_region, pg_database, pg_user, pg_password):
    """Sets up a PostgreSQL Cloud SQL instance with a database and user.

    Args:
        pg_instance (str): Name of the Cloud SQL instance.
        pg_region (str): Region where the instance should be located.
        pg_database (str): Name of the database to create.
        pg_user (str): Name of the user to create.
        pg_password (str): Password for the user.
    """
    
    # Check if Cloud SQL instance exists
    describe_cmd = ["gcloud", "sql", "instances", "describe", pg_instance, "--format=value(databaseVersion)"]
    describe_process = subprocess.run(describe_cmd, capture_output=True, text=True)

    if describe_process.returncode == 0:
        if describe_process.stdout.startswith("POSTGRES"):
            print("Found existing Postgres Cloud SQL Instance!")
        else:
            raise RuntimeError("Existing Cloud SQL instance is not PostgreSQL")
    else:
        print("Creating new Cloud SQL instance...")
        create_cmd = [
            "gcloud", "sql", "instances", "create", pg_instance,
            "--database-version=POSTGRES_15", "--region", pg_region,
            "--cpu=1", "--memory=4GB", "--root-password", pg_password,
            "--database-flags=cloudsql.iam_authentication=On"
        ]
        subprocess.run(create_cmd, check=True)  # Raises an exception if creation fails

        # Wait for instance to be ready
        print("Waiting for instance to be ready...")
        time.sleep(9999)  # You might need to adjust this depending on how long it takes

    # Create the database
    list_cmd = ["gcloud", "sql", "databases", "list", "--instance", pg_instance]
    list_process = subprocess.run(list_cmd, capture_output=True, text=True)

    if pg_database in list_process.stdout:
        print("Found existing Postgres Cloud SQL database!")
    else:
        print("Creating new Cloud SQL database...")
        create_db_cmd = ["gcloud", "sql", "databases", "create", pg_database, "--instance", pg_instance]
        subprocess.run(create_db_cmd, check=True)  

    # Create the user
    create_user_cmd = [
        "gcloud", "sql", "users", "create", pg_user,
        "--instance", pg_instance, "--password", pg_password
    ]
    subprocess.run(create_user_cmd, check=True)

    print(f"PG Database {pg_database} in instance {pg_instance} is ready.")




def create_vector_store():
    """
    Initializes the environment and sets up the vector store for Open Data QnA.

    This function performs the following steps:
        
    1. Loads configurations from the "config.ini" file.
    2. Determines the data source (BigQuery or CloudSQL PostgreSQL) and sets the dataset region accordingly.
    3. If the vector store is "cloudsql-pgvector" and the data source is not CloudSQL PostgreSQL, it creates a new PostgreSQL dataset for the vector store.
    4. If logging is enabled or the vector store is "bigquery-vector", it creates a BigQuery dataset for the vector store and logging table.
    5. It creates a Vertex AI connection for the specified model and embeds the table schemas and columns into the vector database.
    6. If embeddings are stored in BigQuery, creates a table column_details_embeddings in the BigQuery Dataset.
    7. It generates the embeddings for the table schemas and column descriptions, and then inserts those embeddings into the BigQuery table.
   

    Configuration:
        - Requires the following environment variables to be set in "config.ini":
            - `DATA_SOURCE`: The data source (e.g., "bigquery" or "cloudsql-pg").
            - `VECTOR_STORE`: The type of vector store (e.g., "bigquery-vector" or "cloudsql-pgvector").
            - `BQ_REGION`: The BigQuery region.
            - `PROJECT_ID`: The Google Cloud project ID.
            - `BQ_OPENDATAQNA_DATASET_NAME`: The name of the BigQuery dataset for Open Data QnA.
            - `LOGGING`: Whether logging is enabled.

        - If `VECTOR_STORE` is "cloudsql-pgvector" and `DATA_SOURCE` is not "cloudsql-pg":
            - Requires additional environment variables for PostgreSQL instance setup.

    Returns:
        None

    Raises:
        RuntimeError: If there are errors during the setup process (e.g., dataset creation failure).
    """


    print("Initializing environment setup.")
    print("Loading configurations from config.ini file.")



    print("Vector Store source set to: ", VECTOR_STORE)

    # Create PostgreSQL Instance is data source is different from PostgreSQL Instance
    if VECTOR_STORE == 'cloudsql-pgvector' :
        print("Generating pg dataset for vector store.")
        # Parameters for PostgreSQL Instance
        pg_region = DATASET_REGION
        pg_instance = "pg15-opendataqna"
        pg_database = "opendataqna-db"
        pg_user = "pguser"
        pg_password = "pg123"
        pg_schema = 'pg-vector-store' 

        setup_postgresql(pg_instance, pg_region, pg_database, pg_user, pg_password)


    # Create a new data set on Bigquery to use for the logs table
    if LOGGING or VECTOR_STORE == 'bigquery-vector':
        if LOGGING: 
            print("Logging is enabled")

        if VECTOR_STORE == 'bigquery-vector':
            print("Vector store set to 'bigquery-vector'")

        print(f"Generating Big Query dataset {BQ_OPENDATAQNA_DATASET_NAME}")
        client=bigquery.Client(project=PROJECT_ID)
        dataset_ref = f"{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}"


        # Create the dataset if it does not exist already
        try:
            client.get_dataset(dataset_ref)
            print("Destination Dataset exists")
        except google.api_core.exceptions.NotFound:
            print("Cannot find the dataset hence creating.......")
            dataset=bigquery.Dataset(dataset_ref)
            dataset.location=DATASET_REGION
            client.create_dataset(dataset)
            print(str(dataset_ref)+" is created")




def get_embeddings():
    """Generates and returns embeddings for table schemas and column descriptions.

    This function performs the following steps:

    1. Retrieves table schema and column description data based on the specified data source (BigQuery or PostgreSQL).
    2. Generates embeddings for the retrieved data using the configured embedding model.
    3. Returns the generated embeddings for both tables and columns.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing two pandas DataFrames:
            - table_schema_embeddings: Embeddings for the table schemas.
            - col_schema_embeddings: Embeddings for the column descriptions.

    Configuration:
        This function relies on the following configuration variables:
            - DATA_SOURCE: The source database ("bigquery" or "cloudsql-pg").
            - BQ_DATASET_NAME (if DATA_SOURCE is "bigquery"): The BigQuery dataset name.
            - BQ_TABLE_LIST (if DATA_SOURCE is "bigquery"): The list of BigQuery tables to process.
            - PG_SCHEMA (if DATA_SOURCE is "cloudsql-pg"): The PostgreSQL schema name.
    """


    print("Generating embeddings from source db schemas")

    import pandas as pd
    import os

    current_dir = os.getcwd()
    root_dir = os.path.expanduser('~')  # Start at the user's home directory

    while current_dir != root_dir:
        for dirpath, dirnames, filenames in os.walk(current_dir):
            config_path = os.path.join(dirpath, 'data_source_list.csv')
            if os.path.exists(config_path):
                file_path = config_path  # Update root_dir to the found directory
                break  # Stop outer loop once found

        current_dir = os.path.dirname(current_dir)

    print("Source Found at Path :: "+file_path)

    # Load the file
    df_src = pd.read_csv(file_path)
    df_src = df_src.loc[:, ["source", "user_grouping", "schema","table"]]
    df_src = df_src.sort_values(by=["source","user_grouping","schema","table"])
    
    #If no schema Error Out
    if df_src['schema'].astype(str).str.len().min()==0 or df_src['schema'].isna().any():
        raise ValueError("Schema column cannot be empty")


    #Group by for all the tables filtered
    df=df_src.groupby(['source','schema'])['table'].agg(lambda x: list(x.dropna().unique())).reset_index()

    df['table']=df['table'].apply(lambda x: None if pd.isna(x).any() else x)
    
    print("The Embeddings are extracted for the below combinations")
    print(df)
    table_schema_embeddings=pd.DataFrame(columns=['source_type','join_by','table_schema', 'table_name', 'content','embedding'])
    col_schema_embeddings=pd.DataFrame(columns=['source_type','join_by','table_schema', 'table_name', 'column_name', 'content','embedding'])

    for _, row in df.iterrows():
        DATA_SOURCE = row['source']
        SCHEMA = row['schema']
        TABLE_LIST = row['table']
        _t, _c = retrieve_embeddings(DATA_SOURCE, SCHEMA=SCHEMA, table_names=TABLE_LIST)
        _t["source_type"]=DATA_SOURCE
        _c["source_type"]=DATA_SOURCE
        if not TABLE_LIST:
            _t["join_by"]=DATA_SOURCE+"_"+SCHEMA+"_"+SCHEMA
            _c["join_by"]=DATA_SOURCE+"_"+SCHEMA+"_"+SCHEMA
        table_schema_embeddings = pd.concat([table_schema_embeddings,_t],ignore_index=True)
        col_schema_embeddings = pd.concat([col_schema_embeddings,_c],ignore_index=True)

    df_src['join_by'] = df_src.apply(
    lambda row: f"{row['source']}_{row['schema']}_{row['schema']}" if pd.isna(row['table']) else f"{row['source']}_{row['schema']}_{row['table']}",axis=1)

    table_schema_embeddings['join_by'] = table_schema_embeddings['join_by'].fillna(table_schema_embeddings['source_type'] + "_" + table_schema_embeddings['table_schema'] + "_" + table_schema_embeddings['table_name'])


    col_schema_embeddings['join_by'] = col_schema_embeddings['join_by'].fillna(col_schema_embeddings['source_type'] + "_" + col_schema_embeddings['table_schema'] + "_" + col_schema_embeddings['table_name'])



    table_schema_embeddings = table_schema_embeddings.merge(df_src[['join_by', 'user_grouping']], on='join_by', how='left')

    table_schema_embeddings.drop(columns=["join_by"],inplace=True)
    #Replace NaN values in group to default to the schema

    
    table_schema_embeddings['user_grouping'] = table_schema_embeddings['user_grouping'].fillna(table_schema_embeddings['table_schema']+"-"+table_schema_embeddings['source_type'])


    col_schema_embeddings = col_schema_embeddings.merge(df_src[['join_by', 'user_grouping']], on='join_by', how='left')

    col_schema_embeddings.drop(columns=["join_by"],inplace=True)

    #Replace NaN values in group to default to the schema
    col_schema_embeddings['user_grouping'] = col_schema_embeddings['user_grouping'].fillna(col_schema_embeddings['table_schema']+"-"+col_schema_embeddings['source_type'])

    print("Table and Column embeddings are created")


    return table_schema_embeddings, col_schema_embeddings


async def store_embeddings(table_schema_embeddings, col_schema_embeddings):
    """
    Stores table and column embeddings into the specified vector store.

    This asynchronous function saves precomputed embeddings for table schemas and column descriptions 
    into either BigQuery or PostgreSQL (with pgvector extension) based on the VECTOR_STORE configuration.

    Args:
        table_schema_embeddings (pd.DataFrame): Embeddings for the table schemas.
        col_schema_embeddings (pd.DataFrame): Embeddings for the column descriptions.

    Configuration:
        This function relies on the following configuration variables:
            - VECTOR_STORE: Determines the target vector store ("bigquery-vector" or "cloudsql-pgvector").
            - PROJECT_ID, BQ_REGION, BQ_OPENDATAQNA_DATASET_NAME (if VECTOR_STORE is "bigquery-vector"):
                Configuration for BigQuery storage.
            - PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD, PG_REGION (if VECTOR_STORE is "cloudsql-pgvector"):
                Configuration for PostgreSQL storage.

    Returns:
        None
    """

    print("Storing embeddings back to the vector store.")
    if VECTOR_STORE=='bigquery-vector':
        await(store_schema_embeddings(table_details_embeddings=table_schema_embeddings, 
                                    tablecolumn_details_embeddings=col_schema_embeddings, 
                                    project_id=PROJECT_ID,
                                    instance_name=None,
                                    database_name=None,
                                    schema=BQ_OPENDATAQNA_DATASET_NAME,
                                    database_user=None,
                                    database_password=None,
                                    region=BQ_REGION,
                                    VECTOR_STORE = VECTOR_STORE
                                    ))

    elif VECTOR_STORE=='cloudsql-pgvector':
        await(store_schema_embeddings(table_details_embeddings=table_schema_embeddings, 
                                    tablecolumn_details_embeddings=col_schema_embeddings, 
                                    project_id=PROJECT_ID,
                                    instance_name=PG_INSTANCE,
                                    database_name=PG_DATABASE,
                                    schema=None,
                                    database_user=PG_USER,
                                    database_password=PG_PASSWORD,
                                    region=PG_REGION,
                                    VECTOR_STORE = VECTOR_STORE
                                    ))

    print("Table and Column embeddings are saved to vector store")



async def create_kgq_sql_table():
    """
    Creates a table for storing Known Good Query (KGQ) embeddings in the vector store.

    This asynchronous function conditionally sets up a table to store known good SQL queries and their embeddings, 
    which are used to provide examples to the LLM during query generation. The table is created only 
    if the `EXAMPLES` configuration variable is set to 'yes'. If not, it prints a warning message encouraging 
    the user to create a query cache for better results.

    Configuration:
        This function relies on the following configuration variables:
            - EXAMPLES: Determines whether to create the KGQ table ('yes' to create).
            - VECTOR_STORE: Specifies the target vector store ("bigquery-vector" or "cloudsql-pgvector").
            - PROJECT_ID, BQ_REGION, BQ_OPENDATAQNA_DATASET_NAME (if VECTOR_STORE is "bigquery-vector"):
                Configuration for BigQuery storage.
            - PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD, PG_REGION (if VECTOR_STORE is "cloudsql-pgvector"):
                Configuration for PostgreSQL storage.
    
    Returns:
        None
    """
    if EXAMPLES:
        print("Creating kgq table in vector store.")
        # Delete any old tables and create a new table to KGQ embeddings
        if VECTOR_STORE=='bigquery-vector':
            await(setup_kgq_table(project_id=PROJECT_ID,
                                instance_name=None,
                                database_name=None,
                                schema=BQ_OPENDATAQNA_DATASET_NAME,
                                database_user=None,
                                database_password=None,
                                region=BQ_REGION,
                                VECTOR_STORE = VECTOR_STORE
                                ))

        elif VECTOR_STORE=='cloudsql-pgvector':
            await(setup_kgq_table(project_id=PROJECT_ID,
                                instance_name=PG_INSTANCE,
                                database_name=PG_DATABASE,
                                schema=None,
                                database_user=PG_USER,
                                database_password=PG_PASSWORD,
                                region=PG_REGION,
                                VECTOR_STORE = VECTOR_STORE
                                ))
    else:
        print("⚠️ WARNING: No Known Good Queries are provided to create query cache for Few shot examples!")
        print("Creating a query cache is highly recommended for best outcomes")
        print("If no Known Good Queries for the dataset are availabe at this time, you can use 3_LoadKnownGoodSQL.ipynb to load them later!!")




async def store_kgq_sql_embeddings():
    """
    Stores known good query (KGQ) embeddings into the specified vector store.

    This asynchronous function reads known good SQL queries from the "known_good_sql.csv" file
    and stores their embeddings in either BigQuery or PostgreSQL (with pgvector) depending on the
    `VECTOR_STORE` configuration. This process is only performed if the `EXAMPLES` configuration 
    variable is set to 'yes'. Otherwise, a warning message is displayed, highlighting the 
    importance of creating a query cache.

    Configuration:
        - Requires the "known_good_sql.csv" file to be present in the project directory.
        - Relies on the following configuration variables:
            - `EXAMPLES`: Determines whether to store KGQ embeddings ('yes' to store).
            - `VECTOR_STORE`: Specifies the target vector store ("bigquery-vector" or "cloudsql-pgvector").
            - `PROJECT_ID`, `BQ_REGION`, `BQ_OPENDATAQNA_DATASET_NAME` (if VECTOR_STORE is "bigquery-vector"):
                Configuration for BigQuery storage.
            - `PG_INSTANCE`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`, `PG_REGION` (if VECTOR_STORE is "cloudsql-pgvector"):
                Configuration for PostgreSQL storage.

    Returns:
        None
    """
    if EXAMPLES:
        print("Reading contents of known_good_sql.csv")
        # Load the contents of the known_good_sql.csv file into a dataframe
        df_kgq = load_kgq_df()



        print("Storing kgq embeddings in vector store table.")
        # Add KGQ to the vector store
        if VECTOR_STORE=='bigquery-vector':
            await(store_kgq_embeddings(df_kgq,
                                    project_id=PROJECT_ID,
                                        instance_name=None,
                                        database_name=None,
                                        schema=BQ_OPENDATAQNA_DATASET_NAME,
                                        database_user=None,
                                        database_password=None,
                                        region=BQ_REGION,
                                        VECTOR_STORE = VECTOR_STORE
                                        ))

        elif VECTOR_STORE=='cloudsql-pgvector':
            await(store_kgq_embeddings(df_kgq,
                                    project_id=PROJECT_ID,
                                        instance_name=PG_INSTANCE,
                                        database_name=PG_DATABASE,
                                        schema=None,
                                        database_user=PG_USER,
                                        database_password=PG_PASSWORD,
                                        region=PG_REGION,
                                        VECTOR_STORE = VECTOR_STORE
                                        ))
        print('kgq embeddings stored.')

    else:
        print("⚠️ WARNING: No Known Good Queries are provided to create query cache for Few shot examples!")
        print("Creating a query cache is highly recommended for best outcomes")
        print("If no Known Good Queries for the dataset are availabe at this time, you can use 3_LoadKnownGoodSQL.ipynb to load them later!!")


def create_firestore_db(firestore_region,firestore_database="opendataqna-session-logs"):

    # Check if Firestore database exists
    database_exists_cmd = [
        "gcloud", "firestore", "databases", "list", 
        "--filter", f"name=projects/{PROJECT_ID}/databases/{firestore_database}", 
        "--format", "value(name)"  # Extract just the name if found
    ]

    database_exists_process = subprocess.run(
        database_exists_cmd, capture_output=True, text=True
    )
    
    if database_exists_process.returncode == 0 and database_exists_process.stdout:
        if database_exists_process.stdout.startswith(f"projects/{PROJECT_ID}/databases/{firestore_database}"):
            print("Found existing Firestore database with this name already!")
        else:
            raise RuntimeError("Issue with checking if the firestore db exists or not")
    else:
        # Create Firestore database
        print("Creating new Firestore database...")
        create_db_cmd = [
            "gcloud", "firestore", "databases", "create", 
            "--database", firestore_database,
            "--location", firestore_region
        ]
        subprocess.run(create_db_cmd, check=True)  # Raise exception on failure

        # Potential wait for database readiness (optional)
        time.sleep(30)  # May not be strictly necessary for basic use





if __name__ == '__main__':
    # Setup vector store for embeddings
    create_vector_store()  

    # Generate embeddings for tables and columns
    table_schema_embeddings, col_schema_embeddings = get_embeddings()  

    # Store table/column embeddings (asynchronous)
    asyncio.run(store_embeddings(table_schema_embeddings, col_schema_embeddings)) 

    # Create table for known good queries (if enabled)
    asyncio.run(create_kgq_sql_table()) 

    # Store known good query embeddings (if enabled)
    asyncio.run(store_kgq_sql_embeddings())

    create_firestore_db(firestore_region)  

