"""
Provides the base class for all Agents 
"""

from abc import ABC
import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.language_models import CodeGenerationModel
from vertexai.language_models import CodeChatModel
from vertexai.generative_models import GenerativeModel
from vertexai.generative_models import HarmCategory,HarmBlockThreshold



from utilities import PROJECT_ID, PG_REGION
vertexai.init(project=PROJECT_ID, location=PG_REGION)



class Agent(ABC):
    """
    The core class for all Agents
    """

    agentType: str = "Agent"

    def __init__(self,
                model_id:str):
        """
        model_id is the Model ID for initialization
        """

        self.model_id = model_id 

        if model_id == 'code-bison-32k':
            self.model = CodeGenerationModel.from_pretrained('code-bison-32k')
        elif model_id == 'text-bison-32k':
            self.model = TextGenerationModel.from_pretrained('text-bison-32k')
        elif model_id == 'codechat-bison-32k':
            self.model = CodeChatModel.from_pretrained("codechat-bison-32k")
        elif model_id == 'gemini-1.0-pro':
            # print("Model is gemini 1.0 pro")
            self.model = GenerativeModel("gemini-1.0-pro-001")
            self.safety_settings: Optional[dict] = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        elif model_id == 'gemini-1.5-flash':
            # print("Model is gemini 1.5 flash")
            self.model = GenerativeModel("gemini-1.5-flash-preview-0514")
            self.safety_settings: Optional[dict] = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        elif model_id == 'gemini-1.5-pro':
            # print("Model is gemini 1.5 Pro")
            self.model = GenerativeModel("gemini-1.5-pro-001")
            self.safety_settings: Optional[dict] = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        else:
            raise ValueError("Please specify a compatible model.")

    def generate_llm_response(self,prompt):
        context_query = self.model.generate_content(prompt,safety_settings=self.safety_settings,stream=False)
        return str(context_query.candidates[0].text).replace("```sql", "").replace("```", "")


    def rewrite_question(self,question,session_history):
        formatted_history=''
        concat_questions=''
        for i, _row in enumerate(session_history,start=1):
            user_question = _row['user_question']
            # print(user_question)
            formatted_history += f"User Question - Turn :: {i} : {user_question}\n"
            concat_questions += f"{user_question} "

        # print(formatted_history)


        context_prompt = f"""
            Your main objective is to rewrite and refine the question based on the previous questions that has been asked.

            Refine the given question using the provided questions history to produce a standalone question with full context. The refined question should be self-contained, requiring no additional context for answering it.

            Make sure all the information is included in the re-written question. You just need to respond with the re-written question.

            Below is the previous questions history:

            {formatted_history}

            Question to rewrite:

            {question}
        """
        re_written_qe = str(self.generate_llm_response(context_prompt))
        

        print("*"*25 +"Re-written question:: "+"*"*25+"\n"+str(re_written_qe))

        return str(concat_questions),str(re_written_qe)

