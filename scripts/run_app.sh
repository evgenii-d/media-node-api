#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath $0)")")"

if [ ! -z "$generatedHostname" ] &&
    [ "$(hostnamectl hostname)" != "$generatedHostname" ]; then
    echo "Set new hostname"
    sudo hostnamectl set-hostname "$generatedHostname"
    sleep 5 && sudo shutdown -r now
fi

export PYTHONPATH=$app_dir
$app_dir/venv/bin/python -m src.main
