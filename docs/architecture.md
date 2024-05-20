Architecture
-------------
<p align="center">
    <a href="utilities/imgs/Open Data QnA Solution Architecture.png">
        <img src="utilities/imgs/OpenDataQnA Solution Architecture - v1.png" alt="aaie image">
    </a>
</p>



Architecture Summary
-------------
Open Data QnA operates in a sequence of well-defined steps, orchestrating various agents to process user queries and generate informative responses:

* **Vector Store Creation:** The vector store is initialized, storing embeddings of known good SQL queries, table schemas, and column details. This serves as a knowledge base for retrieval-augmented generation (RAG).

* **RAG (Retrieval-Augmented Generation):** User queries are embedded and compared to the vector store to retrieve relevant context (table/column details and similar past queries) for improved query generation.

* **SQL Generation (BuildSQLAgent):**  The BuildSQLAgent leverages the retrieved context and the user's natural language question to generate an initial SQL query.

* **Optional Validation (ValidateSQLAgent):** If enabled, the ValidateSQLAgent assesses the generated SQL for syntactic and semantic correctness.

* **Optional Debugging (DebugSQLAgent):** If the initial SQL is invalid and debugging is enabled, the DebugSQLAgent iteratively refines the query based on error feedback.

* **SQL Execution (Dry Run/Explain):** The refined SQL query is tested with a dry run (BigQuery) or explain plan (PostgreSQL) to estimate resource usage and identify potential errors.

* **SQL Execution (Full Run):** If the query is deemed valid, it's executed against the database to fetch the results.

* **Response Generation (ResponseAgent):** The ResponseAgent analyzes the SQL results and the user's question to generate a natural language response, providing a clear and concise answer.

* **Optional Visualization (VisualizeAgent):** If enabled, the VisualizeAgent suggests suitable chart types and generates JavaScript code for Google Charts to display the SQL results in a visually appealing manner.


**Key Points:**

* **Modularity:** Each step is handled by a specialized agent, allowing for flexibility and customization.
* **RAG Enhancement:** The use of retrieval-augmented generation leverages existing knowledge for better query formulation.
* **Validation and Debugging:** Optional agents enhance the reliability and accuracy of generated queries.
* **Informative Responses:** The ResponseAgent aims to provide meaningful and contextually relevant answers.
* **Visual Appeal:** The optional visualization adds an interactive layer to the user experience.
