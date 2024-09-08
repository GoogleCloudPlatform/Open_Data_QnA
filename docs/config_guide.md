## Follow the below guide to populate your config.ini file: 

______________

**[CONFIG]**

**embedding_model = vertex**     *;Options: 'vertex' or 'vertex-lang'*

**description_model = gemini-1.0-pro**   *;Options 'gemini-1.0-pro', 'gemini-1.5-pro', 'text-bison-32k', 'gemini-1.5-flash'*

**vector_store = cloudsql-pgvector**    *;Options: 'bigquery-vector', 'cloudsql-pgvector'*

**debugging = yes**    *;if debugging is enabled. yes or no*

**logging = yes**    *;if logging is enabled. yes or no* 

**kgq_examples = yes**    *;if known-good-queries are provided. yes or no.* 

**use_session_history = yes** *;if you want to use current session's questions without re-evaluating them*

**use_column_samples = yes** *;if you want the solution to collect some samples values from the data source columns to imporve understanding of values. yes or no*

**[GCP]**

**project_id = my_project**    *;your GCP project* 


*; fill out the values below if you want to use PG as your vector database:*

**[PGCLOUDSQL]**

**pg_region = us-central1**   

**pg_instance = pg15-opendataqna**

**pg_database = opendataqna-db**

**pg_user = pguser**

**pg_password = pg123**


*; fill out the values below if you want to use BQ as your vector database:* 

**[BIGQUERY]**


*; the remaining values are the settings for the BQ vector store / log dataset and table created by the solution:* 

**bq_dataset_region = us-central1**

**bq_opendataqna_dataset_name = opendataqna**

**bq_log_table_name = audit_log_table**

**firestore_region = us-central** *;region for NoSQL DB firestore region to deploy*


________________
