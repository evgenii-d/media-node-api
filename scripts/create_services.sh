#!/bin/bash
user_services_dir=~/".config/systemd/user"
app_dir="$(dirname "$(dirname "$(realpath $0)")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"

if [ $EUID -eq 0 ]; then
    echo "Run script without root privileges"
    exit 1
fi

echo "Enable user lingering"
loginctl enable-linger "$(logname)"

echo "Creating directory for services under current user"
mkdir -p $user_services_dir

# Create systemd sevices
echo "Add Media Node API Service"
cat <<EOF >$user_services_dir/media-node-api.service
[Unit]
Description=Media Node API
After=network-online.target
Wants=network-online.target

[Service]
Type=exec
Restart=always
EnvironmentFile=$configs_dir/media_node.ini
ExecStart=$scripts_dir/run_app.sh

[Install]
WantedBy=default.target
EOF

echo "Add VLC Media Player Service"
cat <<EOF >$user_services_dir/media-player.service
[Unit]
Description=VLC Media Player + RC Interface
After=graphical.target

[Service]
Restart=on-failure
Environment="DISPLAY=:0"
EnvironmentFile=$configs_dir/media_player.ini
EnvironmentFile=$configs_dir/playlists.ini
ExecStart=$scripts_dir/run_vlc.sh
ExecStartPost=sleep 3
ExecStartPost=python3 $scripts_dir/init_vlc_audio.py

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo "Add Chromium Browser Service"
cat <<EOF >$user_services_dir/web-browser.service
[Unit]
Description=Chromium Browser
After=graphical.target

[Service]
Restart=on-failure
Environment="DISPLAY=:0"
EnvironmentFile=$configs_dir/web_browser.ini
ExecStart=$scripts_dir/run_web_browser.sh

[Install]
WantedBy=graphical.target
WantedBy=default.target
EOF

echo Done
