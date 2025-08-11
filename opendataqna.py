"""
This script serves as the command-line interface for the Open Data QnA application.
It initializes and runs the main pipeline based on command-line arguments.
"""

import asyncio
import argparse
from pipeline import Pipeline



def main():
    """
    Main function to run the Open Data QnA pipeline from the command line.
    It parses arguments, initializes the pipeline, and prints the results.
    """
    parser = argparse.ArgumentParser(description="Open Data QnA SQL Generation")
    
    # Required arguments
    parser.add_argument("--session_id", type=str, required=True, help="Session Id for the conversation.")
    parser.add_argument("--user_question", type=str, required=True, help="The user's natural language question.")
    parser.add_argument("--user_grouping", type=str, required=True, help="The user grouping (database/schema) to query against.")

    # Optional pipeline behavior arguments
    parser.add_argument("--run_debugger", action="store_true", help="Enable the SQL debugger agent.")
    parser.add_argument("--execute_final_sql", action="store_true", help="Execute the final generated SQL query.")
    parser.add_argument("--debugging_rounds", type=int, default=2, help="Number of debugging rounds.")
    parser.add_argument("--llm_validation", action="store_true", help="Enable LLM-based validation of SQL.")

    # Optional model override arguments
    parser.add_argument("--embedder_model", type=str, help="Override the default embedder model.")
    parser.add_argument("--sqlbuilder_model", type=str, help="Override the default SQL builder model.")
    parser.add_argument("--sqlchecker_model", type=str, help="Override the default SQL checker model.")
    parser.add_argument("--sqldebugger_model", type=str, help="Override the default SQL debugger model.")
    parser.add_argument("--responder_model", type=str, help="Override the default responder model.")

    # Optional similarity search arguments
    parser.add_argument("--num_table_matches", type=int, default=5, help="Number of similar tables to retrieve.")
    parser.add_argument("--num_column_matches", type=int, default=10, help="Number of similar columns to retrieve.")
    parser.add_argument("--num_sql_matches", type=int, default=3, help="Number of similar SQL examples to retrieve.")
    parser.add_argument("--table_similarity_threshold", type=float, default=0.1, help="Threshold for table similarity.")
    parser.add_argument("--column_similarity_threshold", type=float, default=0.1, help="Threshold for column similarity.")
    parser.add_argument("--example_similarity_threshold", type=float, default=0.1, help="Threshold for example similarity.")
    
    args = parser.parse_args()

    # Create a config dict from optional model args to override defaults
    pipeline_config = {
        'sqlbuilder_model': args.sqlbuilder_model,
        'sqlchecker_model': args.sqlchecker_model,
        'sqldebugger_model': args.sqldebugger_model,
        'responder_model': args.responder_model,
        'embedder_model': args.embedder_model,
    }
    # Filter out None values so that only user-provided models override defaults
    pipeline_config = {k: v for k, v in pipeline_config.items() if v is not None}

    # Instantiate the pipeline with potential model overrides
    qna_pipeline = Pipeline(config=pipeline_config)

    # Run the pipeline asynchronously
    final_sql, response, natural_response = asyncio.run(qna_pipeline.run(
        session_id=args.session_id,
        user_question=args.user_question,
        user_grouping=args.user_grouping,
        run_debugger=args.run_debugger,
        execute_final_sql=args.execute_final_sql,
        debugging_rounds=args.debugging_rounds,
        llm_validation=args.llm_validation,
        num_table_matches=args.num_table_matches,
        num_column_matches=args.num_column_matches,
        table_similarity_threshold=args.table_similarity_threshold,
        column_similarity_threshold=args.column_similarity_threshold,
        example_similarity_threshold=args.example_similarity_threshold,
        num_sql_matches=args.num_sql_matches
    ))

    # Print the results
    print("*"*50 + "\nGenerated SQL\n" + "*"*50 + "\n" + str(final_sql))
    print("\n" + "*"*50 + "\nResults\n" + "*"*50)
    print(response)
    print("*"*50 + "\nNatural Response\n" + "*"*50 + "\n" + str(natural_response))

if __name__ == '__main__':
    main()