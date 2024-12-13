#!/bin/bash
set -e
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"

if [ "$EUID" -eq 0 ]; then
    echo "Run this script without root privileges." >&2
    exit 1
fi

echo
echo "[Setup Project]"
echo "> Creating virtual environment"
python3 -m venv "$app_dir/venv"

echo "> Activating virtual environment"
# shellcheck disable=SC1091
. "$app_dir/venv/bin/activate"

echo "> Installing project dependencies"
pip install -r "$app_dir/requirements.txt"

echo "> Deactivating virtual environment"
deactivate

echo
echo "Project setup complete."
