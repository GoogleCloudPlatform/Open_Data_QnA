"""
BigQuery Connector Class
"""
from google.cloud import bigquery
from google.cloud import bigquery_connection_v1 as bq_connection
from dbconnectors import DBConnector
from abc import ABC
from datetime import datetime
import google.auth
import pandas as pd
from google.cloud.exceptions import NotFound

def get_auth_user():
    credentials, project_id = google.auth.default()

    if hasattr(credentials, 'service_account_email'):
        return credentials.service_account_email
    else:
        return "Not Determined"

def bq_specific_data_types(): 
    return '''
    BigQuery offers a wide variety of datatypes to store different types of data effectively. Here's a breakdown of the available categories:
    Numeric Types -
    INTEGER (INT64): Stores whole numbers within the range of -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807. Ideal for non-fractional values.
    FLOAT (FLOAT64): Stores approximate floating-point numbers with a range of -1.7E+308 to 1.7E+308. Suitable for decimals with a degree of imprecision.
    NUMERIC: Stores exact fixed-precision decimal numbers, with up to 38 digits of precision and 9 digits to the right of the decimal point. Useful for precise financial and accounting calculations.
    BIGNUMERIC: Similar to NUMERIC but with even larger scale and precision. Designed for extreme precision in calculations.
    
    Character Types -
    STRING: Stores variable-length Unicode character sequences. Enclosed using single, double, or triple quotes.
    
    Boolean Type -
    BOOLEAN: Stores logical values of TRUE or FALSE (case-insensitive).
    
    Date and Time Types -
    DATE: Stores dates without associated time information.
    TIME: Stores time information independent of a specific date.
    DATETIME: Stores both date and time information (without timezone information).
    TIMESTAMP: Stores an exact moment in time with microsecond precision, including a timezone component for global accuracy.
    
    Other Types
    BYTES: Stores variable-length binary data. Distinguished from strings by using 'B' or 'b' prefix in values.
    GEOGRAPHY: Stores points, lines, and polygons representing locations on the Earth's surface.
    ARRAY: Stores an ordered collection of zero or more elements of the same (non-ARRAY) data type.
    STRUCT: Stores an ordered collection of fields, each with its own name and data type (can be nested).
    
    This list covers the most common datatypes in BigQuery.
    '''


