"""
Google Cloud Spanner Connector Class
"""
from google.cloud import spanner
from google.cloud.spanner_v1 import param_types, ExecuteSqlRequest

import pandas as pd
from dbconnectors import DBConnector
from abc import ABC
from typing import List, Tuple, Optional


def spanner_specific_data_types():
    return '''
    Google Cloud Spanner offers a variety of data types to store different types of data effectively. Here's a breakdown of the available categories:

    Numeric Types:
    INT64: 64-bit signed integer.
    FLOAT64: 64-bit IEEE 754 floating point number.
    NUMERIC: Exact numeric value with 38 digits of precision and 9 decimal digits.

    String Types:
    STRING(n): Variable-length character string with a maximum length of n characters. If n is not specified, it defaults to MAX.
    BYTES(n): Variable-length binary string with a maximum length of n bytes. If n is not specified, it defaults to MAX.

    Boolean Type:
    BOOL: Represents TRUE or FALSE.

    Date and Time Types:
    DATE: Calendar date (year, month, day).
    TIMESTAMP: Absolute point in time with microsecond precision.

    Array Type:
    ARRAY: Ordered list of zero or more elements of any non-ARRAY type.

    Struct Type:
    STRUCT: Container of ordered fields each with a type (except STRUCT) and field name.

    This list covers the most common data types in Google Cloud Spanner.
    '''


