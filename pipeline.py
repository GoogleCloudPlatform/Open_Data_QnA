"""
This module defines the main pipeline for the Open Data QnA application.
"""
import uuid

from agents import (
    EmbedderAgent,
    BuildSQLAgent,
    DebugSQLAgent,
    ValidateSQLAgent,
    ResponseAgent,
    VisualizeAgent
)
from dbconnectors import BQConnector, PgConnector, FirestoreConnector
from utilities import (
    VECTOR_STORE,
    SQLBUILDER_MODEL,
    SQLCHECKER_MODEL,
    SQLDEBUGGER_MODEL,
    RESPONDER_MODEL,
    EMBEDDER_MODEL,
    PROJECT_ID,
    BQ_OPENDATAQNA_DATASET_NAME,
    EXAMPLES,
    LOGGING,
    USE_SESSION_HISTORY,
    PG_INSTANCE,
    PG_DATABASE,
    PG_USER,
    PG_PASSWORD,
    PG_REGION,
    BQ_REGION,
    BQ_LOG_TABLE_NAME
)


class Pipeline:
    """
    Orchestrates the entire process of converting a natural language question
    to an SQL query, executing it, and generating a response.
    """
    def __init__(self, config: dict = None):
        """
        Initializes the pipeline, loading agents and connectors.
        """
        if config is None:
            config = {}

        # Use model names from config or fall back to defaults from utilities
        self.sqlbuilder_model = config.get('sqlbuilder_model', SQLBUILDER_MODEL)
        self.sqlchecker_model = config.get('sqlchecker_model', SQLCHECKER_MODEL)
        self.sqldebugger_model = config.get('sqldebugger_model', SQLDEBUGGER_MODEL)
        self.responder_model = config.get('responder_model', RESPONDER_MODEL)
        self.embedder_model = config.get('embedder_model', EMBEDDER_MODEL)

        # Load agents
        print("Loading Agents for the pipeline...")
        self.embedder = EmbedderAgent(self.embedder_model)
        self.sql_builder = BuildSQLAgent(self.sqlbuilder_model)
        self.sql_checker = ValidateSQLAgent(self.sqlchecker_model)
        self.sql_debugger = DebugSQLAgent(self.sqldebugger_model)
        self.responder = ResponseAgent(self.responder_model)
        self.visualizer = VisualizeAgent()

        # Instantiate connectors
        self.firestore_connector = FirestoreConnector(PROJECT_ID, "opendataqna-session-logs")
        self.bq_connector = BQConnector(PROJECT_ID, BQ_REGION, BQ_OPENDATAQNA_DATASET_NAME, BQ_LOG_TABLE_NAME)
        self.pg_connector = PgConnector(PROJECT_ID, PG_REGION, PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD)

        # Determine vector connector based on config
        if VECTOR_STORE == 'bigquery-vector':
            self.vector_connector = self.bq_connector
            self.call_await = False
        elif VECTOR_STORE == 'cloudsql-pgvector':
            self.vector_connector = self.pg_connector
            self.call_await = True
        else:
            raise ValueError(
                "Please specify a valid Vector Store in config.ini. "
                "Supported are 'bigquery-vector' or 'cloudsql-pgvector'"
            )

        print("Pipeline initialized successfully.")

    async def run(self, session_id, user_question, user_grouping, run_debugger=True, execute_final_sql=True,
                debugging_rounds=2, llm_validation=False, num_table_matches=5, num_column_matches=10,
                table_similarity_threshold=0.3, column_similarity_threshold=0.3,
                example_similarity_threshold=0.3, num_sql_matches=3, user_id="opendataqna-user@google.com"):
        final_sql, session_id, invalid_response = await self._generate_sql(
            session_id, user_question, user_grouping, run_debugger, debugging_rounds, llm_validation,
            num_table_matches, num_column_matches, table_similarity_threshold,
            column_similarity_threshold, example_similarity_threshold, num_sql_matches, user_id)

        if not invalid_response:
            results_df, invalid_response = self._get_results(
                user_grouping, final_sql, invalid_response=invalid_response,
                EXECUTE_FINAL_SQL=execute_final_sql)

            if not invalid_response:
                _resp, invalid_response = self._get_response(
                    session_id, user_question, results_df.to_json(orient='records'))
            else:
                _resp = results_df
        else:
            results_df = final_sql
            _resp = final_sql

        return final_sql, results_df, _resp

    async def _generate_sql(self, session_id, user_question, user_grouping, run_debugger, debugging_rounds,
                           llm_validation, num_table_matches, num_column_matches,
                           table_similarity_threshold, column_similarity_threshold,
                           example_similarity_threshold, num_sql_matches, user_id):
        try:
            if not session_id:
                print("This is a new session")
                session_id = self._generate_uuid()

            re_written_qe = user_question
            print(f"Getting the history for the session {session_id}...")
            session_history = self.firestore_connector.get_chat_logs_for_session(session_id)
            print(f"Grabbed history for the session: {session_history}")

            if session_history:
                _, re_written_qe = self.sql_builder.rewrite_question(user_question, session_history)
            else:
                print("No records for the session. Not rewriting the question.")

            found_in_vector = 'N'
            final_sql = 'Not Generated Yet'
            process_step = 'Not Started'
            error_msg = ''
            audit_text = ''

            data_source, src_invalid = self._get_source_type(user_grouping)
            if src_invalid:
                raise ValueError(data_source)

            print(f"Source selected: {data_source} for user grouping: {user_grouping}")
            print(f"Vector Store selected: {VECTOR_STORE}")

            audit_text = 'Creating embedding for given question'
            embedded_question = self.embedder.create(re_written_qe)
            audit_text += f"\\nUser Question: {user_question}\\nUser Database: {user_grouping}"
            process_step = "\\n\\nGet Exact Match: "

            exact_sql_history = self.vector_connector.getExactMatches(user_question) if EXAMPLES else None

            if exact_sql_history:
                found_in_vector = 'Y'
                final_sql = exact_sql_history
                invalid_response = False
                audit_text += "\\nExact match has been found! Retrieving from cache."
            else:
                # Continue with similarity search
                similar_sql, table_matches, column_matches = await self._get_similar_matches(
                    user_grouping, embedded_question, num_sql_matches, example_similarity_threshold,
                    num_table_matches, table_similarity_threshold, num_column_matches, column_similarity_threshold
                )

                audit_text += f"\\nRetrieved context: \\nTables: {table_matches}\\nColumns: {column_matches}\\nSQL: {similar_sql}"

                if table_matches.replace('Schema(values):', '').strip() or column_matches.replace('Column name(type):', '').strip():
                    generated_sql = self.sql_builder.build_sql(data_source, user_grouping, user_question, session_history, table_matches, column_matches, similar_sql)
                    final_sql = generated_sql
                    audit_text += f"\\nGenerated SQL: {generated_sql}"

                    if 'unrelated_answer' in generated_sql:
                        invalid_response = True
                        final_sql = "This is an unrelated question or you are not asking a valid query."
                    else:
                        invalid_response = False
                        if run_debugger:
                            connector = self.bq_connector if data_source == 'bigquery' else self.pg_connector
                            final_sql, invalid_response, audit_text = self.sql_debugger.start_debugger(
                                data_source, user_grouping, connector, generated_sql, user_question, self.sql_checker,
                                table_matches, column_matches, audit_text, similar_sql,
                                debugging_rounds, llm_validation)
                        audit_text += f"\\nFinal SQL after Debugger: {final_sql}"
                else:
                    invalid_response = True
                    print('No tables found in Vector DB.')
                    audit_text += "\\nNo tables have been found in the Vector DB."

            if LOGGING:
                self.bq_connector.make_audit_entry(data_source, user_grouping, self.sqlbuilder_model, user_question, final_sql, found_in_vector, "", process_step, error_msg, audit_text)

        except Exception as e:
            error_msg = str(e)
            final_sql = f"Error generating the SQL. Please check the logs: {e}"
            invalid_response = True
            audit_text += "\\nException at SQL generation"
            print(f"Error :: {error_msg}")
            if LOGGING:
                self.bq_connector.make_audit_entry(data_source, user_grouping, self.sqlbuilder_model, user_question, final_sql, found_in_vector, "", process_step, error_msg, audit_text)

        if USE_SESSION_HISTORY and not invalid_response:
            self.firestore_connector.log_chat(session_id, user_question, final_sql, user_id)
            print("Session history persisted.")

        return final_sql, session_id, invalid_response

    async def _get_similar_matches(self, user_grouping, embedded_question, num_sql_matches, example_similarity_threshold,
                                 num_table_matches, table_similarity_threshold, num_column_matches, column_similarity_threshold):
        similar_sql = "No similar SQLs provided..."
        if EXAMPLES:
            if self.call_await:
                similar_sql = await self.vector_connector.getSimilarMatches('example', user_grouping, embedded_question, num_sql_matches, example_similarity_threshold)
            else:
                similar_sql = self.vector_connector.getSimilarMatches('example', user_grouping, embedded_question, num_sql_matches, example_similarity_threshold)

        if self.call_await:
            table_matches = await self.vector_connector.getSimilarMatches('table', user_grouping, embedded_question, num_table_matches, table_similarity_threshold)
            column_matches = await self.vector_connector.getSimilarMatches('column', user_grouping, embedded_question, num_column_matches, column_similarity_threshold)
        else:
            table_matches = self.vector_connector.getSimilarMatches('table', user_grouping, embedded_question, num_table_matches, table_similarity_threshold)
            column_matches = self.vector_connector.getSimilarMatches('column', user_grouping, embedded_question, num_column_matches, column_similarity_threshold)

        return similar_sql, table_matches, column_matches

    def _get_results(self, user_grouping, final_sql, invalid_response=False, EXECUTE_FINAL_SQL=True):
        try:
            data_source, src_invalid = self._get_source_type(user_grouping)
            if src_invalid:
                raise ValueError(data_source)

            src_connector = self.bq_connector if data_source == 'bigquery' else self.pg_connector

            if not invalid_response:
                if EXECUTE_FINAL_SQL:
                    result_df = src_connector.retrieve_df(final_sql.replace("```sql", "").replace("```", "").replace("EXPLAIN ANALYZE ", ""))
                else:
                    print("Not executing final SQL since EXECUTE_FINAL_SQL is False.")
                    result_df = "Execution of the final SQL is disabled."
                    invalid_response = True
            else:
                result_df = "Not executing final SQL as it is invalid."

        except Exception as e:
            print(f"An error occurred while getting results: {e}")
            result_df = f"Error has been encountered: {e}"
            invalid_response = True

        return result_df, invalid_response

    def _get_response(self, session_id, user_question, result_df):
        try:
            if session_id:
                session_history = self.firestore_connector.get_chat_logs_for_session(session_id)
                if session_history:
                    _, user_question = self.responder.rewrite_question(user_question, session_history)

            _resp = self.responder.run(user_question, result_df)
            invalid_response = False
        except Exception as e:
            print(f"An error occurred while generating response: {e}")
            _resp = f"Error has been encountered: {e}"
            invalid_response = True

        return _resp, invalid_response

    def _get_source_type(self, user_grouping):
        try:
            if VECTOR_STORE == 'bigquery-vector':
                sql = f"SELECT DISTINCT source_type FROM `{PROJECT_ID}.{BQ_OPENDATAQNA_DATASET_NAME}.table_details_embeddings` WHERE user_grouping='{user_grouping}'"
            else:
                sql = f"SELECT DISTINCT source_type FROM table_details_embeddings WHERE user_grouping='{user_grouping}'"

            result = self.vector_connector.retrieve_df(sql)
            result = str(result.iloc[0, 0]).lower()
            invalid_response = False
        except Exception as e:
            result = f"Error finding the data source: {e}"
            invalid_response = True
        return result, invalid_response

    def _generate_uuid(self):
        return str(uuid.uuid4())
