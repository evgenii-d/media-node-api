#!/bin/bash
set -e
script_dir="$(dirname "$(realpath "$0")")"
lightdm_conf="/etc/lightdm/lightdm.conf"
greeter_conf="/etc/lightdm/lightdm-gtk-greeter.conf"
network_interfaces_conf="/etc/network/interfaces"
packages=(
    xserver-xorg
    openbox
    accountsservice
    lightdm
    pulseaudio
    network-manager
    python3-venv
    python3-tk
    ufw
    chromium
    vlc
)

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root." >&2
    exit 1
fi

echo
echo "[Setup System]"
echo "> Fetch the latest version of the package list and install the updates"
sudo apt update && sudo apt -y upgrade

echo
echo "> Install packages"
for pkg in "${packages[@]}"; do
    sudo apt install -y "$pkg" || echo "Warning: Failed to install $pkg" >&2
done

echo "> Change default target to 'graphical.target'"
sudo systemctl set-default graphical.target

echo
echo "[LightDM]"
if [[ ! -f $lightdm_conf ]]; then
    echo "Error: $lightdm_conf not found!" >&2
    exit 1
fi
# Backup LightDM configuration
if [[ ! -f "$lightdm_conf.bak" ]]; then
    sudo cp $lightdm_conf "$lightdm_conf.bak"
fi

echo "> Configure X server startup"
sed -i 's/#xserver-command=.*$/xserver-command=X -s 0 dpms :0 -nocursor/' \
    $lightdm_conf

echo "> Enable autologin for current user"
sed -i 's/#autologin-user=.*$/autologin-user='"$SUDO_USER"'/' \
    $lightdm_conf
sed -i "s/#autologin-user-timeout=.*$/autologin-user-timeout=0/" \
    $lightdm_conf

echo "> Change the greeter's background"
if [[ ! -f $greeter_conf ]]; then
    echo "Error: $greeter_conf not found!" >&2
    exit 1
fi
# Backup greeter configuration
if [[ ! -f "$greeter_conf.bak" ]]; then
    sudo cp $greeter_conf "$greeter_conf.bak"
fi
sed -i 's/#background=.*$/background=#000000/' $greeter_conf

echo
echo "[NetworkManager]"
if [[ -f $network_interfaces_conf ]]; then
    echo "> Remove configuration from $network_interfaces_conf"
    sudo cp "$network_interfaces_conf" "${network_interfaces_conf}.bak"
    sed -i '/^\s*\(auto\|allow-hotplug\|iface\)/s/^/# /' \
        $network_interfaces_conf
    sed -i '/^\s*#\s*\(auto lo\|allow-hotplug lo\|iface lo\)/s/^\s*#\s*//' \
        $network_interfaces_conf
    sudo systemctl restart NetworkManager
fi

echo "> Disable MAC address randomization"
cat <<EOF >"/etc/NetworkManager/conf.d/wifi_rand_mac.conf"
[device]
wifi.scan-rand-mac-address=no
EOF

echo
echo "[UFW (Uncomplicated Firewall)]"
echo "> Setup UFW default policies"
sudo ufw default deny incoming
sudo ufw default allow outgoing

echo "> Open port 5000"
sudo ufw allow 5000

echo "> Block SSH access"
sudo ufw delete allow ssh

echo "> Enable UFW"
sudo ufw --force enable

echo
echo "[Create Sudoers File for Current User]"
cat <<EOF >"/etc/sudoers.d/$SUDO_USER"
$SUDO_USER ALL=NOPASSWD: $(sudo which hostnamectl)
$SUDO_USER ALL=NOPASSWD: $(sudo which shutdown)
$SUDO_USER ALL=NOPASSWD: $(sudo which nmcli)
$SUDO_USER ALL=NOPASSWD: $(sudo which sed)
$SUDO_USER ALL=NOPASSWD: $script_dir/change_hostname.sh
$SUDO_USER ALL=NOPASSWD: $script_dir/mouse_cursor_control.sh
EOF
sudo chmod 0440 "/etc/sudoers.d/$SUDO_USER"

echo
echo "Warning: SSH access is blocked!"
echo "Ensure you have console access if needed."
echo "System setup complete."
