#!/bin/bash

# Check if Poetry is already installed and on the PATH
pwd

pip3 install pipx
export PATH="$PATH:$(python3 -m site --user-base)/bin"
pipx install poetry

poetry --version 
poetry lock
poetry install
poetry env info