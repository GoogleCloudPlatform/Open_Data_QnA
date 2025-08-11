from abc import ABC
# Assuming .core and other necessary imports are available
from .core import Agent, LLM_Model
from typing import Dict, Any

# Placeholders for schema descriptions (these would be passed dynamically)
EXAMPLE_JSON_SCHEMA_DESC_DEBUG = """
JSON Schema Description (from patient_json_schema.json):
- Top-level keys: patient_email_original, total_conversations, conversations, last_updated_iso, patient_preferences.
  - 'patient_email_original' (string): The original email address of the patient.
  - 'conversations' (array of objects): List of conversation threads.
    - Each conversation object includes keys like: conversation_id, messages.
      - 'messages' (array of objects): List of messages.
        - Each message object includes keys like: message_id, sender, date_iso, subject, body, direction.
          - 'direction' (string enum: ['inbound', 'outbound']): Message direction relative to the patient.
(Note: This is a simplified version for the prompt. The actual schema is more detailed.)
"""

EXAMPLE_ALL_EMAIL_CORPUS_CSV_SCHEMA_DESC_DEBUG = """
Schema Description for 'all_email_corpus.csv' (from csv_schema.txt):
Relevant Columns:
- patient_email: The email of the patient.
- conversation_id: ID for the conversation thread.
- message_content: Text body of the email.
(Used if the query requires searching across all emails before focusing on a patient's JSON.)
"""

EXAMPLE_MASTER_PATIENT_LINKS_CSV_SCHEMA_DESC_DEBUG = """
Schema Description for 'master_patient_json_links.csv' (from master_csv_schema.txt):
Relevant Columns:
- "Patient Email": Primary email of the patient.
- "JSON File Path (Relative to Output Root)": Relative path to the patient's JSON data file.
This CSV MUST be used to map a patient_email to their specific JSON data file path.
"""

