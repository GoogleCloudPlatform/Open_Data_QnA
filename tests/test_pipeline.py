"""
Tests for the main pipeline.
"""

import pytest
from pipeline import Pipeline

def test_pipeline_initialization(mocker):
    """
    Tests that the Pipeline class can be initialized successfully.
    Mocks all external dependencies to isolate the test to the constructor logic.
    """
    # Mock the agent classes
    mocker.patch('pipeline.EmbedderAgent')
    mocker.patch('pipeline.BuildSQLAgent')
    mocker.patch('pipeline.ValidateSQLAgent')
    mocker.patch('pipeline.DebugSQLAgent')
    mocker.patch('pipeline.ResponseAgent')
    mocker.patch('pipeline.VisualizeAgent')

    # Mock the connector classes
    mocker.patch('pipeline.FirestoreConnector')
    mocker.patch('pipeline.BQConnector')
    mocker.patch('pipeline.PgConnector')

    # Mock the config values imported from utilities
    mocker.patch('pipeline.VECTOR_STORE', 'bigquery-vector')
    mocker.patch('pipeline.SQLBUILDER_MODEL', 'gemini-1.5-pro')
    mocker.patch('pipeline.SQLCHECKER_MODEL', 'gemini-1.0-pro')
    mocker.patch('pipeline.SQLDEBUGGER_MODEL', 'gemini-1.0-pro')
    mocker.patch('pipeline.RESPONDER_MODEL', 'gemini-1.0-pro')
    mocker.patch('pipeline.EMBEDDER_MODEL', 'vertex')
    mocker.patch('pipeline.PROJECT_ID', 'test-project')
    mocker.patch('pipeline.BQ_OPENDATAQNA_DATASET_NAME', 'test_dataset')
    mocker.patch('pipeline.EXAMPLES', True)
    mocker.patch('pipeline.LOGGING', False)
    mocker.patch('pipeline.USE_SESSION_HISTORY', False)

    try:
        # Create an instance of the pipeline
        pipeline = Pipeline()
        # Assert that the pipeline object was created
        assert pipeline is not None
        print("Pipeline initialized successfully in test.")
    except Exception as e:
        pytest.fail(f"Pipeline initialization raised an unexpected exception: {e}")


@pytest.mark.asyncio
async def test_pipeline_run_happy_path(mocker):
    """
    Tests the main run method of the Pipeline class on a happy path.
    """
    # Mock all external dependencies
    mocker.patch('pipeline.EmbedderAgent')
    mocker.patch('pipeline.BuildSQLAgent')
    mocker.patch('pipeline.ValidateSQLAgent')
    mocker.patch('pipeline.DebugSQLAgent')
    mocker.patch('pipeline.ResponseAgent')
    mocker.patch('pipeline.VisualizeAgent')
    mocker.patch('pipeline.FirestoreConnector')
    mocker.patch('pipeline.BQConnector')
    mocker.patch('pipeline.PgConnector')
    mocker.patch('pipeline.VECTOR_STORE', 'bigquery-vector')
    mocker.patch('pipeline.SQLBUILDER_MODEL', 'gemini-1.5-pro')
    mocker.patch('pipeline.SQLCHECKER_MODEL', 'gemini-1.0-pro')
    mocker.patch('pipeline.SQLDEBUGGER_MODEL', 'gemini-1.0-pro')
    mocker.patch('pipeline.RESPONDER_MODEL', 'gemini-1.0-pro')
    mocker.patch('pipeline.EMBEDDER_MODEL', 'vertex')
    mocker.patch('pipeline.PROJECT_ID', 'test-project')
    mocker.patch('pipeline.BQ_OPENDATAQNA_DATASET_NAME', 'test_dataset')
    mocker.patch('pipeline.EXAMPLES', True)
    mocker.patch('pipeline.LOGGING', False)
    mocker.patch('pipeline.USE_SESSION_HISTORY', False)

    # Instantiate the pipeline
    pipeline = Pipeline()

    # Configure mocks to simulate a successful run
    mocker.patch.object(pipeline.firestore_connector, 'get_chat_logs_for_session', return_value=[])
    mocker.patch.object(pipeline.vector_connector, 'getExactMatches', return_value=None)
    mocker.patch.object(pipeline.vector_connector, 'getSimilarMatches', return_value="some_schema")
    mocker.patch.object(pipeline.sql_builder, 'build_sql', return_value='SELECT * FROM test_table;')
    mocker.patch.object(pipeline.sql_debugger, 'start_debugger', return_value=('SELECT * FROM test_table;', False, ''))
    mocker.patch.object(pipeline.bq_connector, 'retrieve_df', return_value=mocker.MagicMock())
    mocker.patch.object(pipeline.responder, 'run', return_value="Here are the results.")
    mocker.patch.object(pipeline, '_get_source_type', return_value=('bigquery', False))


    # Call the run method
    final_sql, _, _ = await pipeline.run(
        session_id="test_session",
        user_question="test question",
        user_grouping="test_grouping"
    )

    # Assert that the final SQL is what we expect
    assert final_sql == 'SELECT * FROM test_table;'
