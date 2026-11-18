import ast
from abc import ABC
from .core import Agent, LLM_Model # Assuming .core contains Agent and LLM_Model
from typing import Dict, Any

# Placeholder for schema descriptions that might be used by an LLM for validation assistance
EXAMPLE_JSON_SCHEMA_DESC_VALIDATION = """
Brief JSON Schema Overview:
- Top-level keys: patient_email_original, conversations.
- 'conversations' is an array of objects, each with 'messages'.
- 'messages' is an array of objects, each with 'message_id', 'date_iso', 'subject', 'body', 'direction', 'sender'.
(This is a highly simplified version for the validation prompt, actual schema is more complex)
"""

class ValidateJSONQueryAgent(Agent, ABC):
    """
    Agent specialized in validating Python code generated for querying JSON files.
    Primary validation is done using ast.parse() for syntax check.
    Optionally, an LLM can be used for a high-level semantic check.
    """
    agentType: str = "ValidateJSONQueryAgent"

    PYTHON_VALIDATION_PROMPT_TEMPLATE = """
You are a Python code review assistant.
Your task is to perform a high-level review of the provided Python code snippet.
The code is intended to query patient data from JSON files based on a user's question.

Provided Python Code:
```python
{python_code}
```

User's Question (for context, if available):
{user_question}

JSON Schema Context (highly simplified):
{json_schema_description}

Please check for the following:
1.  **Obvious Syntax Errors:** Does the code appear to have gross syntactical issues that `ast.parse()` might miss in edge cases or that are pattern-based? (Primary syntax check is done by `ast.parse()`).
2.  **Alignment with Task:** Does the code generally seem to be trying to load JSON, access its elements, and filter data?
3.  **Basic Safety/Best Practices (High Level):** Are there any obvious anti-patterns like hardcoded sensitive data (though unlikely in this context) or extremely inefficient loops if immediately apparent?
4.  **Import Usage:** Does it import reasonable libraries for JSON processing (e.g., `json`, `pandas` for CSVs if used for lookup)?

Do not perform a deep semantic analysis or execute the code.
This is a quick check. The main syntactic validation is done by `ast.parse()`.

Based on your review, answer with:
- If the code seems plausible and syntactically okay at a high level: "VALID"
- If you spot obvious issues based on the criteria above: "INVALID" followed by a brief, one-sentence explanation.

Example:
User Question: "Get emails from patient X"
Code: (some python code)
JSON Schema: (brief schema)
Your response: VALID

User Question: "Get emails"
Code: "def my_func(): print('hello world'" (missing closing parenthesis)
JSON Schema: (brief schema)
Your response: INVALID - Appears to have a syntax error (e.g., unclosed parenthesis).
"""

    def __init__(self, llm_model: LLM_Model, model_name="gemini-1.0-pro", use_llm_for_เสริม_validation=False, **kwargs):
        super().__init__(llm_model, model_name, **kwargs)
        self.use_llm_for_เสริม_validation = use_llm_for_เสริม_validation # "เสริม" means supplementary

    def _validate_python_syntax(self, python_code: str) -> Dict[str, Any]:
        """
        Validates Python code syntax using ast.parse().
        """
        try:
            ast.parse(python_code)
            return {"is_valid": True, "error_message": None, "details": "Code is syntactically valid."}
        except SyntaxError as e:
            return {
                "is_valid": False,
                "error_message": f"SyntaxError: {e.msg} (line {e.lineno}, offset {e.offset})",
                "details": str(e)
            }
        except Exception as e: # Catch other potential errors during parsing
            return {
                "is_valid": False,
                "error_message": f"Error during ast.parse: {str(e)}",
                "details": str(e)
            }

    async def validate_code(self,
                            python_code: str,
                            user_question: str = "Not provided", # Optional, for LLM context
                            json_schema_desc: str = EXAMPLE_JSON_SCHEMA_DESC_VALIDATION, # Optional
                            **kwargs) -> Dict[str, Any]:
        """
        Validates the generated Python code.
        The primary check is Python syntax using ast.parse().
        If use_llm_for_เสริม_validation is True, an LLM provides a high-level check.

        Args:
            python_code (str): The Python code string to validate.
            user_question (str, optional): The original user question for context.
            json_schema_desc (str, optional): A simplified JSON schema description for context.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing validation status.
                Example: {"is_valid": True/False, "error_message": "...", "llm_เสริม_check_result": "..."}
        """
        print(f"ValidateJSONQueryAgent: Validating Python code (first 100 chars): {python_code[:100]}...")

        # 1. Primary Syntax Validation using ast.parse()
        syntax_check_result = self._validate_python_syntax(python_code)

        if not syntax_check_result["is_valid"]:
            print(f"ValidateJSONQueryAgent: Syntax check FAILED. Error: {syntax_check_result['error_message']}")
            return {
                "is_valid": False,
                "error_type": "syntax_error",
                "error_message": syntax_check_result["error_message"],
                "details": syntax_check_result["details"],
                "llm_เสริม_check_result": "Not performed due to syntax error."
            }

        print("ValidateJSONQueryAgent: Syntax check PASSED with ast.parse().")

        # 2. Optional: High-level check using LLM (if enabled)
        llm_check_text = "Not performed."
        if self.use_llm_for_เสริม_validation:
            print("ValidateJSONQueryAgent: Performing supplementary LLM validation...")
            prompt = self.PYTHON_VALIDATION_PROMPT_TEMPLATE.format(
                python_code=python_code,
                user_question=user_question,
                json_schema_description=json_schema_desc
            )
            try:
                # Assuming base class has generate_text_from_chat_async or similar
                llm_response = await super().generate_text_from_chat_async(
                    prompt=prompt,
                    # context="Python code validation assistance", # Optional
                    **kwargs
                )
                llm_check_text = llm_response.strip()
                print(f"ValidateJSONQueryAgent: LLM supplementary check response: {llm_check_text}")
                if llm_check_text.upper().startswith("INVALID"):
                    # LLM found a high-level issue. We can flag this but ast.parse() is king for syntax.
                    # This could be a semantic issue or a missed syntactic one.
                    return {
                        "is_valid": False, # Or, can keep True based on ast.parse and let user decide on LLM feedback
                        "error_type": "llm_identified_issue",
                        "error_message": f"LLM supplementary check flagged potential issue: {llm_check_text}",
                        "details": llm_check_text,
                        "llm_เสริม_check_result": llm_check_text
                    }
            except Exception as e:
                print(f"ValidateJSONQueryAgent: Error during LLM supplementary validation: {e}")
                llm_check_text = f"Error: {e}"

        return {
            "is_valid": True, # If ast.parse passed and LLM (if used) didn't find critical issues
            "error_message": None,
            "details": "Code is syntactically valid. LLM supplementary check (if performed) found no critical issues or was not configured.",
            "llm_เสริม_check_result": llm_check_text
        }

    # Commenting out original SQL-specific methods (if any were in ValidateSQLAgent)
    # For example, if there was a method like `_run_sql_explain(sql_query)`:
    # def _run_sql_explain(self, sql_query: str):
    #     """ This method is SQL-specific and not applicable here. """
    #     # ... original SQL EXPLAIN logic ...
    #     pass
    #
    # async def validate_sql_query_with_db(self, sql_query: str, **kwargs):
    #     """ This method is SQL-specific and not applicable here. """
    #     # ... original logic involving DB connection and EXPLAIN ...
    #     pass


