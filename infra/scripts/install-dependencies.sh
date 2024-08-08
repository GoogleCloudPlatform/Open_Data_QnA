#!/bin/bash

# Check if Poetry is already installed and on the PATH
pwd
# pip3 uninstall poetry -y
pip3 install poetry --quiet

# if ! command -v poetry &> /dev/null; then
#   echo "Poetry not found. Installing..."

#   # Install or update Poetry (use appropriate method for your system)
#   curl -sSL https://install.python-poetry.org | python3 -

#   echo "Poetry installed successfully!"
# fi

# Get the installation path directly from Poetry
# POETRY_BIN_PATH=$(poetry config --list | grep virtualenvs.path | cut -d' ' -f2)/bin

# echo "$POETRY_BIN_PATH"
# # Check if the PATH already contains POETRY_BIN_PATH
# if ! grep -q "$POETRY_BIN_PATH" "$HOME/.bashrc"; then  
#   echo "Adding Poetry to PATH in ~/.bashrc..."

#   # Append the path to .zshrc or .bashrc (replace .zshrc with .bashrc if you use Bash)
#   echo "export PATH=$POETRY_BIN_PATH:$PATH" >> "$HOME/.bashrc"

#   # Source the updated profile
#   source "$HOME/.bashrc"

#   echo "Poetry added to PATH successfully!"
# else
#   echo "Poetry is already in PATH."
# fi

# Now you can safely run Poetry commands
poetry --version 
poetry lock
poetry install
poetry env info

# pip3 uninstall poetry -y
# pip3 install poetry --quiet

# poetry lock #resolve dependecies (also auto create poetry venv if not exists)
# poetry install --quiet #installs dependencies
# poetry env info #Displays the evn just created and the path to it

# poetry shell