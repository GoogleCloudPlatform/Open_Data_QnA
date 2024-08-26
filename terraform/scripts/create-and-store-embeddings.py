import os
import sys
import asyncio
module_path = os.path.abspath(os.path.join('..', '..'))
sys.path.append(module_path)

print(f"module_path: {module_path}")

os.chdir(module_path) 
current_dir = os.getcwd()

print(f"current_dir : {current_dir}")

from env_setup import get_embeddings, store_embeddings, store_kgq_sql_embeddings

async def create_and_store_embeddings():
# Generate embeddings for tables and columns
    table_schema_embeddings, col_schema_embeddings = get_embeddings()

# Store table/column embeddings (asynchronous)
    await(store_embeddings(table_schema_embeddings, col_schema_embeddings))

asyncio.run(create_and_store_embeddings())

# Store known good query embeddings (if enabled)
asyncio.run(store_kgq_sql_embeddings())