# Conceptual main execution for demonstration
# if __name__ == '__main__':
#     import asyncio
#     # This requires a concrete LLM_Model implementation
#     # from ..llm_models import GeminiModel # Example
#     # llm_model_instance = GeminiModel(model_name="gemini-1.0-pro")
#
#     # Create a dummy LLM model for testing structure
#     class DummyLLM(LLM_Model):
#         async def generate_text_async(self, prompt: str, **kwargs) -> str: return "VALID"
#         async def generate_text_from_chat_async(self, prompt: str, **kwargs) -> str: return "VALID"
#
#     llm_model_instance = DummyLLM()
#
#     # Test with use_llm_for_เสริม_validation = False (default)
#     validator_agent_no_llm = ValidateJSONQueryAgent(llm_model=llm_model_instance)
#
#     # Test with use_llm_for_เสริม_validation = True
#     validator_agent_with_llm = ValidateJSONQueryAgent(llm_model=llm_model_instance, use_llm_for_เสริม_validation=True)
#
#     valid_python_code = """
# import json
#
# def get_names(data_list):
#     names = []
#     for item in data_list:
#         if 'name' in item:
#             names.append(item['name'])
#     return names
#     """
#
#     invalid_python_code = """
# import json
#
# def get_names(data_list) # Missing colon
#     names = []
#     for item in data_list:
#         if 'name' in item:
#             names.append(item['name'])
#     return names
#     """
#
#     async def run_tests():
#         print("--- Testing with Valid Code (LLM validation OFF) ---")
#         result_valid_no_llm = await validator_agent_no_llm.validate_code(valid_python_code)
#         print(result_valid_no_llm)
#
#         print("\n--- Testing with Invalid Code (LLM validation OFF) ---")
#         result_invalid_no_llm = await validator_agent_no_llm.validate_code(invalid_python_code)
#         print(result_invalid_no_llm)
#
#         print("\n--- Testing with Valid Code (LLM validation ON) ---")
#         result_valid_with_llm = await validator_agent_with_llm.validate_code(valid_python_code, user_question="Get all names.")
#         print(result_valid_with_llm)
#
#     asyncio.run(run_tests())
