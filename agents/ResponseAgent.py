import json 
from abc import ABC
from .core import Agent, LLM_Model # Assuming .core.Agent and LLM_Model are defined
from typing import Any # For type hinting if LLM_Model is used directly
from utilities import PROMPTS, format_prompt # Assuming these are available
from vertexai.generative_models import HarmCategory, HarmBlockThreshold # Specific to Vertex AI
from google.cloud.aiplatform import telemetry # Specific to Vertex AI
import vertexai # Specific to Vertex AI
# Assuming utilities.PROJECT_ID and utilities.PG_REGION are available
# from utilities import PROJECT_ID, PG_REGION

# Initialize Vertex AI (if not already done globally)
# vertexai.init(project=PROJECT_ID, location=PG_REGION) # This is often done once at application startup

class ResponseAgent(Agent, ABC):
    """
    An agent that generates natural language responses to user questions based on
    the results from data querying (originally SQL, now Python code execution).

    This agent acts as a data assistant, interpreting query results and transforming
    them into user-friendly, natural language answers. It utilizes a language model
    to craft responses that effectively convey the information derived from the data.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "ResponseAgent".
        safety_settings (Dict, optional): Safety settings for the LLM.
    """
    agentType: str = "ResponseAgent"

    def __init__(self, llm_model: LLM_Model, model_name="gemini-1.0-pro", safety_settings=None, **kwargs):
        super().__init__(llm_model, model_name, **kwargs) # Call base class constructor
        if safety_settings is None:
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        else:
            self.safety_settings = safety_settings


    # MODIFICATION: Changed parameter name from sql_result to execution_result
    # execution_result is a dict: {'success': True/False, 'data': ..., 'error': ..., 'details': ...}
    async def run(self, user_question: str, execution_result: dict, **kwargs) -> str: # Added async and kwargs
        """
        Generates a natural language response to the user's question based on the
        result of the executed query code.

        Args:
            user_question (str): The question asked by the user in natural language.
            execution_result (dict): The result from execute_json_query.run_generated_code().
                                     Format: {'success': bool, 'data': any, 'error': str|None, 'details': str|None}
            **kwargs: Additional keyword arguments for the LLM call.

        Returns:
            str: The generated natural language response.
        """

        # MODIFICATION: Handle error case from execution_result
        if not execution_result.get('success', False):
            error_message = execution_result.get('error', 'An unspecified error occurred during query execution.')
            error_details = execution_result.get('details', '')

            print(f"ResponseAgent: Execution failed. Error: {error_message}, Details: {error_details}")

            nl_error_response_prompt_template = """
User's question: {user_question}
An error occurred while trying to get the answer for the user.
Error Message: "{error}"
Error Details: "{details}"

Please explain this error to a non-technical user in a brief, polite, and helpful manner.
If the error is 'FileNotFoundError', suggest that a required data file might be missing or a path is incorrect.
If the error is 'KeyError', suggest that the expected data might not be present in the available records.
If the error is a 'SyntaxError' in generated code, just state that a technical issue prevented fulfilling the request.
Do not try to make up an answer for the original user question. Focus on explaining the problem.
Your explanation:
"""
            error_prompt = nl_error_response_prompt_template.format(
                user_question=user_question,
                error=error_message,
                # Avoid sending full tracebacks directly to LLM for explanation if too verbose
                details=error_details if error_details and len(error_details) < 500 else "No further specific details."
            )
            try {
                error_explanation = await self._call_llm(error_prompt, **kwargs)
                return f"I'm sorry, I couldn't answer your question. {error_explanation}"
            } except Exception as e:
                print(f"ResponseAgent: LLM call for error explanation failed: {e}")
                # Fallback to a more direct, templated error message
                return f"I'm sorry, I encountered an error processing your request: {error_message}. Please try again later or contact support if the issue persists."


        # If execution was successful, process the data
        retrieved_data = execution_result.get('data')

        if isinstance(retrieved_data, str):
            execution_data_string = retrieved_data
        elif isinstance(retrieved_data, (list, dict)):
            try:
                execution_data_string = json.dumps(retrieved_data, indent=2, default=str)
            except TypeError:
                execution_data_string = str(retrieved_data)
        elif retrieved_data is None:
            execution_data_string = "No data was returned from the query."
        else:
            execution_data_string = str(retrieved_data)
        
        # MODIFIED PROMPT TEMPLATE (could be loaded from utilities.PROMPTS)
        NL_RESPONSE_PROMPT_TEMPLATE_ADAPTED = """
You are a helpful AI assistant. Your goal is to answer the user's question based on the data provided below.
The data was retrieved by executing a Python script designed to query JSON data files.
Present the information clearly, concisely, and in a conversational manner.
Do not just repeat the data verbatim if it's complex; summarize it or extract key insights relevant to the question.
If the data seems to directly answer the question as a single fact, present that fact.
If the data is a list or has multiple parts, summarize them or list the most relevant items.
If the data is empty, explicitly state that no information was found matching the user's criteria.
If the data indicates an error or a specific reason why information isn't available (e.g. "patient not found"), relay that.

User's Question:
{user_question}

Retrieved Data (in JSON format, or as a simple string):
```
{execution_data_string}
```

Based on this, your natural language response to the user is:
"""
        context_prompt = NL_RESPONSE_PROMPT_TEMPLATE_ADAPTED.format(
            user_question=user_question,
            execution_data_string=execution_data_string
        )

        # print(f"ResponseAgent: Prompt for Natural Language Response: \n{context_prompt}")

        try {
            natural_language_response = await self._call_llm(context_prompt, **kwargs)
            return natural_language_response
        } except Exception as e:
            print(f"ResponseAgent: LLM call for generating response failed: {e}")
            return f"I found some information, but I had trouble phrasing a response. The raw data is: {execution_data_string}"


    async def _call_llm(self, prompt: str, **kwargs) -> str: # Added async
        """
        Encapsulates the actual LLM call logic.
        """
        # Ensure self.model is the initialized LLM model instance from the base class.
        # The original code used self.model.generate_content or self.model.predict
        # This assumes the base Agent's __init__ correctly sets up self.model and self.model_id
        if 'gemini' in self.model_id:
            with telemetry.tool_context_manager('opendataqna-response-v2'):
                # Pass through kwargs like temperature if they are supported
                response = await self.model.generate_content_async( # Use async version
                    prompt,
                    safety_settings=self.safety_settings,
                    stream=False,
                    generation_config=kwargs # e.g., {"temperature": 0.7}
                )
                return str(response.candidates[0].content.parts[0].text) # Adjusted for Gemini API
        else: # Assuming this is for other models like PaLM (older API)
             with telemetry.tool_context_manager('opendataqna-response-v2'):
                # PaLM predict API might not be async by default or might have different kwargs
                # This part might need adjustment based on the actual PaLM SDK being used if it's not Gemini
                # For now, assuming a synchronous call or that the base model handles async if available
                response = self.model.predict(prompt, **kwargs) # e.g. max_output_tokens=8000, temperature=0
                # The way to get text might vary; common for older PaLM SDK was response.text
                return str(response.text if hasattr(response, 'text') else response.candidates[0])

        return "Error: LLM model type not recognized or call failed."

