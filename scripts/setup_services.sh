#!/bin/bash
set -e
user_services_dir="$HOME/.config/systemd/user"
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
scripts_dir="$app_dir/scripts"
configs_dir="$app_dir/resources/configs"
openbox_autostart="$HOME/.config/openbox/autostart.sh"
xresources_file="$HOME/.Xresources"

if [ "$EUID" -eq 0 ]; then
    echo "Run this script without root privileges." >&2
    exit 1
fi

echo
echo "[Setup Services]"
echo "> Enabling user lingering"
if ! loginctl enable-linger "$USER"; then
    echo "Failed to enable user lingering for $USER" >&2
    exit 1
fi

echo "> Creating directory for user services"
mkdir -p "$user_services_dir"

echo
echo "[Create user services]"
echo "> Media Node API"
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

echo "> VLC Media Player Instance"
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

echo "> VLC Media Player Instances Manager"
cat <<EOF >"$user_services_dir/media-player-instances-control@.service"
[Unit]
Description=VLC Media Player Instances Manager. Command %i
After=graphical.target

[Service]
Type=oneshot
ExecStart=$scripts_dir/media_player_instances_manager.sh %i
EOF

echo "> Chromium Browser Instance"
cat <<EOF >"$user_services_dir/web-browser@.service"
[Unit]
Description=Chromium Browser. Instance %i
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/web_browser/%i.ini
ExecStart=$scripts_dir/run_web_browser.sh
EOF

echo "> Chromium Browser Instances Manager"
cat <<EOF >"$user_services_dir/web-browser-instances-control@.service"
[Unit]
Description=Chromium Browser Instances Manager. Command %i
After=graphical.target

[Service]
Type=oneshot
ExecStart=$scripts_dir/web_browser_instances_control.sh %i
EOF

echo "> Display Detector"
cat <<EOF >"$user_services_dir/display-detector.service"
[Unit]
Description=Display Detector
After=graphical.target

[Service]
Restart=on-failure
ExecStart=python3 $scripts_dir/display_detector.py
EOF

echo "> Enable the Media Node API service"
systemctl --user enable media-node-api.service

echo
echo "[Create Openbox autostart file]"
mkdir -p "$HOME/.config/openbox"
cat <<EOF >"$openbox_autostart"
#!/bin/bash
"$scripts_dir/autostart.sh"
EOF
chmod +x "$openbox_autostart"

echo
echo "[Configure Mouse Cursor]"
echo "> Create .Xresources file"
[ ! -f "$xresources_file" ] && touch "$xresources_file"

echo "> Set mouse cursor size (24)"
# Check if the cursor size exist in .Xresources
if grep -qF "Xcursor.size:" "$xresources_file"; then
    # If cursor size exist, replace the line containing it
    sed -i \
        "s/^Xcursor.size:\s.*$/Xcursor.size: 24/" \
        "$xresources_file"
else
    # If it doesn't exist, add the new line to the end of the file
    echo "Xcursor.size: 24" | tee -a "$xresources_file" >/dev/null
fi

echo
echo "Setup complete."
