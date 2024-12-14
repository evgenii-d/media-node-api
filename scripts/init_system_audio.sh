#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
configs_dir="$app_dir/resources/configs"
system_control_config="$configs_dir/system_control.ini"

# Check if system_control.ini exists
if [[ ! -f "$system_control_config" ]]; then
    echo "'system_control.ini' not found" >&2
    exit 1
fi

# Get the default audio device and volume from system_control_config
audioDevice=$(
    awk -F= '/^audioDevice/ {print $2; exit}' \
        "$system_control_config" | xargs
)
volume=$(
    awk -F= '/^volume/ {print $2; exit}' \
        "$system_control_config" | xargs
)

if [ -n "$audioDevice" ]; then
    echo "Changing default audio device to $audioDevice"
    pacmd set-default-sink "$audioDevice"
fi

if [ -n "$volume" ]; then
    echo "Setting volume for default audio device to $volume%"
    pactl set-sink-volume @DEFAULT_SINK@ "$volume%"
fi
