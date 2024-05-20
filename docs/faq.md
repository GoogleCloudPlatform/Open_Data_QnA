# Open Data QnA: FAQ

## Source and Vector Store Setup
**Q: If new to the vector store concept, which vector store would you recommend?**

A: Both the vector stores (pgvector and bigquery vector) are created using embedding model as you specify and also the vector search for both the vector stores are using cosine similarity to find the nearest matches. You can choose bigquery vector as that avoids any extra resource like cloudsql. 
Vector Embeddings and Search

________

**Q: Why are my example SQLs not being pulled as few-shot examples for the question asked even though the question is almost similar?**

A: Verify if the embedding of the example question has happened successfully.
Check the retrieval SQL written to pull the similar sqls for a few shot examples. If the cosine similarity logic is wrong that might be the reason for the issue. Correct the SQL to pull required similarity based SQLs

## Accuracy and Latency

**Q: How accurate are the results?**

A: Depending on the context, the more accurate these are helpful with accuracy.
Building blocks such as known good sql, validation all help with accuracy

________
**Q: How is the latency overall?**
A: Ambiguous questions have increased latency. If latency is a factor, would suggest adding caching layer and reducing validation steps
V2 is also coming up with resolving ambiguity



## Overall Solution
**Q: How do I get started quickly?**

A: The quickest way is to follow the "Quickstart with Open Data QnA: Standalone BigQuery Notebook." It provides a simplified experience using BigQuery. If you need more customization, follow the instructions for setting up the main repository.

________
**Q: Which databases does Open Data QnA currently support?**

A: Currently, it supports Google Cloud SQL for PostgreSQL and Google BigQuery.

________
**Q: What are the requirements to use Open Data QnA?**

A: You'll need:
A Google Cloud Project
An active database (PostgreSQL or BigQuery)
Python 3.9 or higher
Required Python packages (listed in requirements.txt)

________
**Q: Can I customize the behavior of the agents?**

A: Yes, the agents are designed to be modular and extensible. You can modify their code or create your own custom agents.

________
**Q: How do I incorporate my own known good SQL queries into the system?**

A: Follow the setup instructions or use the "3. Loading Known Good SQL Examples" notebook to add your own SQL queries to the vector store. This will improve the accuracy of query generation through RAG.
________

**Q: How do I set the table, column, and example similarity thresholds?**

A: These thresholds are used during the Retrieval-Augmented Generation (RAG) process to determine how similar your query is to the stored embeddings.
Table Similarity Threshold: Determines how closely a user's query needs to match a table name in the vector store to be considered relevant. Higher values make the matching stricter.
Column Similarity Threshold: Similar to the table threshold, but for column names.
Example Similarity Threshold: Controls how closely a user's query needs to match a known good SQL query example to be considered similar.
You can adjust these thresholds when running the pipeline_run function. Start with the default values and experiment to find what works best for your specific data and queries. Generally, start with higher values and gradually decrease them if you're not getting enough relevant results.

________
**Q: Can I visualize the results of my queries?**

A: Yes, the VisualizeAgent can generate JavaScript code for Google Charts to create visualizations of your data.
________

**Q: Are all building blocks mandatory?**

A: No. They can be replaced
________

**Q: Can this be tested against any database?**

A: Tested against Oracle and Snowflake
________
**Q: How are the competitors doing?**

A: Few langchain labs, some experimenting with agents
________

**Q: I created a test colab with langchain and a simple implementation. Why complicate it?**

A: If your environment is not complex, we would suggest to leverage your simplified approach, or look into the [standalone notebook](/notebooks/(standalone)Run_OpenDataQnA.ipynb) 


