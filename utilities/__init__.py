import configparser
import os
import sys
import yaml
from google.cloud import secretmanager

config = configparser.ConfigParser()

def _get_secret(project_id, secret_id, version_id="latest"):
    """
    Access a secret version from Google Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Failed to access secret {secret_id}: {e}")
        return None

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

def load_yaml(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

if is_root_dir():
    current_dir = os.getcwd()
    config.read(current_dir + '/config.ini')
    root_dir = current_dir
else:
    root_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    config.read(root_dir+'/config.ini')

if not 'root_dir' in locals():  # If not found in any parent dir
    raise FileNotFoundError("config.ini not found in current or parent directories.")

print(f'root_dir set to: {root_dir}')

def format_prompt(context_prompt, **kwargs):
    """
    Formats a context prompt by replacing placeholders with values from keyword arguments.
    Args:
        context_prompt (str): The prompt string containing placeholders (e.g., {var1}).
        **kwargs: Keyword arguments representing placeholder names and their values.
    Returns:
        str: The formatted prompt with placeholders replaced.
    """
    return context_prompt.format(**kwargs)

# [CONFIG]
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', config.get('CONFIG', 'EMBEDDING_MODEL'))
DESCRIPTION_MODEL = os.getenv('DESCRIPTION_MODEL', config.get('CONFIG', 'DESCRIPTION_MODEL'))
VECTOR_STORE = os.getenv('VECTOR_STORE', config.get('CONFIG', 'VECTOR_STORE'))
LOGGING = os.getenv('LOGGING', config.get('CONFIG', 'LOGGING', fallback='false')).lower() in ('true', '1', 't')
EXAMPLES = os.getenv('EXAMPLES', config.get('CONFIG', 'KGQ_EXAMPLES', fallback='false')).lower() in ('true', '1', 't')
USE_SESSION_HISTORY = os.getenv('USE_SESSION_HISTORY', config.get('CONFIG', 'USE_SESSION_HISTORY', fallback='false')).lower() in ('true', '1', 't')
USE_COLUMN_SAMPLES = os.getenv('USE_COLUMN_SAMPLES', config.get('CONFIG', 'USE_COLUMN_SAMPLES', fallback='false')).lower() in ('true', '1', 't')
FIRESTORE_REGION = os.getenv('FIRESTORE_REGION', config.get('CONFIG', 'FIRESTORE_REGION'))

#[GCP]
PROJECT_ID = os.getenv('PROJECT_ID', config.get('GCP', 'PROJECT_ID'))

#[PGCLOUDSQL]
PG_REGION = os.getenv('PG_REGION', config.get('PGCLOUDSQL', 'PG_REGION'))
PG_INSTANCE = os.getenv('PG_INSTANCE', config.get('PGCLOUDSQL', 'PG_INSTANCE'))
PG_DATABASE = os.getenv('PG_DATABASE', config.get('PGCLOUDSQL', 'PG_DATABASE'))
PG_USER = os.getenv('PG_USER', config.get('PGCLOUDSQL', 'PG_USER'))

# Logic for PG_PASSWORD:
# 1. Check for PG_PASSWORD_SECRET_ID env var. If set, fetch from Secret Manager.
# 2. If not, fall back to PG_PASSWORD env var.
# 3. If not, fall back to config.ini.
pg_password_secret_id = os.getenv('PG_PASSWORD_SECRET_ID')
if pg_password_secret_id:
    PG_PASSWORD = _get_secret(PROJECT_ID, pg_password_secret_id)
else:
    PG_PASSWORD = os.getenv('PG_PASSWORD', config.get('PGCLOUDSQL', 'PG_PASSWORD'))

#[BIGQUERY]
BQ_REGION = os.getenv('BQ_REGION', config.get('BIGQUERY', 'BQ_DATASET_REGION'))
BQ_OPENDATAQNA_DATASET_NAME = os.getenv('BQ_OPENDATAQNA_DATASET_NAME', config.get('BIGQUERY', 'BQ_OPENDATAQNA_DATASET_NAME'))
BQ_LOG_TABLE_NAME = os.getenv('BQ_LOG_TABLE_NAME', config.get('BIGQUERY', 'BQ_LOG_TABLE_NAME'))

#[MODELS]
SQLBUILDER_MODEL = os.getenv('SQLBUILDER_MODEL', config.get('MODELS', 'SQLBUILDER_MODEL'))
SQLCHECKER_MODEL = os.getenv('SQLCHECKER_MODEL', config.get('MODELS', 'SQLCHECKER_MODEL'))
SQLDEBUGGER_MODEL = os.getenv('SQLDEBUGGER_MODEL', config.get('MODELS', 'SQLDEBUGGER_MODEL'))
RESPONDER_MODEL = os.getenv('RESPONDER_MODEL', config.get('MODELS', 'RESPONDER_MODEL'))
EMBEDDER_MODEL = os.getenv('EMBEDDER_MODEL', config.get('MODELS', 'EMBEDDER_MODEL'))

#[PROMPTS]
PROMPTS = load_yaml(root_dir + '/prompts.yaml')

__all__ = ["EMBEDDING_MODEL",
           "DESCRIPTION_MODEL",
          #"DATA_SOURCE",
           "VECTOR_STORE",
           #"CACHING",
           #"DEBUGGING",
           "LOGGING",
           "EXAMPLES", 
           "PROJECT_ID",
           "PG_REGION",
        #    "PG_SCHEMA",
           "PG_INSTANCE",
           "PG_DATABASE",
           "PG_USER",
           "PG_PASSWORD", 
           "BQ_REGION",
        #    "BQ_DATASET_NAME",
           "BQ_OPENDATAQNA_DATASET_NAME",
           "BQ_LOG_TABLE_NAME",
        #    "BQ_TABLE_LIST",
           "FIRESTORE_REGION",
           "SQLBUILDER_MODEL",
           "SQLCHECKER_MODEL",
           "SQLDEBUGGER_MODEL",
           "RESPONDER_MODEL",
           "EMBEDDER_MODEL",
           "PROMPTS",
           "root_dir",
           "save_config"]