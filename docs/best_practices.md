# Open Data QnA: Best Practices

## General Usage 

### Select the Right Database Connector: 
Choose between `PgConnector`(Google Cloud SQL PostgreSQL) and `BQConnector`(BigQuery) to match your specific database. 

### Prepare your data: 
Ensure your database tables are structured logically with appropriate column names and data types. We further recommend adding concise descriptions to tables and columns to provide the LLM agents with the necessary context. 
Additionally, please ensure that the overall data quality of your database is good - if you have pattern mismatches or missing values, these will impact the performance of the Open Data QnA solution. 

### Start simple: 
Begin with straightforward questions and fewer tables and progressively experiment with more complex queries and adding more tables. 

### Leverage the ‘Known Good SQL’ Cache
The `Known Good SQL` cache can (and should) be populated with example user question <-> SQL query pairs relating to your use case. This benefits the solution in two ways: 
Caching layer reduces latency: if a known user question is found in the cache that exactly matches (meaning, each char is matching, down to punctuation) the new input question, the known good SQL query is fetched and SQL generation will be skipped. 
In Context Learning: if a known user question is found to be similar to one of the existing queries in the cache, the similar user question is retrieved along with the corresponding SQL query and used as a few-shot example in the prompt for the SQL Generation agent. The user can specify how many example values should be retrieved to use as few-shot examples. We recommend using 3-5 examples, but this further depends on the variations of user questions you expect in your use case. 

### Explore Visualizations
Utilize the `VisualizeAgent`to generate charts and graphs for a more intuitive understanding of your data. However, make sure to only run the agent on queries that the pipeline has flagged as ‘valid’. 



## Customization & Optimization
### Agent Modification 
The `core`Agent class (agents/core.py) specifies the models supported for the different agents in the Open Data QnA solution. 

In version 1, these are: 
- Code Bison ('code-bison-32k')
- Text Bison ('text-bison-32k')
- Codechat Bison ('codechat-bison-32k') 
- Gemini 1.0 pro ('gemini-1.0-pro')

You can set the different models for each agent when calling the pipeline_run function (see below under `Pipeline Run Configurations`). 

### Prompt Engineering 
Each of the defined agents has their own prompt specified in its agent class file. 
BuildSQLAgent.py: prompts for BigQuery and PostgreSQL SQL Generation. 
DebugSQLAgent.py: prompts for debugging for either BQ or PG queries. 
DescriptionAgent.py: prompts for generating missing table and column descriptions. 
ResponseAgent.py: prompt to generate a natural language response, answering the user question by using the output of the generated SQL query. 
ValidateSQLAgent.py: prompt to classify a given SQL as valid or invalid. 
VisualizeAgent.py two prompts; one for proposing a fitting graph / plot for a given question <-> SQL pair; the other for generating the visualization. 


### Pipeline Run Configurations 
Additionally to changing the base models and the prompts, it is advisable to experiment with different configuration settings of the pipeline run function: 
```
async def run_pipeline(user_question,
               RUN_DEBUGGER=True,
               EXECUTE_FINAL_SQL=True,
               DEBUGGING_ROUNDS = 2,
               LLM_VALIDATION=True,
               SQLBuilder_model= 'gemini-1.0-pro',
               SQLChecker_model= 'gemini-1.0-pro',
               SQLDebugger_model= 'gemini-1.0-pro',
               Responder_model= 'gemini-1.0-pro',
               num_table_matches = 5,
               num_column_matches = 10,
               table_similarity_threshold = 0.3,
               column_similarity_threshold = 0.3,
               example_similarity_threshold = 0.3,
               num_sql_matches=3)
```


Args:

* **user_question (str):** The natural language question to answer.
* **RUN_DEBUGGER (bool, optional):** Whether to run the SQL debugger. Defaults to True.
It is recommended to use the debugger for improved SQL Generation accuracy.
* **DEBUGGING_ROUNDS (int, optional):** The number of debugging rounds. Defaults to 2.
We suggest using a value between 2-5, depending on your accuracy and latency requirements.  
* **EXECUTE_FINAL_SQL (bool, optional):** Whether to execute the final SQL query. Defaults to True.
You can disable the SQL execution. This will leave you with the generated SQL query as a response, skipping the retrieval of the execution result and the response generation. 
* **LLM_VALIDATION (bool, optional):** Whether to use LLM for SQL validation during debugging. Defaults to True.
You can disable the SQL Validator if you have specific latency requirements. When disabled, the Debugger will execute a dry run to retrieve any errors from the database call and debug accordingly. 
* **SQLBuilder_model (str, optional):** The name of the SQL building model. Defaults to 'gemini-1.0-pro'.
* **SQLChecker_model (str, optional):** The name of the SQL validation model. Defaults to 'gemini-1.0-pro'.
* **SQLDebugger_model (str, optional):** The name of the SQL debugging model. Defaults to 'gemini-1.0-pro'.
* **Responder_model (str, optional):** The name of the response generation model. Defaults to 'gemini-1.0-pro'.
* **num_table_matches (int, optional):** The number of similar tables to retrieve. Defaults to 5.
These will be used when calling the SQL Generation Agent. 
We recommend setting this higher if you have high variations in your database and user queries. 
* **num_column_matches (int, optional):** The number of similar columns to retrieve. Defaults to 10.
These will be used when calling the SQL Generation Agent. 
We recommend setting this higher if you have high variations in your database and user queries. 
* **table_similarity_threshold (float, optional):** The similarity threshold for tables. Defaults to 0.3.
Start with higher values and gradually decrease them if you’re not getting enough relevant results. 
* **column_similarity_threshold (float, optional):** The similarity threshold for columns. Defaults to 0.3.
Start with higher values and gradually decrease them if you’re not getting enough relevant results. 
* **example_similarity_threshold (float, optional):** The similarity threshold for example questions. Defaults to 0.3.
Start with higher values and gradually decrease them if you’re not getting enough relevant results. 
* **num_sql_matches (int, optional):** The number of similar SQL queries to retrieve. Defaults to 3.









