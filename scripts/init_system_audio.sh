#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
configs_dir="$app_dir/resources/configs"
system_control_config="$configs_dir/system_control.ini"

# Get the default audio device and volume from the config
audioDevice=$(grep "audioDevice" "$system_control_config" |
    cut -d "=" -f2 | tr -d "\r" | xargs)
volume=$(grep "volume" "$system_control_config" |
    cut -d "=" -f2 | tr -d "\r" | xargs)

if [ -n "$audioDevice" ]; then
    echo "Changing default audio device to $audioDevice"
    pacmd set-default-sink "$audioDevice"
fi

if [ -n "$volume" ]; then
    echo "Setting volume for default audio device to $volume%"
    pactl set-sink-volume @DEFAULT_SINK@ "$volume%"
fi
