#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$0")
echo "$SCRIPT_DIR"
# Activate the poetry virtual environment
source "$(poetry env info --path)/bin/activate"

# Navigate to the correct directory (assuming the script is in the 'scripts' folder)
cd "$SCRIPT_DIR/"
pwd
# Execute the Python file within the virtual environment
poetry run python create-and-store-embeddings.py


# poetry run python create-and-store-embeddings.py