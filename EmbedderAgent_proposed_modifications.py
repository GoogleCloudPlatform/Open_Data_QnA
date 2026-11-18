from abc import ABC
from .core import Agent # Assuming .core is in the same directory orPYTHONPATH
from vertexai.language_models import TextEmbeddingModel
# from langchain.embeddings import VertexAIEmbeddings # Keep for lang-vertex mode
# from langchain.docstore.document import Document # For creating Document objects

# --- FOR PROPOSED MODIFICATIONS ---
# Import functions from the updated embedding_content_preparation.py
# This assumes embedding_content_preparation.py is in the python path or same directory
# from embedding_content_preparation import (
# generate_json_schema_description_from_file,
# generate_text_file_schema_description,
# generate_json_filenames_summary_description_from_file
# )
import os # For checking file existence

class EmbedderAgent(Agent, ABC):
    """
    An agent specialized in generating text embeddings using Large Language Models (LLMs).
    This agent supports two modes for generating embeddings:
    1. "vertex": Directly interacts with the Vertex AI TextEmbeddingModel.
    2. "lang-vertex": Uses LangChain's VertexAIEmbeddings for a streamlined interface.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "EmbedderAgent".
        mode (str): The embedding generation mode ("vertex" or "lang-vertex").
        model: The underlying embedding model.
        vector_store: The configured vector store instance.
    """

    agentType: str = "EmbedderAgent"

    def __init__(self, mode, embeddings_model='text-embedding-004', vector_store=None):
        if mode == 'vertex':
            self.mode = mode
            self.model = TextEmbeddingModel.from_pretrained(embeddings_model)
        elif mode == 'lang-vertex':
            self.mode = mode
            from langchain.embeddings import VertexAIEmbeddings # Import moved here
            self.model = VertexAIEmbeddings(model_name=embeddings_model)
        else:
            raise ValueError('EmbedderAgent mode must be either vertex or lang-vertex')

        self.vector_store = vector_store

    def create(self, question_or_texts): # Renamed for clarity
        """
        Generates text embeddings for the given input text(s).
        Input can be a single string or a list of strings.
        """
        if self.mode == 'vertex':
            if isinstance(question_or_texts, str):
                embeddings_response = self.model.get_embeddings([question_or_texts])
                # Assuming get_embeddings returns a list of Embedding objects
                return embeddings_response[0].values if embeddings_response else None
            elif isinstance(question_or_texts, list):
                # Vertex AI SDK can take a list of up to 250 texts
                embeddings_response = self.model.get_embeddings(question_or_texts)
                return [emb.values for emb in embeddings_response] if embeddings_response else []
            else:
                raise ValueError('Input must be either str or list for vertex mode')

        elif self.mode == 'lang-vertex':
            if isinstance(question_or_texts, str):
                return self.model.embed_query(question_or_texts)
            elif isinstance(question_or_texts, list):
                return self.model.embed_documents(question_or_texts)
            else:
                raise ValueError('Input for lang-vertex mode must be str or list of str')
        return None # Should not reach here

    # --- START OF PROPOSED MODIFICATIONS ---

    def embed_and_store_data_source_schemas(self,
                                            json_schema_filepath="patient_json_schema.json",
                                            csv_schema_filepath="csv_schema.txt",
                                            master_csv_schema_filepath="master_csv_schema.txt",
                                            json_filenames_filepath="json_filenames.txt"):
        """
        Reads schema descriptions and data file information from specified files,
        generates descriptive texts using functions from embedding_content_preparation.py,
        embeds these texts, and stores them in the configured vector store with appropriate metadata.

        This method is designed to prepare the vector store with essential information
        for Retrieval-Augmented Generation (RAG) when dealing with JSON data,
        related CSV files, and the mechanism to link them.

        Args:
            json_schema_filepath (str): Path to the JSON schema file (e.g., patient_json_schema.json).
            csv_schema_filepath (str): Path to the text file describing the main CSV schema (e.g., all_email_corpus.csv).
            master_csv_schema_filepath (str): Path to the text file describing the master CSV linking schema.
            json_filenames_filepath (str): Path to the text file listing example JSON filenames.

        Returns:
            dict: A status dictionary indicating success/failure and details of embeddings.
        """
        print("Starting embedding process for data source schemas...")

        # Import preparation functions here to ensure they are picked up if this agent is loaded standalone
        # or to avoid circular dependencies at the module level if not careful.
        try:
            from embedding_content_preparation import (
                generate_json_schema_description_from_file,
                generate_text_file_schema_description,
                generate_json_filenames_summary_description_from_file
            )
        except ImportError:
            print("ERROR: embedding_content_preparation.py not found or functions not importable.")
            return {"status": "failure", "error": "Missing embedding_content_preparation module."}

        documents_to_embed = []
        errors = []

        # 1. Process Patient JSON Schema
        if os.path.exists(json_schema_filepath):
            json_schema_text = generate_json_schema_description_from_file(json_schema_filepath)
            if "Error" not in json_schema_text:
                documents_to_embed.append({
                    "text": json_schema_text,
                    "metadata": {"doc_type": "json_schema", "source_file": json_schema_filepath}
                })
            else: errors.append(f"JSON Schema: {json_schema_text}")
        else: errors.append(f"File not found: {json_schema_filepath}")

        # 2. Process CSV Schema (all_email_corpus.csv)
        if os.path.exists(csv_schema_filepath):
            csv_schema_text = generate_text_file_schema_description(csv_schema_filepath, "'all_email_corpus.csv'")
            if "Error" not in csv_schema_text:
                documents_to_embed.append({
                    "text": csv_schema_text,
                    "metadata": {"doc_type": "csv_schema", "describes": "all_email_corpus.csv", "source_file": csv_schema_filepath}
                })
            else: errors.append(f"CSV Schema: {csv_schema_text}")
        else: errors.append(f"File not found: {csv_schema_filepath}")

        # 3. Process Master CSV Schema (master_patient_json_links.csv)
        if os.path.exists(master_csv_schema_filepath):
            master_csv_schema_text = generate_text_file_schema_description(master_csv_schema_filepath, "'master_patient_json_links.csv'")
            if "Error" not in master_csv_schema_text:
                documents_to_embed.append({
                    "text": master_csv_schema_text,
                    "metadata": {"doc_type": "master_csv_schema", "describes": "master_patient_json_links.csv", "source_file": master_csv_schema_filepath}
                })
            else: errors.append(f"Master CSV Schema: {master_csv_schema_text}")
        else: errors.append(f"File not found: {master_csv_schema_filepath}")

        # 4. Process JSON Filenames Summary
        if os.path.exists(json_filenames_filepath):
            json_filenames_text = generate_json_filenames_summary_description_from_file(json_filenames_filepath)
            if "Error" not in json_filenames_text:
                documents_to_embed.append({
                    "text": json_filenames_text,
                    "metadata": {"doc_type": "json_filename_summary", "source_file": json_filenames_filepath}
                })
            else: errors.append(f"JSON Filenames: {json_filenames_text}")
        else: errors.append(f"File not found: {json_filenames_filepath}")

        if errors:
            print(f"Errors encountered during text preparation: {errors}")
            # Decide if to proceed with partial embedding or fail
            if not documents_to_embed:
                 return {"status": "failure", "error": "No documents to embed due to file errors.", "details": errors}

        # Prepare texts and metadatas for LangChain Document structure or direct embedding
        texts = [doc["text"] for doc in documents_to_embed]
        metadatas = [doc["metadata"] for doc in documents_to_embed]

        try:
            # Embed the texts using the agent's own 'create' method.
            # The 'create' method should handle a list of texts and return a list of embeddings.
            print(f"Generating embeddings for {len(texts)} document(s)...")
            embeddings_vectors = self.create(texts) # This calls the method defined above in the class

            if not embeddings_vectors or len(embeddings_vectors) != len(texts):
                raise ValueError("Failed to generate embeddings for all documents or embeddings list mismatch.")

            print(f"Successfully generated {len(embeddings_vectors)} embeddings.")

            # Store in vector store
            if self.vector_store:
                # Using LangChain's Document structure is common for vector store integration.
                from langchain.docstore.document import Document # Import here for clarity

                langchain_documents = []
                for i, text_content in enumerate(texts):
                    doc = Document(page_content=text_content, metadata=metadatas[i])
                    # Note: Embeddings themselves are not typically added to the Document object here.
                    # The vector store's `add_documents` method, when used with an embedder
                    # (like Langchain's VertexAIEmbeddings which our agent can be),
                    # will handle the embedding process for the page_content.
                    # If self.vector_store is configured to use this self.model (EmbedderAgent instance)
                    # as its embedder, then it works seamlessly.
                    langchain_documents.append(doc)

                # Conceptual: The vector_store.add_documents method will internally use an
                # embedding function (ideally configured to be this agent or a compatible one)
                # to convert Document.page_content into vectors and store them.
                self.vector_store.add_documents(langchain_documents)

                print(f"Successfully stored {len(langchain_documents)} documents with their embeddings in the vector store.")
                storage_status = "success"
            else:
                print("Vector store not configured. Skipping storage of embeddings.")
                storage_status = "skipped_storage (vector store not configured)"
                # For demonstration if no vector store:
                # for i, text_content in enumerate(texts):
                # print(f"  Text: '{text_content[:50]}...' -> Embedding (first 5 values): {embeddings_vectors[i][:5] if embeddings_vectors[i] else 'N/A'}...")

            return {
                "status": "success" if not errors else "partial_success",
                "embeddings_generated_count": len(embeddings_vectors) if embeddings_vectors else 0,
                "storage_status": storage_status,
                "prepared_texts_count": len(texts),
                "errors": errors if errors else None
            }

        except Exception as e:
            print(f"Error during embedding or storage: {e}")
            return {"status": "failure", "error": str(e), "details": errors}

    # --- END OF PROPOSED MODIFICATIONS ---

    # Example of how this new method might be called (conceptual)
    # if __name__ == '__main__':
    #     # This is conceptual and requires a vector store and GCP setup for actual execution.
    #     print("Conceptual demonstration of EmbedderAgent modifications")

    #     # Assuming a vector store is initialized (e.g., PGVector, BigQueryVectorStore via a connector)
    #     # from some_vector_store_library import MyVectorStoreConnector
    #     # vector_store_connector = MyVectorStoreConnector(embedding_function=None) # Or pass the agent itself

    #     # Initialize the agent
    #     # For 'lang-vertex' mode, the agent itself can be the embedding function for LangChain vector stores.
    #     # embedder_agent = EmbedderAgent(mode='lang-vertex', vector_store=vector_store_connector)
    #     # if vector_store_connector.embedding_function is None:
    #     #     vector_store_connector.embedding_function = embedder_agent.model # or just embedder_agent if it implements embed_documents/embed_query

        # Create dummy files for the agent to read (if they don't exist from previous steps)
        # file_paths = {
        #     "json_schema_filepath": "patient_json_schema.json",
        #     "csv_schema_filepath": "csv_schema.txt",
        #     "master_csv_schema_filepath": "master_csv_schema.txt",
        #     "json_filenames_filepath": "json_filenames.txt"
        # }
        # for fp in file_paths.values():
        #     if not os.path.exists(fp):
        #         with open(fp, "w") as f:
        #             f.write(f"Dummy content for {fp}") # Create minimal dummy files

        # Call the new method
        # print("\nCalling embed_and_store_data_source_schemas (simulated vector store)...")
        # embedder_agent_simulated_vs = EmbedderAgent(mode='lang-vertex', vector_store=None) # Simulate no vector store
        # result = embedder_agent_simulated_vs.embed_and_store_data_source_schemas(**file_paths)
        # print(f"\nResult of embedding process: {result}")

        # To run this, one would need:
        # 1. `embedding_content_preparation.py` in the same directory or PYTHONPATH.
        # 2. The dummy files created in earlier steps (`patient_json_schema.json`, etc.).
        # 3. A configured Vertex AI environment for embeddings.
        # 4. A vector store instance compatible with LangChain (if using `add_documents`).


    # Original embed_and_store_schema_descriptions - can be deprecated or removed
    # if the new method `embed_and_store_data_source_schemas` supersedes it.
    # For now, keeping it to show the evolution or if it serves a different specific purpose.
    def embed_and_store_schema_descriptions_OLD(self, formal_json_schema, csv_headers, json_lookup_meta_id="json_lookup_mechanism", csv_meta_id="csv_schema_description", json_meta_id="json_schema_description"):
        """
        DEPRECATED/OLD: Generates descriptions for JSON schema, CSV schema, and JSON file lookup,
        embeds them, and stores them in the configured vector store.
        This version takes direct inputs rather than file paths.
        """
        # ... (implementation from the original file can be kept here for reference or removed)
        print("WARN: Using embed_and_store_schema_descriptions_OLD. Consider new file-based method.")
        # The rest of the old method's code...
        pass