class BQConnector(DBConnector, ABC):
    """
    A connector class for interacting with BigQuery databases.

    This class provides methods for connecting to BigQuery, executing queries, retrieving results as DataFrames, logging interactions, and managing embeddings.

    Attributes:
        project_id (str): The Google Cloud project ID where the BigQuery dataset resides.
        region (str): The region where the BigQuery dataset is located.
        dataset_name (str): The name of the BigQuery dataset to interact with.
        opendataqna_dataset (str): Name of the dataset to use for OpenDataQnA functionalities.
        audit_log_table_name (str): Name of the table to store audit logs.
        client (bigquery.Client): The BigQuery client instance for executing queries.

    Methods:
        getconn() -> bigquery.Client:
            Establishes a connection to BigQuery and returns a client object.

        retrieve_df(query) -> pd.DataFrame:
            Executes a SQL query and returns the results as a pandas DataFrame.

        make_audit_entry(source_type, user_grouping, model, question, generated_sql, found_in_vector, need_rewrite, failure_step, error_msg, FULL_LOG_TEXT) -> str:
            Logs an audit entry to BigQuery, recording details of the interaction and the generated SQL query.

        create_vertex_connection(connection_id) -> None:
            Creates a Vertex AI connection for remote model usage in BigQuery.

        create_embedding_model(connection_id, embedding_model) -> None:
            Creates or replaces an embedding model in BigQuery using a Vertex AI connection.

        retrieve_matches(mode, user_grouping, qe, similarity_threshold, limit) -> list:
            Retrieves the most similar table schemas, column schemas, or example queries based on the given mode and parameters.

        getSimilarMatches(mode, user_grouping, qe, num_matches, similarity_threshold) -> str:
            Returns a formatted string containing similar matches found for tables, columns, or examples.

        getExactMatches(query) -> str or None:
            Checks if the exact question is present in the example SQL set and returns the corresponding SQL query if found.

        test_sql_plan_execution(generated_sql) -> Tuple[bool, str]:
            Tests the execution plan of a generated SQL query in BigQuery. Returns a tuple indicating success and a message.

        return_table_schema_sql(dataset, table_names=None) -> str:
            Returns a SQL query to retrieve table schema information from a BigQuery dataset.

        return_column_schema_sql(dataset, table_names=None) -> str:
            Returns a SQL query to retrieve column schema information from a BigQuery dataset.
    """


    def __init__(self,
                 project_id:str,
                 region:str,
                 opendataqna_dataset:str,
                 audit_log_table_name:str):

        self.project_id = project_id
        self.region = region
        self.opendataqna_dataset = opendataqna_dataset
        self.audit_log_table_name = audit_log_table_name
        self.client=self.getconn()

    def getconn(self):
        client = bigquery.Client(project=self.project_id)
        return client
    
    def retrieve_df(self,query):
        return self.client.query_and_wait(query).to_dataframe()

    def make_audit_entry(self, source_type, user_grouping, model, question, generated_sql, found_in_vector, need_rewrite, failure_step, error_msg, FULL_LOG_TEXT):
        # global FULL_LOG_TEXT
        auth_user=get_auth_user()

        PROJECT_ID = self.project_id

        table_id= PROJECT_ID+ '.' + self.opendataqna_dataset + '.' + self.audit_log_table_name
        now = datetime.now()

        table_exists=False
        client = self.getconn()

        df1 = pd.DataFrame(columns=[
                'source_type',
                'project_id',
                'user',
                'user_grouping',
                'model_used',
                'question',
                'generated_sql',
                'found_in_vector',
                'need_rewrite',
                'failure_step',
                'error_msg',
                'execution_time',
                'full_log'
                ])

        new_row = {
                "source_type":source_type,
                "project_id":str(PROJECT_ID),
                "user":str(auth_user),
                "user_grouping": user_grouping,
                "model_used": model,
                "question": question,
                "generated_sql": generated_sql,
                "found_in_vector":found_in_vector,
                "need_rewrite":need_rewrite,
                "failure_step":failure_step,
                "error_msg":error_msg,
                "execution_time": now,
                "full_log": FULL_LOG_TEXT
                }

        df1.loc[len(df1)] = new_row

        db_schema=[
                    # Specify the type of columns whose type cannot be auto-detected. For
                    # example the "title" column uses pandas dtype "object", so its
                    # data type is ambiguous.
                    bigquery.SchemaField("source_type", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("project_id", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("user", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("user_grouping", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("model_used", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("question", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("generated_sql", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("found_in_vector", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("need_rewrite", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("failure_step", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("error_msg", bigquery.enums.SqlTypeNames.STRING),
                    bigquery.SchemaField("execution_time", bigquery.enums.SqlTypeNames.TIMESTAMP),
                    bigquery.SchemaField("full_log", bigquery.enums.SqlTypeNames.STRING),
                ]

        try:
            client.get_table(table_id)  # Make an API request.
            # print("Table {} already exists.".format(table_id))
            table_exists=True
        except NotFound:
            print("Table {} is not found. Will create this log table".format(table_id))
            table_exists=False

        if table_exists is True:
            # print('Performing streaming insert')
            errors = client.insert_rows_from_dataframe(table=table_id, dataframe=df1, selected_fields=db_schema)  # Make an API request.
            if errors == [[]]:
                   print("Logged the run")
            else:
                   print("Encountered errors while inserting rows: {}".format(errors))
        else:
            job_config = bigquery.LoadJobConfig(schema=db_schema,write_disposition="WRITE_TRUNCATE")
            # pandas_gbq.to_gbq(df1, table_id, project_id=PROJECT_ID)  # replace to replace table; append to append to a table
            client.load_table_from_dataframe(df1,table_id,job_config=job_config)  # replace to replace table; append to append to a table


        # df1.loc[len(df1)] = new_row
        # pandas_gbq.to_gbq(df1, table_id, project_id=PROJECT_ID, if_exists='append')  # replace to replace table; append to append to a table
            # print('\n Query added to BQ log table \n')
        return 'Completed the logging step'

    def create_vertex_connection(self, connection_id : str):
        client=bq_connection.ConnectionServiceClient()
        
        cloud_resource_properties = bq_connection.types.CloudResourceProperties()
        new_connection=bq_connection.Connection(cloud_resource=cloud_resource_properties)
        response= client.create_connection(parent=f'projects/{self.project_id}/locations/{self.region}',connection=new_connection,connection_id=connection_id)

    
    def create_embedding_model(self,connection_id: str, embedding_model: str):
        client = self.getconn()
        client.query_and_wait(f'''CREATE OR REPLACE MODEL `{self.project_id}.{self.opendataqna_dataset}.EMBEDDING_MODEL`
                                            REMOTE WITH CONNECTION `{self.project_id}.{self.region}.{connection_id}`
                                            OPTIONS (ENDPOINT = '{embedding_model}');''')
   
    
    def retrieve_matches(self, mode, user_grouping, qe, similarity_threshold, limit): 
        """
        This function retrieves the most similar table_schema and column_schema.
        Modes can be either 'table', 'column', or 'example' 
        """
        matches = []

        if mode == 'table':
            sql = '''select base.content as tables_content from vector_search(
                 (SELECT * FROM `{}.table_details_embeddings` WHERE user_grouping = '{}'), "embedding", 
            (SELECT {} as qe), top_k=> {},distance_type=>"COSINE") where 1-distance > {} '''
        
        elif mode == 'column':
            sql='''select base.content as columns_content from vector_search(
                 (SELECT * FROM `{}.tablecolumn_details_embeddings` WHERE user_grouping = '{}'), "embedding",
            (SELECT {} as qe), top_k=> {}, distance_type=>"COSINE") where 1-distance > {} '''

        elif mode == 'example': 
            sql='''select base.example_user_question, base.example_generated_sql from vector_search ( 
                (SELECT * FROM `{}.example_prompt_sql_embeddings` WHERE user_grouping = '{}'), "embedding",
            (select {} as qe), top_k=> {}, distance_type=>"COSINE") where 1-distance > {} '''
    
        else: 
            ValueError("No valid mode. Must be either table, column, or example")
            name_txt = ''

        results=self.client.query_and_wait(sql.format('{}.{}'.format(self.project_id,self.opendataqna_dataset),user_grouping,qe,limit,similarity_threshold)).to_dataframe()
        # CHECK RESULTS 
        if len(results) == 0:
            print(f"Did not find any results for {mode}. Adjust the query parameters.")
        else:
            print(f"Found {len(results)} similarity matches for {mode}.")

        if mode == 'table': 
            name_txt = ''
            for _ , r in results.iterrows():
                name_txt=name_txt+r["tables_content"]+"\n"

        elif mode == 'column': 
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

    def getSimilarMatches(self, mode, user_grouping, qe, num_matches, similarity_threshold):

        if mode == 'table': 
            match_result= self.retrieve_matches(mode, user_grouping, qe, similarity_threshold, num_matches)
            match_result = match_result[0]
            # print(match_result)

        elif mode == 'column': 
            match_result= self.retrieve_matches(mode, user_grouping, qe, similarity_threshold, num_matches)
            match_result = match_result[0]
        
        elif mode == 'example': 
            match_result= self.retrieve_matches(mode, user_grouping, qe, similarity_threshold, num_matches)
            if len(match_result) == 0:
                match_result = None
            else:
                match_result = match_result[0]

        return match_result

    def getExactMatches(self, query):
        """Checks if the exact question is already present in the example SQL set"""
        check_history_sql=f"""SELECT example_user_question,example_generated_sql FROM `{self.project_id}.{self.opendataqna_dataset}.example_prompt_sql_embeddings`
                          WHERE lower(example_user_question) = lower("{query}") LIMIT 1; """

        exact_sql_history = self.client.query_and_wait(check_history_sql).to_dataframe()


        if exact_sql_history[exact_sql_history.columns[0]].count() != 0:
            sql_example_txt = ''
            exact_sql = ''
            for index, row in exact_sql_history.iterrows():
                example_user_question=row["example_user_question"]
                example_sql=row["example_generated_sql"]
                exact_sql=example_sql
                sql_example_txt = sql_example_txt + "\n Example_question: "+example_user_question+ "; Example_SQL: "+example_sql

            # print("Found a matching question from the history!" + str(sql_example_txt))
            final_sql=exact_sql

        else: 
            print("No exact match found for the user prompt")
            final_sql = None

        return final_sql

    def test_sql_plan_execution(self, generated_sql):
        try:
            exec_result_df=""
            job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            query_job = self.client.query(generated_sql,job_config=job_config)
            # print(query_job)
            exec_result_df=("This query will process {} bytes.".format(query_job.total_bytes_processed))
            correct_sql = True
            print(exec_result_df)
            return correct_sql, exec_result_df
        except Exception as e:
            return False,str(e)


    def return_table_schema_sql(self, dataset, table_names=None): 
        """
        Returns the SQL query to be run on 'Source DB' to get the Table Schema
        The SQL query below returns a df containing the cols table_schema, table_name, table_description, table_columns (with cols in the table)
        for the schema specified above, e.g. 'retail'
        - table_schema: e.g. retail 
        - table_name: name of the table inside the schema, e.g. products 
        - table_description: text descriptor, can be empty 
        - table_columns: aggregate of the col names inside the table 
        """

        user_dataset = self.project_id + '.' + dataset

        table_filter_clause = ""

        if table_names:
            # Extract individual table names from the input string
            #table_names = [name.strip() for name in table_names[1:-1].split(",")]  # Handle the string as a list
            formatted_table_names = [f"'{name}'" for name in table_names]
            table_filter_clause = f"""AND TABLE_NAME IN ({', '.join(formatted_table_names)})"""


        table_schema_sql = f"""
        (SELECT
            TABLE_CATALOG as project_id, TABLE_SCHEMA as table_schema , TABLE_NAME as table_name,  OPTION_VALUE as table_description,
            (SELECT STRING_AGG(column_name, ', ') from `{user_dataset}.INFORMATION_SCHEMA.COLUMNS` where TABLE_NAME= t.TABLE_NAME and TABLE_SCHEMA=t.TABLE_SCHEMA) as table_columns
        FROM
            `{user_dataset}.INFORMATION_SCHEMA.TABLE_OPTIONS` as t
        WHERE
            OPTION_NAME = "description"
            {table_filter_clause}
        ORDER BY
            project_id, table_schema, table_name)

        UNION ALL

        (SELECT
            TABLE_CATALOG as project_id, TABLE_SCHEMA as table_schema , TABLE_NAME as table_name,  "NA" as table_description,
            (SELECT STRING_AGG(column_name, ', ') from `{user_dataset}.INFORMATION_SCHEMA.COLUMNS` where TABLE_NAME= t.TABLE_NAME and TABLE_SCHEMA=t.TABLE_SCHEMA) as table_columns
        FROM
            `{user_dataset}.INFORMATION_SCHEMA.TABLES` as t 
        WHERE 
            NOT EXISTS (SELECT 1   FROM
            `{user_dataset}.INFORMATION_SCHEMA.TABLE_OPTIONS`  
        WHERE
            OPTION_NAME = "description" AND  TABLE_NAME= t.TABLE_NAME and TABLE_SCHEMA=t.TABLE_SCHEMA)
            {table_filter_clause}
        ORDER BY
            project_id, table_schema, table_name)
        """
        return table_schema_sql
    


    def return_column_schema_sql(self, dataset, table_names=None): 
        """
        Returns the SQL query to be run on 'Source DB' to get the column schema 
         
        The SQL query below returns a df containing the cols table_schema, table_name, column_name, data_type, column_description, table_description, primary_key, column_constraints
        for the schema specified above, e.g. 'retail'
        - table_schema: e.g. retail 
        - table_name: name of the tables inside the schema, e.g. products 
        - column_name: name of each col in each table in the schema, e.g. id_product 
        - data_type: data type of each col 
        - column_description: col descriptor, can be empty 
        - table_description: text descriptor, can be empty 
        - primary_key: whether the col is PK; if yes, the field contains the col_name 
        - column_constraints: e.g. "Primary key for this table"
        """

        user_dataset = self.project_id + '.' + dataset

        table_filter_clause = ""

        if table_names:
            
            # table_names = [name.strip() for name in table_names[1:-1].split(",")]  # Handle the string as a list
            formatted_table_names = [f"'{name}'" for name in table_names]
            table_filter_clause = f"""AND C.TABLE_NAME IN ({', '.join(formatted_table_names)})"""
            
        column_schema_sql = f"""
        SELECT
            C.TABLE_CATALOG as project_id, C.TABLE_SCHEMA as table_schema, C.TABLE_NAME as table_name, C.COLUMN_NAME as column_name,
            C.DATA_TYPE as data_type, C.DESCRIPTION as column_description, CASE WHEN T.CONSTRAINT_TYPE="PRIMARY KEY" THEN "This Column is a Primary Key for this table" WHEN 
            T.CONSTRAINT_TYPE = "FOREIGN_KEY" THEN "This column is Foreign Key" ELSE NULL END as column_constraints
        FROM
            `{user_dataset}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` C 
        LEFT JOIN 
            `{user_dataset}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS` T 
            ON C.TABLE_CATALOG = T.TABLE_CATALOG AND
            C.TABLE_SCHEMA = T.TABLE_SCHEMA AND 
            C.TABLE_NAME = T.TABLE_NAME AND  
            T.ENFORCED ='YES'
        LEFT JOIN 
            `{user_dataset}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE` K
            ON K.CONSTRAINT_NAME=T.CONSTRAINT_NAME AND C.COLUMN_NAME = K.COLUMN_NAME 
        WHERE
            1=1
            {table_filter_clause} 
        ORDER BY
            project_id, table_schema, table_name, column_name;
    """

        return column_schema_sql

    def get_column_samples(self,columns_df):
        sample_column_list=[]

        for index, row in columns_df.iterrows():
            get_column_sample_sql=f'''SELECT STRING_AGG(CAST(value AS STRING)) as sample_values FROM UNNEST((SELECT APPROX_TOP_COUNT(`{row["column_name"]}`,5) as osn 
            FROM `{row["project_id"]}.{row["table_schema"]}.{row["table_name"]}`
            ))'''

            column_samples_df=self.retrieve_df(get_column_sample_sql)
            # display(column_samples_df)
            sample_column_list.append(column_samples_df['sample_values'].to_string(index=False))

        columns_df["sample_values"]=sample_column_list
        return columns_df
