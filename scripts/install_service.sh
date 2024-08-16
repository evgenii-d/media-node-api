#!/bin/bash
user_services_dir="$HOME/.config/systemd/user"
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"
openbox_autostart="$HOME/.config/openbox/autostart.sh"

# Check for root privileges
if [ "$EUID" -eq 0 ]; then
    echo "Run script without root privileges" >&2
    exit 1
fi

echo "[Install Service]"

echo
echo "> Enabling user lingering"
loginctl enable-linger "$(logname)"

echo "> Creating directory for user services"
mkdir -p "$user_services_dir"

echo "> Creating systemd user services"
echo " + Media Node API"
cat <<EOF >"$user_services_dir/media-node-api.service"
[Unit]
Description=Media Node API
After=network-online.target
Wants=network-online.target

[Service]
Restart=always
Environment="DISPLAY=:0"
ExecStart=$scripts_dir/run_app.sh

[Install]
WantedBy=default.target
EOF

echo " + VLC Media Player Instance"
cat <<EOF >"$user_services_dir/media-player@.service"
[Unit]
Description=VLC Media Player + RC Interface. Instance %i
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/media_player/%i.ini
ExecStart=$scripts_dir/run_media_player.sh
ExecStartPost=sleep 5
ExecStartPost=python3 $scripts_dir/init_media_player_audio.py
EOF

echo " + VLC Media Player Instances Manager"
cat <<EOF >"$user_services_dir/media-player-instances-manager@.service"
[Unit]
Description=VLC Media Player Instances Manager. Command %i
After=graphical.target

[Service]
Type=oneshot
ExecStart=$scripts_dir/media_player_instances_manager.sh %i
EOF

echo " + Chromium Browser Instance"
cat <<EOF >"$user_services_dir/web-browser@.service"
[Unit]
Description=Chromium Browser. Instance %i
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/web_browser/%i.ini
ExecStart=$scripts_dir/run_web_browser.sh
EOF

echo " + Chromium Browser Instances Manager"
cat <<EOF >"$user_services_dir/web-browser-instances-manager@.service"
[Unit]
Description=Chromium Browser Instances Manager. Command %i
After=graphical.target

[Service]
Type=oneshot
ExecStart=$scripts_dir/web_browser_instances_manager.sh %i
EOF

echo " + Display Detector"
cat <<EOF >"$user_services_dir/display-detector.service"
[Unit]
Description=Display Detector
After=graphical.target

[Service]
Restart=on-failure
ExecStart=python3 $scripts_dir/display_detector.py
EOF

echo "> Enabling the Media Node API service"
systemctl --user enable media-node-api.service

echo "> Creating an Openbox autostart file and adding commands"
echo " + Executing xrandr at startup to configure displays"
echo " + Setting the system audio device and volume at startup"
echo " + Autostarting VLC Media Player instances"
echo " + Autostarting Chromium browser instances"

mkdir -p "$HOME/.config/openbox"
cat <<EOF >"$openbox_autostart"
#!/bin/bash
"$scripts_dir/autostart.sh"
EOF
chmod +x "$openbox_autostart"

echo
echo Done
