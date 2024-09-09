import asyncio
import asyncpg
import pandas as pd
import numpy as np
from pgvector.asyncpg import register_vector
from google.cloud.sql.connector import Connector
from google.cloud import spanner
from langchain_community.embeddings import VertexAIEmbeddings
from google.cloud import bigquery
from dbconnectors import pgconnector
from agents import EmbedderAgent
from sqlalchemy.sql import text
from utilities import VECTOR_STORE, PROJECT_ID, PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD, PG_REGION, \
    BQ_OPENDATAQNA_DATASET_NAME, BQ_REGION, EMBEDDING_MODEL, SPANNER_INSTANCE, SPANNER_OPENDATAQNA_DATABASE

embedder = EmbedderAgent(EMBEDDING_MODEL)

async def store_schema_embeddings(table_details_embeddings, 
                            tablecolumn_details_embeddings, 
                            project_id,
                            instance_name,
                            database_name,
                            schema,
                            database_user,
                            database_password,
                            region,
                            VECTOR_STORE):
    """ 
    Store the vectorised table and column details in the DB table.
    This code may run for a few minutes.  
    """

    if VECTOR_STORE == "cloudsql-pgvector":
    
        loop = asyncio.get_running_loop()
        async with Connector(loop=loop) as connector:
            # Create connection to Cloud SQL database.
            conn: asyncpg.Connection = await connector.connect_async(
                f"{project_id}:{region}:{instance_name}",  # Cloud SQL instance connection name
                "asyncpg",
                user=f"{database_user}",
                password=f"{database_password}",
                db=f"{database_name}",
            )

            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await register_vector(conn)

            # await conn.execute(f"DROP SCHEMA IF EXISTS {pg_schema} CASCADE")        

            # await conn.execute(f"CREATE SCHEMA {pg_schema}")        

            # await conn.execute("DROP TABLE IF EXISTS table_details_embeddings")
            # Create the `table_details_embeddings` table to store vector embeddings.
            await conn.execute(
                """CREATE TABLE IF NOT EXISTS table_details_embeddings(
                                    source_type VARCHAR(100) NOT NULL,
                                    user_grouping VARCHAR(100) NOT NULL,
                                    table_schema VARCHAR(1024) NOT NULL,
                                    table_name VARCHAR(1024) NOT NULL,
                                    content TEXT,
                                    embedding vector(768))"""
            )

            # Store all the generated embeddings back into the database.
            for index, row in table_details_embeddings.iterrows():
                await conn.execute(
                    f"""
                    MERGE INTO table_details_embeddings AS target
                    USING (SELECT $1::text AS source_type, $2::text AS user_grouping, $3::text AS table_schema, $4::text AS table_name, $5::text AS content, $6::vector AS embedding) AS source
                    ON target.user_grouping = source.user_grouping AND target.table_name = source.table_name
                    WHEN MATCHED THEN 
                        UPDATE SET source_type = source.source_type, table_schema = source.table_schema, content = source.content, embedding = source.embedding
                    WHEN NOT MATCHED THEN
                        INSERT (source_type, user_grouping, table_schema, table_name, content, embedding) 
                        VALUES (source.source_type, source.user_grouping, source.table_schema, source.table_name, source.content, source.embedding);
                    """,
                    row["source_type"],
                    row["user_grouping"],
                    row["table_schema"],
                    row["table_name"],
                    row["content"],
                    np.array(row["embedding"]),
                )

            # await conn.execute("DROP TABLE IF EXISTS tablecolumn_details_embeddings")
            # Create the `table_details_embeddings` table to store vector embeddings.
            await conn.execute(
                """CREATE TABLE IF NOT EXISTS tablecolumn_details_embeddings(
                                    source_type VARCHAR(100) NOT NULL,
                                    user_grouping VARCHAR(100) NOT NULL,
                                    table_schema VARCHAR(1024) NOT NULL,
                                    table_name VARCHAR(1024) NOT NULL,
                                    column_name VARCHAR(1024) NOT NULL,
                                    content TEXT,
                                    embedding vector(768))"""
            )

            # Store all the generated embeddings back into the database.
            for index, row in tablecolumn_details_embeddings.iterrows():
                await conn.execute(
                    f"""
                    MERGE INTO tablecolumn_details_embeddings AS target
                    USING (SELECT $1::text AS source_type, $2::text AS user_grouping, $3::text AS table_schema, 
                                $4::text AS table_name, $5::text AS column_name, $6::text AS content, $7::vector AS embedding) AS source
                    ON target.user_grouping = source.user_grouping 
                    AND target.table_name = source.table_name 
                    AND target.column_name = source.column_name
                    WHEN MATCHED THEN 
                        UPDATE SET source_type = source.source_type, table_schema = source.table_schema, content = source.content, embedding = source.embedding
                    WHEN NOT MATCHED THEN
                        INSERT (source_type, user_grouping, table_schema, table_name, column_name, content, embedding) 
                        VALUES (source.source_type, source.user_grouping, source.table_schema, source.table_name, source.column_name, source.content, source.embedding);
                    """,
                    row["source_type"],
                    row["user_grouping"],
                    row["table_schema"],
                    row["table_name"],
                    row["column_name"],
                    row["content"],
                    np.array(row["embedding"]),
                )
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await register_vector(conn)

            # await conn.execute("DROP TABLE IF EXISTS example_prompt_sql_embeddings")
            await conn.execute(
                        """CREATE TABLE IF NOT EXISTS example_prompt_sql_embeddings(
                                            user_grouping VARCHAR(1024) NOT NULL,
                                            example_user_question text NOT NULL,
                                            example_generated_sql text NOT NULL,
                                            embedding vector(768))"""
                        )

            await conn.close()


    elif VECTOR_STORE == "bigquery-vector": 
         
        client=bigquery.Client(project=project_id)

        #Store table embeddings
        client.query_and_wait(f'''CREATE TABLE IF NOT EXISTS `{project_id}.{schema}.table_details_embeddings` (
            source_type string NOT NULL, user_grouping string NOT NULL, table_schema string NOT NULL, table_name string NOT NULL, content string, embedding ARRAY<FLOAT64>)''')
        #job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

        delete_conditions = table_details_embeddings[['user_grouping', 'table_name']].apply(tuple, axis=1).tolist()
        where_clause = " OR ".join([f"(user_grouping = '{cond[0]}' AND table_name = '{cond[1]}')" for cond in delete_conditions])

        delete_query = f"""
        DELETE FROM `{project_id}.{schema}.table_details_embeddings`
        WHERE {where_clause}
        """
        client.query_and_wait(delete_query)
        
        client.load_table_from_dataframe(table_details_embeddings,f'{project_id}.{schema}.table_details_embeddings')


        #Store column embeddings
        client.query_and_wait(f'''CREATE TABLE IF NOT EXISTS `{project_id}.{schema}.tablecolumn_details_embeddings` (
            source_type string NOT NULL,user_grouping string NOT NULL, table_schema string NOT NULL, table_name string NOT NULL, column_name string NOT NULL,
            content string, embedding ARRAY<FLOAT64>)''')
        #job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

        delete_conditions = tablecolumn_details_embeddings[['user_grouping', 'table_name', 'column_name']].apply(tuple, axis=1).tolist()
        where_clause = " OR ".join([f"(user_grouping = '{cond[0]}' AND table_name = '{cond[1]}' AND column_name = '{cond[2]}')" for cond in delete_conditions])

        delete_query = f"""
            DELETE FROM `{project_id}.{schema}.tablecolumn_details_embeddings`
            WHERE {where_clause}
            """
        client.query_and_wait(delete_query)

        client.load_table_from_dataframe(tablecolumn_details_embeddings,f'{project_id}.{schema}.tablecolumn_details_embeddings')

        client.query_and_wait(f'''CREATE TABLE IF NOT EXISTS `{project_id}.{schema}.example_prompt_sql_embeddings` (
                              user_grouping string NOT NULL, example_user_question string NOT NULL, example_generated_sql string NOT NULL,
                              embedding ARRAY<FLOAT64>)''')

    if VECTOR_STORE == "spanner-vector":

        spanner_client = spanner.Client(project=PROJECT_ID)
        instance = spanner_client.instance(SPANNER_INSTANCE)
        database = instance.database(SPANNER_OPENDATAQNA_DATABASE)

        def create_tables():
            # Create tables using DDL statements
            ddl_statements = [
                """CREATE TABLE IF NOT EXISTS table_details_embeddings (
                    source_type STRING(100) NOT NULL,
                    user_grouping STRING(100) NOT NULL,
                    table_schema STRING(1024) NOT NULL,
                    table_name STRING(1024) NOT NULL,
                    content STRING(MAX),
                    embedding ARRAY<FLOAT64>
                ) PRIMARY KEY (user_grouping, table_name)""",

                """CREATE TABLE IF NOT EXISTS tablecolumn_details_embeddings (
                    source_type STRING(100) NOT NULL,
                    user_grouping STRING(100) NOT NULL,
                    table_schema STRING(1024) NOT NULL,
                    table_name STRING(1024) NOT NULL,
                    column_name STRING(1024) NOT NULL,
                    content STRING(MAX),
                    embedding ARRAY<FLOAT64>
                ) PRIMARY KEY (user_grouping, table_name, column_name)""",

                """CREATE TABLE IF NOT EXISTS example_prompt_sql_embeddings (
                    user_grouping STRING(1024) NOT NULL,
                    example_user_question STRING(MAX) NOT NULL,
                    example_generated_sql STRING(MAX) NOT NULL,
                    embedding ARRAY<FLOAT64>
                ) PRIMARY KEY (user_grouping, example_user_question)"""
            ]

            operation = database.update_ddl(ddl_statements)
            operation.result()  # Wait for the operation to complete

        # Function to convert numpy array to list
        def np_to_list(arr):
            return arr.tolist() if isinstance(arr, np.ndarray) else arr

        def insert_table_details(transaction):
            for _, row in table_details_embeddings.iterrows():
                transaction.insert_or_update(
                    table="table_details_embeddings",
                    columns=("source_type", "user_grouping", "table_schema", "table_name", "content", "embedding"),
                    values=[(
                        row["source_type"],
                        row["user_grouping"],
                        row["table_schema"],
                        row["table_name"],
                        row["content"],
                        np_to_list(row["embedding"])
                    )]
                )

        def insert_column_details(transaction):
            for _, row in tablecolumn_details_embeddings.iterrows():
                transaction.insert_or_update(
                    table="tablecolumn_details_embeddings",
                    columns=("source_type", "user_grouping", "table_schema", "table_name", "column_name", "content",
                             "embedding"),
                    values=[(
                        row["source_type"],
                        row["user_grouping"],
                        row["table_schema"],
                        row["table_name"],
                        row["column_name"],
                        row["content"],
                        np_to_list(row["embedding"])
                    )]
                )

        try:
            create_tables()
            print("Tables created successfully.")

            database.run_in_transaction(insert_table_details)
            print("Table details inserted successfully.")

            database.run_in_transaction(insert_column_details)
            print("Column details inserted successfully.")

            print("Vector store implementation for Spanner completed successfully.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    else: raise ValueError("Please provide a valid Vector Store.")
    return "Embeddings are stored successfully"

async def add_sql_embedding(user_question, generated_sql, database):
        
        
        emb=embedder.create(user_question)

        if VECTOR_STORE == "cloudsql-pgvector":
        #    sql=  f'''MERGE INTO example_prompt_sql_embeddings as tgt
        #    using (SELECT '{user_question}' as example_user_question) as src 
        #    on tgt.example_user_question=src.example_user_question 
        #    when not matched then
        #    insert (table_schema, example_user_question,example_generated_sql,embedding) 
        #    values('{database}','{user_question}','{generated_sql}','{(emb)}')
        #    when matched then update set
        #    table_schema = '{database}',
        #    example_generated_sql = '{generated_sql}',
        #    embedding = '{(emb)}' '''

        # #    print(sql)
        #    conn=pgconnector.pool.connect()
        #    await conn.execute(text(sql))
        #    pgconnector.retrieve_df(sql)
            loop = asyncio.get_running_loop()
            async with Connector(loop=loop) as connector:
                    # Create connection to Cloud SQL database.
                conn: asyncpg.Connection = await connector.connect_async(
                        f"{PROJECT_ID}:{PG_REGION}:{PG_INSTANCE}",  # Cloud SQL instance connection name
                        "asyncpg",
                        user=f"{PG_USER}",
                        password=f"{PG_PASSWORD}",
                        db=f"{PG_DATABASE}",
                    )

                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await register_vector(conn)

                await conn.execute("DELETE FROM example_prompt_sql_embeddings WHERE user_grouping= $1 and example_user_question=$2",
                                    database,
                                    user_question)
                cleaned_sql =generated_sql.replace("\r", " ").replace("\n", " ")
                await conn.execute(
                                "INSERT INTO example_prompt_sql_embeddings (user_grouping, example_user_question, example_generated_sql, embedding) VALUES ($1, $2, $3, $4)",
                                database,
                                user_question,
                                cleaned_sql,
                                np.array(emb),
                            )

        elif VECTOR_STORE == "bigquery-vector":

            client=bigquery.Client(project=PROJECT_ID)
        
            client.query_and_wait(f'''CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.example_prompt_sql_embeddings` (
                user_grouping string NOT NULL, example_user_question string NOT NULL, example_generated_sql string NOT NULL,
                embedding ARRAY<FLOAT64>)''')
            client.query_and_wait(f'''DELETE FROM `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.example_prompt_sql_embeddings`
                                WHERE user_grouping= '{database}' and example_user_question= "{user_question}" '''
                                    )
                        # embedding=np.array(row["embedding"])
            cleaned_sql = generated_sql.replace("\r", " ").replace("\n", " ")
            client.query_and_wait(f'''INSERT INTO `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.example_prompt_sql_embeddings` 
                        VALUES ("{database}","{user_question}" , 
                        "{cleaned_sql}",{emb})''')
        return 1



if __name__ == '__main__': 
    from retrieve_embeddings import retrieve_embeddings
    from utilities import PG_SCHEMA, PROJECT_ID, PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD, PG_REGION
    VECTOR_STORE = "cloudsql-pgvector"
    t, c = retrieve_embeddings(VECTOR_STORE, PG_SCHEMA) 
    asyncio.run(store_schema_embeddings(t, 
                            c, 
                            PROJECT_ID,
                            PG_INSTANCE,
                            PG_DATABASE,
                            PG_SCHEMA,
                            PG_USER,
                            PG_PASSWORD,
                            PG_REGION,
                            VECTOR_STORE = VECTOR_STORE))