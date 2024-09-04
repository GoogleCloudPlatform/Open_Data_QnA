from abc import ABC
from .core import Agent
import time


class DescriptionAgent(Agent, ABC):
    """
    An agent specialized in generating descriptions for database tables and columns.

    This agent leverages a large language model to create concise and informative descriptions that aid in understanding the structure and content of database elements. The generated descriptions can be valuable for documenting schemas, enhancing data exploration, and facilitating SQL query generation.

    Attributes:
        agentType (str): Indicates the type of agent, fixed as "DescriptionAgent".

    Methods:
        generate_llm_response(prompt) -> str:
            Generates a response from the underlying language model based on the given prompt.

            Args:
                prompt (str): The prompt to feed into the language model.

            Returns:
                str: The generated text response, cleaned of any SQL-related formatting artifacts.

        generate_missing_descriptions(source, table_desc_df, column_name_df) -> Tuple[pd.DataFrame, pd.DataFrame]:
            Generates missing table and column descriptions using the language model.

            Args:
                source (str): The source of the database schema ("bigquery").  
                table_desc_df (pd.DataFrame): A DataFrame containing table metadata with potential missing descriptions.
                column_name_df (pd.DataFrame): A DataFrame containing column metadata with potential missing descriptions.

            Returns:
                Tuple[pd.DataFrame, pd.DataFrame]: 
                    - The updated `table_desc_df` with generated table descriptions.
                    - The updated `column_name_df` with generated column descriptions.
    """


    agentType: str = "DescriptionAgent"

    def generate_llm_response(self,prompt):
        context_query = self.model.generate_content(prompt,safety_settings=self.safety_settings,stream=False)
        return str(context_query.candidates[0].text).replace("```sql", "").replace("```", "")


    def generate_missing_descriptions(self,source,table_desc_df, column_name_df):
        llm_generated=0
        print("\n\n")
        for index, row in table_desc_df.iterrows():
            if row['table_description'] is None or row['table_description']=='NA':
                q=f"table_name == '{row['table_name']}' and table_schema == '{row['table_schema']}'"
                if source=='bigquery':
                    context_prompt = f"""
                        Generate short and crisp description for the table {row['project_id']}.{row['table_schema']}.{row['table_name']}
                        Remember that this desciprtion should help LLMs to help build better SQL for any quries related to this table.
                        Parameters:
                        - column metadata: {column_name_df.query(q).to_markdown(index = False)}
                        - table metadata: {table_desc_df.query(q).to_markdown(index = False)}
                        
                        DO NOT generate description that is more than two lines
                    """
                else:
                     context_prompt = f"""
                        Generate short and crisp description for the table {row['table_schema']}.{row['table_name']}
                        Remember that this desciprtions should help LLMs to help build better SQL for any quries related to this table.
                        Parameters:
                        - column metadata: {column_name_df.query(q).to_markdown(index = False)}
                        - table metadata: {table_desc_df.query(q).to_markdown(index = False)}
                        DO NOT generate description that is more than two lines
                    """

                time.sleep(5) # to avoid quota errors
                table_desc_df.at[index,'table_description']=self.generate_llm_response(context_prompt)
                print(f"Generated table description for {row['table_schema']}.{row['table_name']}")
                llm_generated=llm_generated+1
        print("LLM generated "+ str(llm_generated) + " Table Descriptions")
        llm_generated = 0
        print("\n\n")
        for index, row in column_name_df.iterrows():
            # print(row['column_description'])
            if row['column_description'] is None or row['column_description']=='':
                q=f"table_name == '{row['table_name']}' and table_schema == '{row['table_schema']}'"
                if source=='bigquery':
                    context_prompt = f"""
                    Generate short and crisp description for the column {row['project_id']}.{row['table_schema']}.{row['table_name']}.{row['column_name']}
                    Remember that this description should help LLMs to help generate better SQL for any queries related to these columns.

                    Consider the below information while generating the description
                        Name of the column : {row['column_name']}
                        Data type of the column is : {row['data_type']}
                        Details of the table of this column are below:
                        {table_desc_df.query(q).to_markdown(index=False)}
                        Column Contrainst of this column are : {row['column_constraints']}

                    DO NOT generate description that is more than two lines
                """

                else:
                    context_prompt = f"""
                    Generate short and crisp description for the column {row['table_schema']}.{row['table_name']}.{row['column_name']}
                    Remember that this description should help LLMs to help generate better SQL for any queries related to these columns.

                    Consider the below information while generating the description

                        Name of the column : {row['column_name']}
                        Data type of the column is : {row['data_type']}
                        Details of the table of this column are below:
                        {table_desc_df.query(q).to_markdown(index=False)}
                        Column Contrainst of this column are : {row['column_constraints']}

                    DO NOT generate description that is more than two lines
                """
                    
                time.sleep(5) # to avoid quota errors
                column_name_df.at[index,'column_description']=self.generate_llm_response(prompt=context_prompt)
                print(f"Generated column description for {row['table_schema']}.{row['table_name']}.{row['column_name']}")
                llm_generated=llm_generated+1
                
        print("LLM generated "+ str(llm_generated) + " Column Descriptions")
        return table_desc_df,column_name_df
