#!/bin/bash
user_services_dir="$HOME/.config/systemd/user"
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"

# Check for root privileges
if [ "$EUID" -eq 0 ]; then
    echo "Run script without root privileges" >&2
    exit 1
fi

echo "Enable user lingering"
loginctl enable-linger "$(logname)"

echo "Creating directory for services under current user"
mkdir -p "$user_services_dir"

echo "Create systemd user services: "
echo "* Media Node API"
cat <<EOF >"$user_services_dir/media-node-api.service"
[Unit]
Description=Media Node API
After=graphical.target network-online.target
Wants=network-online.target

[Service]
Type=exec
Restart=always
EnvironmentFile=$configs_dir/media_node.ini
ExecStart=$scripts_dir/run_app.sh

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "* VLC Media Player"
cat <<EOF >"$user_services_dir/media-player.service"
[Unit]
Description=VLC Media Player + RC Interface
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/media_player.ini
EnvironmentFile=$configs_dir/playlists.ini
ExecStart=$scripts_dir/run_vlc.sh
ExecStartPost=sleep 3
ExecStartPost=python3 $scripts_dir/vlc_audio.py

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "* Chromium Browser Instance"
cat <<EOF >"$user_services_dir/web-browser@.service"
[Unit]
Description=Chromium Browser. Instance %i
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/web_browser/%i.ini
ExecStart=$scripts_dir/run_web_browser.sh

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "* Chromium Browser Instances Autostart"
cat <<EOF >"$user_services_dir/web-browser-instances-autostart.service"
[Unit]
Description=Chromium Browser Instances Autostart
After=graphical.target

[Service]
ExecStart=$scripts_dir/web_browser_instances_manager.sh autostart

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "* Chromium Browser Instances Starter"
cat <<EOF >"$user_services_dir/web-browser-instances-starter.service"
[Unit]
Description=Start All Chromium Browser Instances
After=graphical.target

[Service]
ExecStart=$scripts_dir/web_browser_instances_manager.sh start-all

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "* Display Detector"
cat <<EOF >"$user_services_dir/display-detector.service"
[Unit]
Description=Display Detector
After=graphical.target

[Service]
Restart=on-failure
ExecStart=python3 $scripts_dir/display_detector.py

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "Enable services: "
echo "* VLC Media Player"
systemctl --user enable media-node-api.service

echo "* Chromium Browser Instances Autostart"
systemctl --user enable web-browser-instances-autostart.service

echo Done
