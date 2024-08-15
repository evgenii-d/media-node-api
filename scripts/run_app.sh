#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
hostname_file="$app_dir/resources/configs/hostname.txt"

# Set new hostname if 'hostname.txt' exists
if [[ -f "$hostname_file" ]]; then
    uuid="$(openssl rand -hex 16)"
    rm "$hostname_file"
    echo "Change hostname"
    sudo "$scripts_dir/change_hostname.sh" "node-$uuid"
fi

export PYTHONPATH="$app_dir"
"$app_dir/venv/bin/python" -m src.main