# Note on `config.ini` for the new method:
# The new method `embed_and_store_data_source_schemas` primarily relies on file paths
# passed as arguments. However, the agent's `__init__` already handles:
# - `mode` (vertex or lang-vertex)
# - `embeddings_model` (e.g., 'text-embedding-004')
# - `vector_store` (the vector store instance)
#
# No new `config.ini` parameters seem strictly required *for this method directly*,
# as the file paths are arguments.
# However, a robust application would likely load these default file paths from a configuration:
#
# Example conceptual additions to config.ini:
# [EmbeddingPaths]
# json_schema_file = patient_json_schema.json
# csv_schema_file = csv_schema.txt
# master_csv_schema_file = master_csv_schema.txt
# json_filenames_file = json_filenames.txt
#
# The script calling `embed_and_store_data_source_schemas` could then read these paths
# from the config and pass them to the method.
# The agent itself remains focused on its core task given the inputs.
#
# The existing `vector_store` configuration (how it's initialized and passed to the agent)
# is crucial and assumed to be handled by the calling framework/script based on `config.ini`
# settings for the chosen vector store (PGVector, BQ Vector Store, etc.).
#
# Metadata considerations:
# The metadata for each document is designed to be specific:
# - `doc_type`: "json_schema", "csv_schema", "master_csv_schema", "json_filename_summary"
#   This allows targeted retrieval. For example, if the LLM needs to understand the main JSON
#   structure, it can specifically query for documents with `doc_type: "json_schema"`.
# - `source_file`: Records the origin of the information.
# - `describes`: (for CSVs) clarifies which CSV file the schema refers to.
#
# This metadata structure helps in creating a more organized and searchable knowledge base
# within the vector store for the RAG process.
#
# For example, when building a prompt for the LLM to query JSON data,
# the RAG system could retrieve:
# 1. The JSON schema description (doc_type: "json_schema")
# 2. The master CSV schema description (doc_type: "master_csv_schema") to understand how to find the right JSON file.
# 3. The JSON filename summary (doc_type: "json_filename_summary") to understand file naming.
# These pieces of context would help the LLM formulate a plan to access and query the JSON data.
```