class DebugJSONQueryAgent(Agent, ABC):
    """
    Agent specialized in debugging Python code generated for querying JSON files.
    It leverages an LLM to analyze erroneous Python code, error messages,
    the user's question, and schema context to provide a corrected code version.
    """
    agentType: str = "DebugJSONQueryAgent"

    PYTHON_DEBUGGING_SYSTEM_PROMPT_TEMPLATE = """
You are an expert Python debugging assistant.
Your task is to analyze provided Python code that failed either due to a syntax error or a runtime error during execution.
The code was intended to query patient data from JSON files based on a user's natural language question.
You need to provide a corrected version of the Python code.

**1. Context for Debugging:**

    **a. User's Original Question:**
    This is the natural language question the user asked, which the original Python code attempted to answer.
    ```
    {user_question}
    ```

    **b. Erroneous Python Code:**
    This is the Python code that needs debugging.
    ```python
    {erroneous_python_code}
    ```

    **c. Error Message:**
    This is the error message produced by the code (e.g., from `ast.parse()` or a runtime exception).
    ```
    {error_message}
    ```

**2. Data Schemas and File Access Logic (Crucial for Correct Code):**

    **a. Patient JSON Data Structure:**
    Queried data is in JSON files. Base path for JSON files: './all_patient_jsons_with_prefix/'
    Schema:
    ```
    {json_schema_description}
    ```

    **b. Master Patient JSON Links CSV (`master_patient_json_links.csv`):**
    This CSV maps patient emails to their JSON file paths. The generated code MUST use this.
    Schema:
    ```
    {master_csv_schema_description}
    ```
    Example Python snippet for lookup (ensure correct column names based on schema):
    ```python
    # import pandas as pd
    # master_df = pd.read_csv('master_patient_json_links.csv')
    # file_path_series = master_df[master_df['Patient Email'] == patient_email_variable]['JSON File Path (Relative to Output Root)']
    # if not file_path_series.empty: relative_json_path = file_path_series.iloc[0]
    ```

    **c. All Email Corpus CSV (`all_email_corpus.csv`):**
    May be used to find relevant `patient_email`s if the user question is general.
    Schema:
    ```
    {all_email_corpus_csv_schema_description}
    ```

**3. Debugging Guidelines & Output Format:**

    *   **Analyze:** Carefully analyze the user question, the erroneous code, the error message, and all provided schemas.
    *   **Identify Root Cause:** Determine if the error is syntactic, logical (e.g., incorrect data access, wrong filtering), or due to misunderstanding the schemas/file lookup.
    *   **Correct the Code:** Provide a fully corrected Python code block.
        *   The corrected code should define a single primary function (e.g., `query_data_for_question()`) that returns the result.
        *   Include necessary imports (`json`, `pandas` if needed, `datetime`).
        *   Ensure JSON file paths are correctly constructed using the base path and the path from `master_patient_json_links.csv`.
        *   Access JSON fields safely (e.g., using `.get()`).
        *   Handle potential `FileNotFoundError` and `json.JSONDecodeError`.
        *   The function should `return` the result, not `print` it.
        *   Do NOT include code to call the function (e.g., `result = query_data_for_question()`).
    *   **Output:** Respond ONLY with the corrected Python code block, enclosed in ```python ... ```. Do not add explanations before or after the code block.

**Example (Illustrative):**
If the erroneous code had a typo like `jsn.load(f)` and the error was `NameError: name 'jsn' is not defined`, you would correct it to `json.load(f)`.
If the code failed to use `master_patient_json_links.csv` to find the file, you would add that logic.

Now, provide the corrected Python code block.
"""

    def __init__(self, llm_model: LLM_Model, model_name="gemini-1.0-pro", **kwargs):
        super().__init__(llm_model, model_name, **kwargs)

    def _prepare_llm_prompt_for_debugging(self,
                                           user_question: str,
                                           erroneous_code: str,
                                           error_message: str,
                                           json_schema_desc: str,
                                           all_email_corpus_csv_schema_desc: str,
                                           master_csv_schema_desc: str) -> str:
        """
        Formats the debugging system prompt with the specific context.
        """
        return self.PYTHON_DEBUGGING_SYSTEM_PROMPT_TEMPLATE.format(
            user_question=user_question,
            erroneous_python_code=erroneous_code,
            error_message=error_message,
            json_schema_description=json_schema_desc,
            all_email_corpus_csv_schema_description=all_email_corpus_csv_schema_desc,
            master_csv_schema_description=master_csv_schema_desc
        )

    async def debug_python_code(self,
                                user_question: str,
                                erroneous_code: str,
                                error_message: str,
                                # Schema descriptions would be passed from a context manager or RAG results
                                json_schema_description: str = EXAMPLE_JSON_SCHEMA_DESC_DEBUG,
                                all_email_corpus_csv_schema_description: str = EXAMPLE_ALL_EMAIL_CORPUS_CSV_SCHEMA_DESC_DEBUG,
                                master_csv_schema_description: str = EXAMPLE_MASTER_PATIENT_LINKS_CSV_SCHEMA_DESC_DEBUG,
                                **kwargs) -> Dict[str, Any]:
        """
        Attempts to debug the provided Python code using an LLM.

        Args:
            user_question (str): The original natural language question.
            erroneous_code (str): The Python code that failed.
            error_message (str): The error message from the failed execution or validation.
            json_schema_description (str): Description of the patient JSON data structure.
            all_email_corpus_csv_schema_description (str): Description of all_email_corpus.csv.
            master_csv_schema_description (str): Description of master_patient_json_links.csv.
            **kwargs: Additional keyword arguments for the LLM.

        Returns:
            Dict[str, Any]: A dictionary containing the suggested corrected Python code
                            (or an error if debugging failed) and other relevant info.
                            Example: {"corrected_code": "...", "status": "success"}
        """
        print(f"DebugJSONQueryAgent: Attempting to debug Python code. Error: {error_message}")
        print(f"Erroreous code (first 100 chars): {erroneous_code[:100]}...")

        # 1. Prepare the full prompt for the LLM
        full_prompt = self._prepare_llm_prompt_for_debugging(
            user_question=user_question,
            erroneous_code=erroneous_code,
            error_message=error_message,
            json_schema_desc=json_schema_description,
            all_email_corpus_csv_schema_desc=all_email_corpus_csv_schema_description,
            master_csv_schema_desc=master_csv_schema_description
        )

        print("DebugJSONQueryAgent: Sending debugging prompt to LLM...")
        # For debugging, can print full_prompt or parts of it
        # print(full_prompt)

        # 2. Call the LLM
        try:
            llm_response = await super().generate_text_from_chat_async(
                prompt=full_prompt,
                # context="Python code debugging for JSON querying", # Optional
                **kwargs # Pass through temperature, max_output_tokens etc.
            )

            # Extract Python code if it's wrapped in markdown ```python ... ```
            corrected_code = llm_response
            if "```python" in corrected_code:
                corrected_code = corrected_code.split("```python\n")[1].split("\n```")[0]
            elif "```" in corrected_code and corrected_code.startswith("```"):
                 corrected_code = corrected_code.split("```\n")[1].split("\n```")[0]


            print("DebugJSONQueryAgent: Received corrected code from LLM.")
            return {
                "corrected_code": corrected_code,
                "status": "success",
                "prompt_sent": full_prompt # For debugging
            }
        except Exception as e:
            print(f"DebugJSONQueryAgent: Error during LLM interaction for debugging: {e}")
            return {
                "corrected_code": None,
                "status": "error",
                "error_message": str(e),
                "prompt_sent": full_prompt # For debugging
            }

