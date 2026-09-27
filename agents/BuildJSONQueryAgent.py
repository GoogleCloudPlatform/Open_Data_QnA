from abc import ABC
# Assume .core and other necessary imports are available
from .core import Agent, LLM_Model
from typing import Dict, Any, List

# Placeholder for actual RAG context/schema descriptions that will be passed in.
# In a real scenario, these would be dynamically retrieved and formatted.
EXAMPLE_JSON_SCHEMA_DESC = """
JSON Schema Description (from patient_json_schema.json):
- Top-level keys: patient_email_original, total_conversations, conversations, last_updated_iso, patient_preferences.
  - 'patient_email_original' (string): The original email address of the patient...
  - 'conversations' (array of objects): List of conversation threads.
    - Each conversation object includes keys like: conversation_id, start_date_iso, total_messages, participants, messages, tags...
      - 'messages' (array of objects): List of messages within the conversation.
        - Each message object includes keys like: message_id, sender, recipients_to, date_iso, subject, body, direction, attachments, read_status...
          - 'message_id' (string): Unique identifier for a single message.
          - 'date_iso' (string date-time): ISO formatted date and time the message was sent.
          - 'subject' (string): Subject line of the message.
          - 'body' (string): Main content/body of the message.
          - 'sender' (string email): Email address of the message sender. (Note: Use 'direction' to determine if patient is sender for their own emails)
          - 'recipients_to' (array of string email): List of email addresses of direct recipients.
          - 'attachments' (array of objects): List of attachments in the message. Each attachment object has keys: filename, size_kb, filepath_gcs
          - 'direction' (string enum: ['inbound', 'outbound']): Direction of the message relative to the patient (e.g., 'inbound' to patient from clinic, 'outbound' from patient to clinic).
"""

EXAMPLE_ALL_EMAIL_CORPUS_CSV_SCHEMA_DESC = """
Schema Description for 'all_email_corpus.csv' (from csv_schema.txt):
Columns:
- turn_id: Unique ID for each message turn.
- patient_email: The email of the patient for this message.
- conversation_id: ID for the conversation thread.
- message_content: Text body of the email.
... (other columns like sentiment, topic, intent)
This CSV can be used to find patient_emails related to broad topics/intents if no specific patient is in the user's query.
"""

EXAMPLE_MASTER_PATIENT_LINKS_CSV_SCHEMA_DESC = """
Schema Description for 'master_patient_json_links.csv' (from master_csv_schema.txt):
Columns:
- "Patient Email": Primary email of the patient.
- "JSON File Path (Relative to Output Root)": Relative path to the patient's JSON data file.
This CSV maps a patient_email to their specific JSON data file.
The filename in "JSON File Path (Relative to Output Root)" is the ground truth for the file path.
Example: patient_email 'aaronmeers73@gmail.com' might map to 'JSON File Path' like 'batch_001/aaronmeers73_at_gmail_com.json'.
"""

EXAMPLE_JSON_FILENAMES_LIST_DESC = """
Summary of JSON Data Filenames (from json_filenames.txt):
The system accesses patient-specific data stored in JSON files. Examples:
- batch_001_aaronmeers73_at_gmail_com.json
- batch_002_another_email_at_example_com.json
These filenames are derived from patient emails. The definitive mapping is in master_patient_json_links.csv.
The root directory for these JSON files is assumed to be './all_patient_jsons_with_prefix/'. (LLM should use this as base path)
"""