class SpannerConnector(DBConnector, ABC):
    """
    A connector class for interacting with Google Cloud Spanner databases.

    This class provides methods for establishing connections to Spanner instances, executing SQL queries,
    retrieving results as DataFrames, and managing database operations.

    Attributes:
        project_id (str): The Google Cloud project ID where the Spanner instance resides.
        instance_id (str): The ID of the Spanner instance.
        database_id (str): The ID of the database to connect to.
        client (spanner.Client): The Spanner client instance for executing queries.

    Methods:
        getconn() -> spanner.Client:
            Establishes a connection to the Spanner instance and returns a client object.

        retrieve_df(query: str, params: Optional[dict] = None) -> pd.DataFrame:
            Executes a SQL query and returns the results as a pandas DataFrame.

        execute_dml(dml_statements: List[str]) -> int:
            Executes a list of DML statements in a single transaction.

        test_sql_plan_execution(generated_sql: str) -> Tuple[bool, str]:
            Tests the execution plan of a generated SQL query in Spanner.

        return_table_schema_sql(schema: str, table_names: Optional[List[str]] = None) -> str:
            Returns a SQL query to retrieve table schema information from a Spanner database.

        return_column_schema_sql(schema: str, table_names: Optional[List[str]] = None) -> str:
            Returns a SQL query to retrieve column schema information from a Spanner database.

        get_column_samples(columns_df: pd.DataFrame) -> pd.DataFrame:
            Retrieves sample values for columns in the given DataFrame.
    """

    def __init__(self, project_id: str, instance_id: str, opendataqna_database_id: str):
        self.project_id = project_id
        self.instance_id = instance_id
        self.opendataqna_database_id = opendataqna_database_id
        self.client = self.getconn()

    def getconn(self) -> spanner.Client:
        """
        Establishes a connection to the Spanner instance and returns a client object.
        """
        return spanner.Client(project=self.project_id)

    def retrieve_df(self, query: str, database_id: str = None, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Executes a SQL query and returns the results as a pandas DataFrame.
        """
        instance = self.client.instance(self.instance_id)
        database = instance.database(self.opendataqna_database_id if database_id is None else database_id)

        with database.snapshot() as snapshot:
            # print(query)
            if params:
                result = snapshot.execute_sql(query, params=params)
            else:
                result = snapshot.execute_sql(query)

            rows = [list(row) for row in result]
            columns = [field.name for field in result.fields]
            return pd.DataFrame(rows, columns=columns)

    def execute_dml(self, dml_statements: List[str], database_id: str = None) -> int:
        """
        Executes a list of DML statements in a single transaction.
        Returns the number of rows affected.
        """
        instance = self.client.instance(self.instance_id)
        database = instance.database(self.opendataqna_database_id if database_id is None else database_id)

        def update_database(transaction):
            row_counts = []
            for sql in dml_statements:
                row_count = transaction.execute_update(sql)
                row_counts.append(row_count)
            return row_counts

        row_counts = database.run_in_transaction(update_database)
        return sum(row_counts)

    def test_sql_plan_execution(self, generated_sql: str, database_id: str = None) -> Tuple[bool, str]:
        """
        Tests the execution plan of a generated SQL query in Spanner.
        Returns a tuple indicating success and the execution plan or error message.
        """
        try:
            instance = self.client.instance(self.instance_id)
            database = instance.database(self.opendataqna_database_id if database_id is None else database_id)

            with database.snapshot() as snapshot:
                result = snapshot.execute_sql(
                    generated_sql,
                    params=None,
                    param_types=None,
                    query_mode=ExecuteSqlRequest.QueryMode.PLAN
                )

                return True, str(result.stats)

        except Exception as e:
            return False, str(e)

    def return_table_schema_sql(self, database_id: str, table_names: Optional[List[str]] = None) -> str:
        """
        Returns a SQL query to retrieve table schema information from a Spanner database,
        including foreign key relationships.
        """
        table_filter = ""
        if table_names:
            formatted_table_names = ", ".join(f"'{name}'" for name in table_names)
            table_filter = f"IN ({formatted_table_names})"

        foreign_key_table_filter = f"AND tc.table_name {table_filter}" if table_filter else ""
        main_query_table_filter = f"AND t.table_name {table_filter}" if table_filter else ""

        return f"""
        WITH foreign_keys AS (
            SELECT
                tc.table_name,
                STRING_AGG(CONCAT(
                    kcu.column_name,
                    ' REFERENCES ',
                    ccu.table_name,
                    '(',
                    ccu.column_name,
                    ')'
                ), ', ') AS foreign_key_info
            FROM
                INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON
                tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN
                INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON
                ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE
                tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = ''
                {foreign_key_table_filter}
            GROUP BY
                tc.table_name
        )
        SELECT
            t.table_catalog AS project_id,
            '{database_id}' AS table_schema,
            t.table_name,
            'NA' AS table_description,
            STRING_AGG(c.column_name, ', ') AS table_columns,
            COALESCE(fk.foreign_key_info, 'No foreign keys') AS foreign_key_info
        FROM
            information_schema.tables t
        JOIN
            information_schema.columns c
        ON
            t.table_catalog = c.table_catalog
            AND t.table_schema = c.table_schema
            AND t.table_name = c.table_name
        LEFT JOIN
            foreign_keys fk
        ON
            t.table_name = fk.table_name
        WHERE
            t.table_schema = ''
            {main_query_table_filter}
        GROUP BY
            t.table_catalog,
            t.table_schema,
            t.table_name,
            t.table_type,
            fk.foreign_key_info
        ORDER BY
            t.table_name;
        """

    def return_column_schema_sql(self, database_id: str, table_names: Optional[List[str]] = None) -> str:
        """
        Returns a SQL query to retrieve column schema information from a Spanner database,
        including foreign key relationships and primary key information.
        """
        table_filter = ""
        if table_names:
            formatted_table_names = ", ".join(f"'{name}'" for name in table_names)
            table_filter = f"IN ({formatted_table_names})"

        foreign_key_table_filter = f"AND tc.table_name {table_filter}" if table_filter else ""
        main_query_table_filter = f"AND t.table_name {table_filter}" if table_filter else ""

        return f"""
        WITH foreign_keys AS (
            SELECT
                tc.table_name,
                kcu.column_name,
                CONCAT(
                    'REFERENCES ',
                    ccu.table_name,
                    '(',
                    ccu.column_name,
                    ')'
                ) AS reference_info
            FROM
                INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON
                tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN
                INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON
                ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE
                tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = ''
                {foreign_key_table_filter}
        )
        SELECT
            c.table_catalog AS project_id,
            '{database_id}' AS table_schema,
            c.table_name,
            c.column_name,
            c.spanner_type AS data_type,
            c.is_nullable,
            c.column_default,
            '' AS column_description,
            c.generation_expression,
            CASE
                WHEN c.is_nullable = 'NO' AND kcu.column_name IS NOT NULL THEN 'PRIMARY KEY'
                WHEN fk.reference_info IS NOT NULL THEN CONCAT('FOREIGN KEY ', fk.reference_info)
                WHEN c.is_nullable = 'NO' THEN 'NOT NULL'
                ELSE NULL
            END AS column_constraints
        FROM
            information_schema.columns c
        LEFT JOIN
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        ON
            c.table_schema = kcu.table_schema
            AND c.table_name = kcu.table_name
            AND c.column_name = kcu.column_name
            AND kcu.constraint_name LIKE '%_pkey'
        LEFT JOIN
            foreign_keys fk
        ON
            c.table_name = fk.table_name
            AND c.column_name = fk.column_name
        WHERE
            c.table_schema = ''
            {main_query_table_filter}
        ORDER BY
            c.table_name,
            c.ordinal_position;
        """

    def get_column_samples(self, columns_df: pd.DataFrame, database_id: str) -> pd.DataFrame:
        """
        Retrieves sample values for columns in the given DataFrame.
        """
        sample_column_list = []

        for _, row in columns_df.iterrows():
            sample_query = f"""
            SELECT {row['column_name']} AS sample_values
            FROM `{row['table_name']}`
            TABLESAMPLE BERNOULLI (80 PERCENT)
            LIMIT 5
            """

            sample_df = self.retrieve_df(sample_query, database_id)
            sample_values = ', '.join(map(str, sample_df['sample_values'].tolist()))
            sample_column_list.append(sample_values)

        columns_df["sample_values"] = sample_column_list
        return columns_df

    def getExactMatches(self, query: str) -> Optional[str]:
        """
        Checks if the exact question is already present in the example SQL set.

        Args:
            query (str): The user's question to check for an exact match.

        Returns:
            Optional[str]: The corresponding SQL if an exact match is found, None otherwise.
        """
        check_history_sql = """
        SELECT example_user_question, example_generated_sql
        FROM example_prompt_sql_embeddings
        WHERE LOWER(example_user_question) = LOWER(@query)
        LIMIT 1
        """

        instance = self.client.instance(self.instance_id)
        database = instance.database(self.opendataqna_database_id)

        with database.snapshot() as snapshot:
            params = {'query': query}
            param_types = {'query': spanner.param_types.STRING}

            results = snapshot.execute_sql(
                check_history_sql,
                params=params,
                param_types=param_types
            )

            for row in results:
                example_user_question, example_sql = row
                print(f"Found a matching question from the history!")
                print(f"Example_question: {example_user_question}")
                print(f"Example_SQL: {example_sql}")
                return example_sql

        print("No exact match found for the user prompt")
        return None

    def getSimilarMatches(self, mode: str, user_grouping: str, qe: List[float], num_matches: int,
                          similarity_threshold: float) -> Optional[str]:
        if mode == 'table':
            table_name = 'table_details_embeddings'
            content_column = 'content'
        elif mode == 'column':
            table_name = 'tablecolumn_details_embeddings'
            content_column = 'content'
        elif mode == 'example':
            table_name = 'example_prompt_sql_embeddings'
            content_column = 'example_user_question'
        else:
            raise ValueError("Invalid mode. Must be 'table', 'column', or 'example'.")

        query = f"""
        SELECT *,
               1 - EUCLIDEAN_DISTANCE(embedding, @query_embedding) AS similarity
        FROM {table_name}
        WHERE user_grouping = @user_grouping
        ORDER BY EUCLIDEAN_DISTANCE(embedding, @query_embedding)
        LIMIT @num_matches
        """

        params = {
            'user_grouping': user_grouping,
            'query_embedding': qe,
            'num_matches': num_matches
        }
        param_types = {
            'user_grouping': spanner.param_types.STRING,
            'query_embedding': spanner.param_types.Array(spanner.param_types.FLOAT64),
            'num_matches': spanner.param_types.INT64
        }

        with self.client.instance(self.instance_id).database(self.opendataqna_database_id).snapshot() as snapshot:
            result = snapshot.execute_sql(query, params=params, param_types=param_types)
            data = [list(row) for row in result]
            columns = [field.name for field in result.fields]
            df = pd.DataFrame(data, columns=columns)

        if df.empty:
            print(f"Did not find any results for {mode}. Adjust the query parameters.")
            return None

        print(f"Found {len(df)} similarity matches for {mode}.")

        if mode in ['table', 'column']:
            return df[content_column].str.cat(sep="\n\n")
        elif mode == 'example':
            result = ""
            for _, row in df.iterrows():
                result += f"\nExample_question: {row['example_user_question']}; Example_SQL: {row['example_generated_sql']}"
            return result