# Example of how this might be used (conceptual, actual call is from orchestrator)
# if __name__ == '__main__':
#     import asyncio
#     # Dummy LLM and Agent base for testing
#     class DummyLLMModel:
#         async def generate_content_async(self, prompt, safety_settings, stream, generation_config):
#             class Part: text: str; constructor(t) { this.text = t; }
#             class Content: parts: Part[]; constructor(t) { this.parts = [new Part(t)]; }
#             class Candidate: content: Content; constructor(t) { this.content = new Content(t); }
#             class Response: candidates: Candidate[]; constructor(t) { this.candidates = [new Candidate(t)]; }

#             print(f"DummyLLM (Gemini-style): Received prompt for nl_response (first 150 chars): {prompt[:150]}...")
#             if "error" in prompt.lower() and "explain this error" in prompt.lower():
#                 return Response("It seems there was a technical hiccup while trying to find that information for you.")
#             return Response(f"Based on your question about '{prompt.split('UserQuestion:')[1].split('Retrieved Data:')[0].strip()}', the data indicates: [Processed Data Placeholder].")

#     class DummyBaseAgent(ABC):
#         def __init__(self, llm_model: Any, model_id: str, **kwargs):
#             self.model = llm_model
#             self.model_id = model_id
#             self.safety_settings = {} # Simplified

#     class TestResponseAgent(ResponseAgent, DummyBaseAgent):
#         def __init__(self, llm_model: Any, model_id: str, **kwargs):
#             DummyBaseAgent.__init__(self, llm_model, model_id, **kwargs)
#             ResponseAgent.__init__(self, llm_model, model_id, **kwargs)


#     async def main():
#         print("--- Testing ResponseAgent Outline ---")
#         dummy_llm = DummyLLMModel()
#         response_agent = TestResponseAgent(llm_model=dummy_llm, model_id="gemini-1.0-pro")

#         user_q1 = "What are the recent subjects for patient X?"
#         exec_res1 = {'success': True, 'data': [{"subject": "Follow up"}, {"subject": "Lab results"}], 'error': None}
#         nl_response1 = await response_agent.run(user_q1, exec_res1)
#         print(f"\nUser Question 1: {user_q1}\nResponse 1: {nl_response1}")

#         user_q4 = "What is the patient's primary concern?"
#         exec_res4 = {'success': False, 'data': None, 'error': "KeyError: 'primary_concern'", 'details': "The key 'primary_concern' was not found."}
#         nl_response4 = await response_agent.run(user_q4, exec_res4)
#         print(f"\nUser Question 4: {user_q4}\nResponse 4: {nl_response4}")

#     if __name__ == '__main__':
#         asyncio.run(main())