class BuildJSONQueryAgent(Agent, ABC):
    """
    Agent specialized in generating Python code to query JSON files based on natural language.
    It leverages an LLM and contextual schema information.
    """
    agentType: str = "BuildJSONQueryAgent"

    def __init__(self, llm_model: LLM_Model, model_name="gemini-1.0-pro", **kwargs):
        super().__init__(llm_model, model_name, **kwargs)
        # self.llm_model is inherited from Agent class and initialized by super()

    # This is the new system prompt for Python code generation.
    # It will be formatted with specific context before being sent to the LLM.
    PYTHON_GENERATION_SYSTEM_PROMPT_TEMPLATE = """
You are an expert Python programming assistant. Your task is to generate Python code to answer a user's question by querying patient data stored in JSON files.
You must adhere to the following instructions and use the provided schemas and context.

**1. Understand the Goal:**
The user will ask a question in natural language. You need to generate a Python script that, when executed, will:
    a. Identify the relevant patient(s) and their JSON data file(s).
    b. Load and parse the JSON data.
    c. Traverse the JSON structure to find the information needed to answer the question.
    d. Filter, sort, and aggregate data as required by the question.
    e. Prepare the final answer as a Python list of dictionaries, a single dictionary, or a primitive value.
    f. The generated Python code should be a single block, containing all necessary imports and a primary function that performs the query. This function should be callable and return the result. Do not include code to execute the function or print the result within the generated block.

**2. Available Data and Schemas:**

    **a. Patient JSON Data Structure:**
    This is the primary data source. Each patient has one JSON file.
    Base path for JSON files: './all_patient_jsons_with_prefix/'
    Schema:
    ```
    {json_schema_description}
    ```

    **b. Master Patient JSON Links CSV (`master_patient_json_links.csv`):**
    This CSV file maps patient emails to their specific JSON file paths.
    Schema:
    ```
    {master_csv_schema_description}
    ```
    Your generated Python code MUST use this CSV to determine the correct JSON file path for a given patient_email.
    Example of reading and using this CSV in Python:
    ```python
    import pandas as pd
    master_df = pd.read_csv('master_patient_json_links.csv')
    # Assuming patient_email_to_find is known
    # Ensure correct column name is used for lookup as per schema description
    file_path_series = master_df[master_df['Patient Email'] == patient_email_to_find]['JSON File Path (Relative to Output Root)']
    if not file_path_series.empty:
        relative_json_path = file_path_series.iloc[0]
        # Construct full path if needed, e.g., base_path + relative_json_path
    ```

    **c. All Email Corpus CSV (`all_email_corpus.csv`):**
    This CSV contains individual email messages and can be used if the question is general and doesn't specify a patient.
    For example, to find which patients discussed a certain topic, you might query this CSV first to get relevant 'patient_email' values.
    Schema:
    ```
    {all_email_corpus_csv_schema_description}
    ```

    **d. Example JSON Filenames (for context on naming conventions, but prefer `master_patient_json_links.csv` for lookup):**
    ```
    {json_filenames_list_description}
    ```

**3. Python Code Generation Guidelines:**

    *   **Imports:** Include necessary imports (e.g., `json`, `pandas` if using CSVs, `datetime` for date comparisons).
    *   **Main Function:** Define a primary function (e.g., `query_data_for_question()`) that takes no arguments and returns the result.
    *   **File Handling:**
        *   Use `with open(...)` for reading files.
        *   Handle potential `FileNotFoundError` and other relevant exceptions gracefully. If a file for a specific patient is not found, return an informative error message string.
        *   JSON file paths are constructed by prepending the base path './all_patient_jsons_with_prefix/' to the path found in `master_patient_json_links.csv`.
    *   **Data Extraction:**
        *   Access JSON fields safely using `.get()` for dictionaries to avoid `KeyError`, especially for optional fields.
        *   Iterate through lists (like `conversations` and `messages`) carefully.
    *   **Filtering:** Apply filters based on dates, keywords, senders, direction, etc., as per the user's question. For date comparisons, ensure you parse ISO date strings into datetime objects.
    *   **Return Value:** The function should `return` the extracted data. Do NOT use `print()` for the final result within the generated function. The result should be a Python list of dictionaries, a single dictionary, or a primitive value.
    *   **No Direct Execution:** Do not include code that calls the main function (e.g., `result = query_data_for_question()`, `print(result)`). Only define the function and necessary helper functions if any.
    *   **Self-Contained:** The generated code block should be executable on its own given the presence of the data files.

**4. Example Scenario:**

    *User Question:* "What were the subjects of the last 2 emails from 'aaronmeers73@gmail.com' where the patient was the sender?"

    *Conceptual Python Code (This is an example of what you should generate. Your code will be more complete based on the full schemas):*
    ```python
    import json
    import pandas as pd
    from datetime import datetime

    def query_data_for_question():
        patient_email_to_find = "aaronmeers73@gmail.com"
        json_base_path = "./all_patient_jsons_with_prefix/" # Make sure to use this

        # 1. Find JSON file path from master_patient_json_links.csv
        try:
            master_df = pd.read_csv("master_patient_json_links.csv")
            # Use the exact column name as specified in its schema description for lookup
            file_path_series = master_df[master_df["Patient Email"] == patient_email_to_find]["JSON File Path (Relative to Output Root)"]

            if file_path_series.empty:
                return f"Error: Patient email {patient_email_to_find} not found in master_patient_json_links.csv."

            relative_json_path = file_path_series.iloc[0]
            json_file_path = json_base_path + relative_json_path # Construct full path

        except FileNotFoundError:
            return "Error: master_patient_json_links.csv not found."
        except Exception as e:
            return f"Error reading master_patient_json_links.csv: {str(e)}"

        # 2. Load and process the patient's JSON data
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            return f"Error: JSON file not found at {json_file_path}."
        except json.JSONDecodeError:
            return f"Error: Could not decode JSON from {json_file_path}."
        except Exception as e:
            return f"Error reading or processing JSON file {json_file_path}: {str(e)}"

        patient_sent_messages = []
        for conv in data.get("conversations", []):
            for msg in conv.get("messages", []):
                # Check direction: 'outbound' means patient sent it to clinic/provider
                # Or check if msg.get('sender') == data.get('patient_email_original')
                # The exact logic depends on how 'sender' and 'direction' are used in the JSON schema.
                # Let's assume 'direction' == 'outbound' means patient is sender.
                if msg.get("direction") == "outbound": # or msg.get("sender") == patient_email_to_find
                    patient_sent_messages.append({
                        "subject": msg.get("subject"),
                        "date_iso": msg.get("date_iso"),
                        "body": msg.get("body") # Example: also extract body
                    })

        if not patient_sent_messages:
            return f"No messages found where patient {patient_email_to_find} was the sender."

        # Sort messages by date (descending) to get the latest ones
        patient_sent_messages.sort(key=lambda x: datetime.fromisoformat(x["date_iso"].replace("Z", "+00:00")), reverse=True)

        # Get subjects of the last 2 emails
        last_2_subjects = [msg["subject"] for msg in patient_sent_messages[:2]]

        return last_2_subjects

    # END OF GENERATED CODE BLOCK
    ```

**5. User's Question:**
```
{user_question}
```

Now, generate the Python code as a single block. Ensure it is complete and follows all guidelines.
"""

    def _prepare_llm_prompt(self,
                            user_question: str,
                            json_schema_desc: str,
                            all_email_corpus_csv_schema_desc: str,
                            master_csv_schema_desc: str,
                            json_filenames_list_desc: str) -> str:
        """
        Formats the system prompt with the specific user question and schema descriptions.
        """
        return self.PYTHON_GENERATION_SYSTEM_PROMPT_TEMPLATE.format(
            user_question=user_question,
            json_schema_description=json_schema_desc,
            all_email_corpus_csv_schema_description=all_email_corpus_csv_schema_desc,
            master_csv_schema_description=master_csv_schema_desc,
            json_filenames_list_description=json_filenames_list_desc
        )

    # Renamed from generate_sql or similar
    async def generate_python_query_code(self,
                                         user_question: str,
                                         # These contexts would be retrieved by RAG in a full system
                                         json_schema_description: str = EXAMPLE_JSON_SCHEMA_DESC,
                                         all_email_corpus_csv_schema_description: str = EXAMPLE_ALL_EMAIL_CORPUS_CSV_SCHEMA_DESC,
                                         master_csv_schema_description: str = EXAMPLE_MASTER_PATIENT_LINKS_CSV_SCHEMA_DESC,
                                         json_filenames_list_description: str = EXAMPLE_JSON_FILENAMES_LIST_DESC,
                                         **kwargs) -> Dict[str, Any]:
        """
        Generates Python code for querying JSON files based on the user's question and provided context.

        Args:
            user_question (str): The natural language question from the user.
            json_schema_description (str): Description of the patient JSON data structure.
            all_email_corpus_csv_schema_description (str): Description of the all_email_corpus.csv schema.
            master_csv_schema_description (str): Description of the master_patient_json_links.csv schema.
            json_filenames_list_description (str): Description/list of example JSON filenames.
            **kwargs: Additional keyword arguments for the LLM.

        Returns:
            Dict[str, Any]: A dictionary containing the generated Python code string
                            (or an error message) and other relevant information.
                            Example: {"python_code": "...", "status": "success"}
        """
        print(f"BuildJSONQueryAgent: Received question: {user_question}")

        # 1. Prepare the full prompt for the LLM
        full_prompt = self._prepare_llm_prompt(
            user_question=user_question,
            json_schema_desc=json_schema_description,
            all_email_corpus_csv_schema_desc=all_email_corpus_csv_schema_description,
            master_csv_schema_desc=master_csv_schema_description,
            json_filenames_list_desc=json_filenames_list_description
        )

        print("BuildJSONQueryAgent: Sending prompt to LLM...")
        # For debugging, can print full_prompt or parts of it
        # print(full_prompt)

        # 2. Call the LLM (inherited method `generate_text_from_chat_async` or `generate_text_async`)
        # Assuming the base Agent class has a method to interact with the LLM model.
        # The exact method might vary based on the LLM_Model implementation.
        # Let's use a generic name for now, assuming it handles the chat/generation.
        try:
            # Use the inherited method for LLM interaction.
            # The 'super().generate_text_from_chat_async' or a similar method
            # from the base Agent class is expected to handle the actual LLM call.
            # This method might take the prompt and other parameters like temperature, max_tokens.
            llm_response = await super().generate_text_from_chat_async(
                prompt=full_prompt,
                # context="Python code generation for JSON querying", # Optional context for the LLM call
                **kwargs # Pass through temperature, max_output_tokens etc.
            )
            # llm_response is expected to be a string containing the Python code.

            # Post-processing: Extract Python code if it's wrapped in markdown ```python ... ```
            generated_code = llm_response
            if "```python" in generated_code:
                generated_code = generated_code.split("```python\n")[1].split("\n```")[0]
            elif "```" in generated_code and generated_code.startswith("```"): # handles case where ``` is present without python
                generated_code = generated_code.split("```\n")[1].split("\n```")[0]


            print("BuildJSONQueryAgent: Received response from LLM.")
            return {
                "python_code": generated_code,
                "status": "success",
                "prompt_sent": full_prompt # For debugging
            }
        except Exception as e:
            print(f"BuildJSONQueryAgent: Error during LLM interaction: {e}")
            return {
                "python_code": None,
                "status": "error",
                "error_message": str(e),
                "prompt_sent": full_prompt # For debugging
            }

