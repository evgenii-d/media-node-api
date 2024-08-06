#!/bin/bash
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"

sleep 10
bash "$configs_dir/xrandr.txt"
"$scripts_dir/init_system_audio.sh"
systemctl --user start media-player-instances-manager@autostart.service
systemctl --user start web-browser-instances-manager@autostart.service
