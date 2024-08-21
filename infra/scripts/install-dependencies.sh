#!/bin/bash

# Check if Poetry is already installed and on the PATH
pwd

pip3 install pipx
export PATH="$PATH:$(python3 -c "import sysconfig; print(sysconfig.get_paths()['scripts'])")"
echo "$PATH"
pipx install poetry
pipx ensurepath
source ~/.bashrc
poetry --version 
poetry lock
poetry install
poetry env info