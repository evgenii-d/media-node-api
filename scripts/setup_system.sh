#!/bin/bash
set -e
lightdm_config_path="/etc/lightdm/lightdm.conf"

echo "[Setup System]"

echo
echo "> Fetch the latest version of the package list and install the updates"
sudo apt update && sudo apt -y upgrade

echo "> Install packages"
sudo apt install -y \
    xserver-xorg \
    openbox \
    accountsservice \
    lightdm \
    pulseaudio \
    network-manager \
    python3-tk \
    ufw \
    chromium \
    vlc

echo "> Change default target to 'graphical.target'"
sudo systemctl set-default graphical.target

echo "> [LightDM] Enable autologin and configure X server command"