# Conceptual main execution for demonstration
# if __name__ == '__main__':
#     import asyncio
#     # This requires a concrete LLM_Model implementation
#     # from ..llm_models import GeminiModel # Example
#     # llm_model_instance = GeminiModel(model_name="gemini-1.0-pro")
#
#     # Create a dummy LLM model for testing structure
#     class DummyLLM(LLM_Model):
#         async def generate_text_async(self, prompt: str, **kwargs) -> str: return "print('corrected code')" # Simplified
#         async def generate_text_from_chat_async(self, prompt: str, **kwargs) -> str:
#             print("DummyLLM for Debugging: Received prompt (first 100 chars):", prompt[:100])
#             # Simulate LLM providing corrected code
#             corrected_example = """
# import json
# import pandas as pd # Added missing import
#
# def query_data_for_question():
#     # Corrected logic based on error and question
#     patient_email = "test@example.com"
#     try:
#         # master_df = pd.read_csv('master_patient_json_links.csv') # Assume this was part of the fix
#         # ... more corrected code ...
#         return [{"subject": "Corrected Subject 1"}, {"subject": "Corrected Subject 2"}]
#     except Exception as e:
#         return f"Error in corrected code: {str(e)}"
#     """
#             return f"```python\n{corrected_example}\n```"
#
#     llm_model_instance = DummyLLM()
#     debugger_agent = DebugJSONQueryAgent(llm_model=llm_model_instance)
#
#     test_user_question = "Get subjects of last 2 emails from test@example.com"
#     test_erroneous_code = """
# import json
# # Missing pandas import
# def query_data_for_question():
#     patient_email = "test@example.com"
#     # Logic error: directly trying to open a file without lookup
#     with open(f"./all_patient_jsons_with_prefix/{patient_email}.json", 'r') as f:
#         data = json.load(f)
#     # ... rest of code might have issues ...
#     return [msg['subject'] for msg in data['messages'][:2]] # Simplified
#     """
#     test_error_message = "FileNotFoundError: [Errno 2] No such file or directory: './all_patient_jsons_with_prefix/test@example.com.json'"
#
#     async def run_debug_test():
#         result = await debugger_agent.debug_python_code(
#             user_question=test_user_question,
#             erroneous_code=test_erroneous_code,
#             error_message=test_error_message
#         )
#         print("\n--- Debug Agent Result ---")
#         if result["status"] == "success":
#             print("Suggested Corrected Code:")
#             print(result["corrected_code"])
#         else:
#             print("Error during debugging:")
#             print(result["error_message"])
#         # print("\nFull prompt sent for debugging (for review):")
#         # print(result["prompt_sent"])
#
#     asyncio.run(run_debug_test())
