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

    def __init__(self, mode, embeddings_model='text-embedding-004', vector_store=None):
        if mode == 'vertex': 
            self.mode = mode 
            self.model = TextEmbeddingModel.from_pretrained(embeddings_model)

        elif mode == 'lang-vertex': 
            self.mode = mode 
            # Assuming embeddings_service should be model for lang-vertex
            from langchain.embeddings import VertexAIEmbeddings
            self.model = VertexAIEmbeddings(model_name=embeddings_model)
            # self.embeddings_service = self.model # if 'embeddings_service' was a typo for 'model'

        else: raise ValueError('EmbedderAgent mode must be either vertex or lang-vertex')

        self.vector_store = vector_store # For storing embeddings



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
            # The original lang-vertex mode seemed to reference self.embeddings_service
            # which was not defined. Assuming it should use self.model like VertexAIEmbeddings()
            # If 'question' is a single string, embed_query is often used.
            # If 'question' is a list of strings (documents), embed_documents is used.
            if isinstance(question, str):
                vector = self.model.embed_query(question)
            elif isinstance(question, list):
                vector = self.model.embed_documents(question)
            else:
                raise ValueError('Input for lang-vertex mode must be str or list of str')
            return vector

    def embed_and_store_schema_descriptions(self, formal_json_schema, csv_headers, json_lookup_meta_id="json_lookup_mechanism", csv_meta_id="csv_schema_description", json_meta_id="json_schema_description"):
        """
        Generates descriptions for JSON schema, CSV schema, and JSON file lookup,
        embeds them, and stores them in the configured vector store.

        Args:
            formal_json_schema (dict): The formal JSON schema dictionary.
            csv_headers (list): A list of CSV column headers.
            json_lookup_meta_id (str): Metadata ID for the JSON lookup description document.
            csv_meta_id (str): Metadata ID for the CSV schema description document.
            json_meta_id (str): Metadata ID for the JSON schema description document.

        Returns:
            dict: A dictionary containing the generated text descriptions and their status of embedding.
                  Example: {'json_schema_text': text, 'csv_schema_text': text, ... , 'embedding_status': 'success/failure'}

        Worker Note:
        - This method assumes `self.vector_store` is initialized and has an `add_texts`
          or `add_documents` method compatible with LangChain vector stores.
        - The actual calls to Vertex AI or vector store are simulated if direct access is not available.
        - LangChain `Document` objects are typically created with `page_content` (the text)
          and `metadata` (e.g., an ID or source).
        """
        try:
            # Import preparation functions
            from embedding_content_preparation import (
                generate_json_schema_description,
                generate_csv_schema_description,
                generate_json_file_lookup_description
            )

            # 1. Generate descriptive texts
            json_schema_text = generate_json_schema_description(formal_json_schema)
            csv_schema_text = generate_csv_schema_description(csv_headers)
            json_lookup_text = generate_json_file_lookup_description()

            descriptions = {
                "json_schema": {"text": json_schema_text, "id": json_meta_id},
                "csv_schema": {"text": csv_schema_text, "id": csv_meta_id},
                "json_lookup": {"text": json_lookup_text, "id": json_lookup_meta_id},
            }

            texts_to_embed = [details["text"] for details in descriptions.values()]
            metadata_list = [{"source_id": details["id"]} for details in descriptions.values()]

            # 2. Embed the texts (using the agent's own 'create' method)
            # The 'create' method is expected to return a list of embeddings if a list of texts is passed.
            # If 'create' is not modified to handle lists for 'vertex' mode directly for batch,
            # it might need to be called in a loop or adjusted.
            # For simplicity, assuming 'create' can handle a list of texts or we call it iteratively.

            # Let's ensure create method handles list input for 'vertex' mode correctly.
            # Based on current 'create' method, it returns a list of embeddings if input is a list.
            embeddings = self.create(texts_to_embed)

            if not embeddings or len(embeddings) != len(texts_to_embed):
                raise ValueError("Failed to generate embeddings for all schema descriptions.")

            # 3. Store in vector store
            # This part is conceptual if self.vector_store is not fully available/mocked.
            # LangChain vector stores typically use `add_texts` or `add_documents`.
            # `add_texts` usually takes iterables of texts and metadatas.
            if self.vector_store:
                # Ensure compatibility with how vector_store expects embeddings.
                # Some stores take texts and embed them internally, others take pre-computed embeddings.
                # Let's assume self.vector_store.add_texts can take texts and metadatas,
                # and it will handle the embedding internally using an embedder it's configured with,
                # OR that it can take pre-embedded texts.
                # For now, we'll use add_texts, a common Langchain method.
                # If the vector store needs pre-computed embeddings, the interface might be different.

                # Option A: If vector_store embeds internally (common)
                # self.vector_store.add_texts(texts=texts_to_embed, metadatas=metadata_list)

                # Option B: If vector_store takes pre-computed texts and their embeddings
                # This is less common for add_texts, more for add_documents with Document objects
                # containing embeddings. For now, we will assume the vector_store is like Chroma/FAISS
                # which can take texts and will use its own configured embedder or one passed to it.
                # If our EmbedderAgent *is* the embedder for the vector store, this is fine.

                # Let's use Langchain's Document structure as it's common.
                from langchain.docstore.document import Document
                documents = []
                for i, text in enumerate(texts_to_embed):
                    doc = Document(page_content=text, metadata=metadata_list[i])
                    # Some vector stores might allow adding embeddings directly to documents
                    # or expect the embedding to happen during the add_documents call.
                    # For now, we prepare documents with text and metadata.
                    documents.append(doc)

                self.vector_store.add_documents(documents) # This is a common LangChain method

                print(f"Successfully embedded and stored schema descriptions in vector store: {', '.join(descriptions.keys())}")
                embedding_status = "success"
            else:
                print("Vector store not configured. Skipping storage of schema embeddings.")
                print("Generated Embeddings (first 50 chars of text and their simulated embeddings):")
                for i, text in enumerate(texts_to_embed):
                    print(f"  Text: '{text[:50]}...' -> Embedding (simulated): {embeddings[i][:5] if embeddings[i] else 'N/A'}...")
                embedding_status = "skipped_storage"

            return {
                "json_schema_text": json_schema_text,
                "csv_schema_text": csv_schema_text,
                "json_lookup_text": json_lookup_text,
                "embedding_status": embedding_status,
                "embeddings_generated_count": len(embeddings) if embeddings else 0
            }

        except Exception as e:
            print(f"Error in embed_and_store_schema_descriptions: {e}")
            return {
                "error": str(e),
                "embedding_status": "failure"
            }