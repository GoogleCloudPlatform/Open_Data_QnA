## Follow the below guide to populate your config.ini file: 

______________

**[CONFIG]**

**embedding_model = vertex**     *;Options: 'vertex' or 'vertex-lang'*

**description_model = gemini-1.0-pro**   *;Options 'gemini-1.0-pro', 'text-bison-32k'*

**data_source = bigquery**    *;Options: 'bigquery' and 'cloudsql-pg'* 

**vector_store = bigquery-vector**    *;Options: 'bigquery-vector', 'cloudsql-pgvector'*

**debugging = yes**    *;if debugging is enabled. yes or no*

**logging = yes**    *;if logging is enabled. yes or no* 

**kgq_examples = no**    *;if known-good-queries are provided. yes or no.* 


**[GCP]**

**project_id = my_project**    *;your GCP project* 


*; fill out the values below if you want to use PG as your source database:*

**[PGCLOUDSQL]**

**pg_region = us-central1**   

**pg_instance = pg15-opendataqna**

**pg_database = opendataqna-db**

**pg_user = pguser**

**pg_password = pg123**

**pg_schema = pg-vector-store**


*; fill out the values below if you want to use BQ as your source database:* 

**[BIGQUERY]**

**bq_dataset_region = us-central1**

**bq_dataset_name = fda_food**


*; the remaining values are the settings for the BQ vector store / log dataset and table created by the solution:* 

**bq_opendataqna_dataset_name = opendataqna**

**bq_log_table_name = audit_log_table**


*; you can specify an array of table names if you don't want to parse every table in your BQ dataset:* 

**bq_table_list= None**    *; either None or ['table1','table2']*


________________
