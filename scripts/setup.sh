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

echo
echo "Enable user lingering"
loginctl enable-linger "$(logname)"

echo
echo "Create directory for user services"
mkdir -p "$user_services_dir"

echo
echo "Create systemd user services:"
echo "+ Media Node API"
cat <<EOF >"$user_services_dir/media-node-api.service"
[Unit]
Description=Media Node API
After=network-online.target
Wants=network-online.target

[Service]
Type=exec
Restart=always
Environment="DISPLAY=:0"
EnvironmentFile=$configs_dir/sys_control.ini
ExecStart=$scripts_dir/run_app.sh

[Install]
WantedBy=default.target
EOF

echo "+ VLC Media Player Instance"
cat <<EOF >"$user_services_dir/media-player@.service"
[Unit]
Description=VLC Media Player + RC Interface. Instance %i
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/media_player/%i.ini
ExecStart=$scripts_dir/run_media_player.sh
ExecStartPost=sleep 5
ExecStartPost=python3 $scripts_dir/media_player_audio.py
EOF

echo "+ VLC Media Player Instances Manager"
cat <<EOF >"$user_services_dir/media-player-instances-manager@.service"
[Unit]
Description=VLC Media Player Instances Manager. Command %i
After=graphical.target

[Service]
Type=oneshot
ExecStart=$scripts_dir/media_player_instances_manager.sh %i
EOF

echo "+ Chromium Browser Instance"
cat <<EOF >"$user_services_dir/web-browser@.service"
[Unit]
Description=Chromium Browser. Instance %i
After=graphical.target

[Service]
Restart=on-failure
EnvironmentFile=$configs_dir/web_browser/%i.ini
ExecStart=$scripts_dir/run_web_browser.sh
EOF

echo "+ Chromium Browser Instances Manager"
cat <<EOF >"$user_services_dir/web-browser-instances-manager@.service"
[Unit]
Description=Chromium Browser Instances Manager. Command %i
After=graphical.target

[Service]
Type=oneshot
ExecStart=$scripts_dir/web_browser_instances_manager.sh %i
EOF

echo "+ Display Detector"
cat <<EOF >"$user_services_dir/display-detector.service"
[Unit]
Description=Display Detector
After=graphical.target

[Service]
Restart=on-failure
ExecStart=python3 $scripts_dir/display_detector.py
EOF

echo
echo "Enable Media Node API service"
systemctl --user enable media-node-api.service

echo
echo "Create openbox autostart file: "
echo "+ xrandr execution to configure displays"
echo "+ Set system audio device and volume"
echo "+ VLC Media Player Instances Autostart"
echo "+ Chromium Browser Instances Autostart"

mkdir -p "$HOME/.config/openbox"
cat <<EOF >"$openbox_autostart"
#!/bin/bash
sleep 10 && bash $configs_dir/xrandr.txt &
$scripts_dir/system_audio.sh
systemctl --user start media-player-instances-manager@autostart.service
systemctl --user start web-browser-instances-manager@autostart.service
EOF
chmod +x "$openbox_autostart"

echo
echo Done
