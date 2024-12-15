#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"
system_control_config="$configs_dir/system_control.ini"

# Get autostartDelay from system_control_config if it exists.
if [[ -f "$system_control_config" ]]; then
    autostartDelay=$(
        awk -F= '/^autostartDelay/ {print $2; exit}' \
            "$system_control_config" | xargs
    )
fi

# Sleep for autostartDelay if set, otherwise sleep for 10 seconds
sleep "${autostartDelay:-10}"

# Execute xrandr to configure displays
bash "$configs_dir/xrandr.txt"

# Set the system audio device and volume
"$scripts_dir/init_system_audio.sh"

# Start VLC Media Player instances with enabled autostart
systemctl --user start media-player-instances-control@start-auto.service

# Start Chromium browser instances with enabled autostart
systemctl --user start web-browser-instances-control@start-auto.service
