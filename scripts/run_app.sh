#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"

# Check if generatedHostname is set and different from the current hostname
if [ -n "$generatedHostname" ] &&
    [ "$(hostnamectl hostname)" != "$generatedHostname" ]; then
    echo "Change hostname"
    sudo "$scripts_dir/change_hostname.sh" "$generatedHostname"
fi

export PYTHONPATH="$app_dir"
"$app_dir/venv/bin/python" -m src.main
