# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import configparser
import os
import sys

config = configparser.ConfigParser()

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

# [CONFIG]
EMBEDDING_MODEL = config['CONFIG']['EMBEDDING_MODEL']
DESCRIPTION_MODEL = config['CONFIG']['DESCRIPTION_MODEL']
DATA_SOURCE = config['CONFIG']['DATA_SOURCE'] 
VECTOR_STORE = config['CONFIG']['VECTOR_STORE']

#CACHING = config.getboolean('CONFIG','CACHING')
#DEBUGGING = config.getboolean('CONFIG','DEBUGGING')
LOGGING = config.getboolean('CONFIG','LOGGING')
EXAMPLES = config.getboolean('CONFIG', 'KGQ_EXAMPLES')

#[GCP]
PROJECT_ID =  config['GCP']['PROJECT_ID']

#[PGCLOUDSQL]
PG_REGION = config['PGCLOUDSQL']['PG_REGION']
PG_SCHEMA = config['PGCLOUDSQL']['PG_SCHEMA'] 
PG_INSTANCE = config['PGCLOUDSQL']['PG_INSTANCE']
PG_DATABASE = config['PGCLOUDSQL']['PG_DATABASE'] 
PG_USER = config['PGCLOUDSQL']['PG_USER'] 
PG_PASSWORD = config['PGCLOUDSQL']['PG_PASSWORD']

#[BIGQUERY]
BQ_REGION = config['BIGQUERY']['BQ_DATASET_REGION']
BQ_DATASET_NAME = config['BIGQUERY']['BQ_DATASET_NAME']
BQ_OPENDATAQNA_DATASET_NAME = config['BIGQUERY']['BQ_OPENDATAQNA_DATASET_NAME']
BQ_LOG_TABLE_NAME = config['BIGQUERY']['BQ_LOG_TABLE_NAME']
BQ_TABLE_LIST = config['BIGQUERY']['BQ_TABLE_LIST']



__all__ = ["EMBEDDING_MODEL",
           "DESCRIPTION_MODEL",
           "DATA_SOURCE",
           "VECTOR_STORE",
           #"CACHING",
           #"DEBUGGING",
           "LOGGING",
           "EXAMPLES", 
           "PROJECT_ID",
           "PG_REGION",
           "PG_SCHEMA",
           "PG_INSTANCE",
           "PG_DATABASE",
           "PG_USER",
           "PG_PASSWORD", 
           "BQ_REGION",
           "BQ_DATASET_NAME",
           "BQ_OPENDATAQNA_DATASET_NAME",
           "BQ_LOG_TABLE_NAME",
           "BQ_TABLE_LIST",
           "root_dir",
           "save_config"]