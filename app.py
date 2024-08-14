import streamlit as st
import pandas as pd
import json
from streamlit.components.v1 import html
from streamlit.logger import get_logger
from opendataqna import  generate_uuid, get_all_databases, run_pipeline, get_kgq
import asyncio

logger = get_logger(__name__)

# Initialize session state variables if they don't exist
if "session_id" not in st.session_state:
    st.session_state.session_id = generate_uuid()
    st.session_state.kgq = []
    st.session_state.user_grouping = None
    logger.info(f"New Session Created  - {st.session_state.session_id}")


def get_known_databases():
    """Retrieves a list of available database schemas from the backend.

    This function fetches a list of database schemas from the backend API.
    These schemas represent the available datasets that users can query.

    Returns:
        list: A list of database schema names.
    """
    logger.info("Getting list of all user databases")
    json_groupings, _ = get_all_databases()
    json_groupings = json.loads(json_groupings)
    groupings = [item["table_schema"] for item in json_groupings if isinstance(item, dict)]
    logger.info(f"user_groupings - {str(groupings)}")
    return groupings

def get_known_sql(selected_schema):
    """Retrieves known good SQL queries (KGQs) for a specific database schema.

    This function fetches a DataFrame containing KGQs for the given schema.
    KGQs are pre-defined SQL queries that can be used as examples or suggestions.

    Args:
        selected_schema (str): The name of the database schema.

    Returns:
        pd.DataFrame: A DataFrame containing KGQs for the specified schema.
    """
    data = get_kgq(selected_schema)
    parsed_data = list(eval(data[0]))
    df = pd.DataFrame(parsed_data)
    return df

def generate_sql_results(selected_schema,user_question):
    """Generates SQL query, executes it, and returns results and response.

    This function orchestrates the process of generating an SQL query based on
    the user's question and selected schema, executing the query, and generating
    a natural language response based on the results.

    Args:
        selected_schema (str): The name of the selected database schema.
        user_question (str): The user's natural language question.

    Returns:
        tuple: A tuple containing the generated SQL query (str), the query results
               as a Pandas DataFrame, and the generated natural language response (str).
    """
    logger.info(f"generating response for user question - {user_question}")
    logger.info(f"selected user groouping - {selected_schema}")
    final_sql, results_df, response = asyncio.run(
            run_pipeline(
                st.session_state.session_id,
                user_question,
                selected_schema,
                RUN_DEBUGGER=True,
                EXECUTE_FINAL_SQL=True,
                DEBUGGING_ROUNDS=2,
                LLM_VALIDATION=False,
                Embedder_model='vertex',  # Options: 'vertex' or 'vertex-lang'
                SQLBuilder_model='gemini-1.5-pro',
                SQLChecker_model='gemini-1.5-pro',
                SQLDebugger_model='gemini-1.5-pro',
                Responder_model='gemini-1.5-pro',
                num_table_matches=5,
                num_column_matches=10,
                table_similarity_threshold=0.1,
                column_similarity_threshold=0.1,
                example_similarity_threshold=0.1,
                num_sql_matches=3
            )
        )
    return(final_sql, results_df, response)

def generate_response(prompt):
    """Generates and displays a response to the user's prompt.

    This function takes a user prompt as input, generates an SQL query and
    response using the `generate_sql_results` function, and displays the
    results in a conversational format using Streamlit's chat message feature.

    Args:
        prompt (str): The user's input prompt.
    """
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "assistant", "content": msg})
    msg = "Generating Response"
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    query, results, response = generate_sql_results(st.session_state.user_grouping, prompt)
    msg = query
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    msg = response
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    with st.chat_message("assistant"): 
        st.dataframe(results)
        st.session_state.messages.append({"role": "assistant", "content": results})

    
st.set_page_config(page_title='Open Data QnA', page_icon="📊", initial_sidebar_state="expanded", layout='wide')
st.markdown("""
        <style>
               .block-container {
                    padding-top: 2rem;
                    padding-bottom: 0rem;
                    padding-left: 2rem;
                    padding-right: 2rem;
                }
        </style>
        """, unsafe_allow_html=True)

st.title("Open Data QnA")

with st.sidebar:
  st.session_state.user_grouping = st.selectbox(
    'Select Table Groupings',
     get_known_databases())
  if st.button("New Query"):
     st.session_state.session_id = generate_uuid()
     st.session_state.messages.clear()
     st.rerun() 
       
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Frequently Asked Questions"}]
if st.session_state.user_grouping is not None:
    df = get_known_sql(st.session_state.user_grouping)
    for index, row in df.iterrows():
      url = text = row["example_user_question"]
      st.session_state.kgq.append(text)

if prompt := st.chat_input():
   generate_response(prompt)
