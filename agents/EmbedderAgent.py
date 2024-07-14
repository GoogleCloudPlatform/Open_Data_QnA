from abc import ABC
from .core import Agent 
from vertexai.language_models import TextEmbeddingModel



class EmbedderAgent(Agent, ABC):
    """
    An agent specialized in generating text embeddings using Large Language Models (LLMs).

    This agent supports two modes for generating embeddings:

    1. "vertex": Directly interacts with the Vertex AI TextEmbeddingModel.
    2. "lang-vertex": Uses LangChain's VertexAIEmbeddings for a streamlined interface.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "EmbedderAgent".
        mode (str): The embedding generation mode ("vertex" or "lang-vertex").
        model: The underlying embedding model (Vertex AI TextEmbeddingModel or LangChain's VertexAIEmbeddings).

    Methods:
        create(question) -> list:
            Generates text embeddings for the given question(s).

            Args:
                question (str or list): The text input for which embeddings are to be generated. Can be a single string or a list of strings.

            Returns:
                list: A list of embedding vectors. Each embedding vector is represented as a list of floating-point numbers.

            Raises:
                ValueError: If the input `question` is not a string or list, or if the specified `mode` is invalid.
    """


    agentType: str = "EmbedderAgent"

    def __init__(self, mode, embeddings_model='textembedding-gecko@002'): 
        if mode == 'vertex': 
            self.mode = mode 
            self.model = TextEmbeddingModel.from_pretrained(embeddings_model)

        elif mode == 'lang-vertex': 
            self.mode = mode 
            from langchain.embeddings import VertexAIEmbeddings
            self.model = VertexAIEmbeddings() 

        else: raise ValueError('EmbedderAgent mode must be either vertex or lang-vertex')



    def create(self, question): 
        """Text embedding with a Large Language Model."""

        if self.mode == 'vertex': 
            if isinstance(question, str): 
                embeddings = self.model.get_embeddings([question])
                for embedding in embeddings:
                    vector = embedding.values
                return vector
            
            elif isinstance(question, list):  
                vector = list() 
                for q in question: 
                    embeddings = self.model.get_embeddings([q])

                    for embedding in embeddings:
                        vector.append(embedding.values) 
                return vector
            
            else: raise ValueError('Input must be either str or list')

        elif self.mode == 'lang-vertex': 
            vector = self.embeddings_service.embed_documents(question)
            return vector           