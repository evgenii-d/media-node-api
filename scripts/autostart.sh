#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"

sleep 10
# Execute xrandr to configure displays
bash "$configs_dir/xrandr.txt"

# Set the system audio device and volume
"$scripts_dir/init_system_audio.sh"

# Start VLC Media Player instances
systemctl --user start media-player-instances-manager@autostart.service

# Start Chromium browser instances
systemctl --user start web-browser-instances-manager@autostart.service
