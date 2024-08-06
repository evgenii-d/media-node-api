#!/bin/bash
set -e
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"

echo "[Setup Project]"

echo
echo "> Creating virtual environment"
python -m venv "$app_dir/venv"

echo "> Activating virtual environment"
. "$app_dir/venv/bin/activate"

echo "> Installing project dependencies"
pip install -r "$app_dir/requirements.txt"

echo "> Deactivating virtual environment"
deactivate

echo
echo "Done"