# Conceptual main execution for demonstration (if this file were run directly)
# if __name__ == '__main__':
#     import asyncio
#     # This requires a concrete LLM_Model implementation (e.g., for Gemini)
#     # from ..llm_models import GeminiModel  # Example
#     # llm_model_instance = GeminiModel(model_name="gemini-1.0-pro")
#
#     # Create a dummy LLM model for testing structure
#     class DummyLLM(LLM_Model):
#         async def generate_text_async(self, prompt: str, **kwargs) -> str:
#             print("DummyLLM: Received prompt (first 100 chars):", prompt[:100])
#             # Simulate LLM generating Python code based on the example in the prompt
#             example_code = """
#import json
#import pandas as pd
#from datetime import datetime
#
#def query_data_for_question():
#    patient_email_to_find = "aaronmeers73@gmail.com"
#    json_base_path = "./all_patient_jsons_with_prefix/"
#    try:
#        master_df = pd.read_csv("master_patient_json_links.csv")
#        file_path_series = master_df[master_df["Patient Email"] == patient_email_to_find]["JSON File Path (Relative to Output Root)"]
#        if file_path_series.empty:
#            return f"Error: Patient email {patient_email_to_find} not found in master_patient_json_links.csv."
#        relative_json_path = file_path_series.iloc[0]
#        json_file_path = json_base_path + relative_json_path
#    except FileNotFoundError:
#        return "Error: master_patient_json_links.csv not found."
#    except Exception as e:
#        return f"Error reading master_patient_json_links.csv: {str(e)}"
#    try:
#        with open(json_file_path, 'r') as f:
#            data = json.load(f)
#    except FileNotFoundError:
#        return f"Error: JSON file not found at {json_file_path}."
#    except json.JSONDecodeError:
#        return f"Error: Could not decode JSON from {json_file_path}."
#    except Exception as e:
#        return f"Error reading or processing JSON file {json_file_path}: {str(e)}"
#    patient_sent_messages = []
#    for conv in data.get("conversations", []):
#        for msg in conv.get("messages", []):
#            if msg.get("direction") == "outbound":
#                patient_sent_messages.append({
#                    "subject": msg.get("subject"),
#                    "date_iso": msg.get("date_iso")
#                })
#    if not patient_sent_messages:
#        return f"No messages found where patient {patient_email_to_find} was the sender."
#    patient_sent_messages.sort(key=lambda x: datetime.fromisoformat(x["date_iso"].replace("Z", "+00:00")), reverse=True)
#    last_2_subjects = [msg["subject"] for msg in patient_sent_messages[:2]]
#    return last_2_subjects
#            """
#            return f"```python\n{example_code}\n```"
#
#        async def generate_text_from_chat_async(self, prompt: str, context: str = None, examples: List[Dict[str, str]] = None, **kwargs) -> str:
#             # Simplified for this dummy, just use the text generation part
#            return await self.generate_text_async(prompt, **kwargs)


#     llm_model_instance = DummyLLM()
#     json_query_agent = BuildJSONQueryAgent(llm_model=llm_model_instance)
#
#     test_question = "What were the subjects of the last 2 emails from 'aaronmeers73@gmail.com' where the patient was the sender?"
#
#     async def run_test():
#         result = await json_query_agent.generate_python_query_code(
#             user_question=test_question
#             # Using default example schema descriptions for this test
#         )
#         print("\n--- Agent Result ---")
#         if result["status"] == "success":
#             print("Generated Python Code:")
#             print(result["python_code"])
#         else:
#             print("Error generating code:")
#             print(result["error_message"])
#         # print("\nFull prompt sent to LLM (for debugging):")
#         # print(result["prompt_sent"])
#
#     asyncio.run(run_test())
