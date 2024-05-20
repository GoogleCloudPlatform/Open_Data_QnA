import os
import sys
import configparser


def is_root_dir():
    """
    Checks if the current working directory is the root directory of a project 
    by looking for either the "/notebooks" or "/agents" folders.

    Returns:
        bool: True if either directory exists in the current directory, False otherwise.
    """

    current_dir = os.getcwd()
    print("current dir: ", current_dir)
    notebooks_path = os.path.join(current_dir, "notebooks")
    agents_path = os.path.join(current_dir, "agents")
    
    return os.path.exists(notebooks_path) or os.path.exists(agents_path)



def save_config(embedding_model,
                description_model,
                data_source, 
                vector_store,
                logging,
                kgq_examples,
                PROJECT_ID,
                pg_region, 
                pg_instance, 
                pg_database, 
                pg_user, 
                pg_password, 
                pg_schema, 
                bq_dataset_region, 
                bq_dataset_name, 
                bq_opendataqna_dataset_name, 
                bq_log_table_name,
                bq_table_list): 
    
    config = configparser.ConfigParser()

    if is_root_dir():
        current_dir = os.getcwd()
        config.read(current_dir + '/config.ini')
        root_dir = current_dir
    else:
        root_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
        config.read(root_dir+'/config.ini')

    if not 'root_dir' in locals():  # If not found in any parent dir
        raise FileNotFoundError("config.ini not found in current or parent directories.")


    config['GCP']['PROJECT_ID'] = PROJECT_ID
    config['CONFIG']['DATA_SOURCE'] = data_source
    config['CONFIG']['VECTOR_STORE'] = vector_store
    config['CONFIG']['EMBEDDING_MODEL'] = embedding_model
    config['CONFIG']['DESCRIPTION_MODEL'] = description_model


    # Save the parameters based on Data Source and Vector Store Choices
    if data_source == 'cloudsql-pg' or vector_store == 'cloudsql-pgvector':
        config['PGCLOUDSQL']['PG_INSTANCE'] = pg_instance
        config['PGCLOUDSQL']['PG_DATABASE'] = pg_database
        config['PGCLOUDSQL']['PG_USER'] = pg_user
        config['PGCLOUDSQL']['PG_PASSWORD'] = pg_password
        config['PGCLOUDSQL']['PG_REGION'] = pg_region
        config['PGCLOUDSQL']['PG_SCHEMA'] = pg_schema

    if data_source := 'bigquery':
        config['BIGQUERY']['BQ_DATASET_REGION'] = bq_dataset_region
        config['BIGQUERY']['BQ_DATASET_NAME'] = bq_dataset_name
        config['BIGQUERY']['BQ_OPENDATAQNA_DATASET_NAME'] = bq_opendataqna_dataset_name
        config['BIGQUERY']['BQ_TABLE_LIST'] = str(bq_table_list)
        config['BIGQUERY']['BQ_LOG_TABLE_NAME'] = bq_log_table_name

    if logging: 
        config['CONFIG']['LOGGING'] = 'yes'
        config['BIGQUERY']['BQ_LOG_TABLE_NAME'] = bq_log_table_name

    else: 
        config['CONFIG']['LOGGING'] = 'no'

    if kgq_examples: 
        config['CONFIG']['KGQ_EXAMPLES'] = 'yes'

    else: 
        config['CONFIG']['KGQ_EXAMPLES'] = 'no'


    with open(root_dir+'/config.ini', 'w') as configfile:  
        config.write(configfile)

    print('All configuration paramaters saved to file!')