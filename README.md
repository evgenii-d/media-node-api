# Media Node API

## Installation

Download project

```bash
git clone https://github.com/evgenii-d/media-node-api.git
```

Make scripts executable

```bash
chmod +x ./scripts/*.sh
```

Execute `setup_project.sh`

```bash
./scripts/setup_project.sh
```

Execute `install_service.sh`

```bash
./scripts/install_service.sh
```

Reboot

## System configuration

### Allow command execution without sudo password

Locate the executable files. For example, `shutdown`

```txt
sudo which shutdown
> /usr/sbin/shutdown
```

Modify `/etc/sudoers` with `visudo`

`sudo visudo`

```txt
<USER_NAME> ALL=NOPASSWD: /PATH/TO/shutdown
<USER_NAME> ALL=NOPASSWD: /PATH/TO/hostnamectl
<USER_NAME> ALL=NOPASSWD: /PATH/TO/nmcli
<USER_NAME> ALL=NOPASSWD: /PATH/TO/change_hostname.sh
```

## Software installation

```sh
sudo apt update && sudo apt -y upgrade
sudo apt install -y xserver-xorg openbox accountsservice lightdm \
                    pulseaudio network-manager \
                    python3-tk ufw chromium vlc \
```

### LightDM

#### Enabling LightDM

`sudo systemctl enable lightdm.service`

(Optional) Change default target to boot into

```sh
systemctl get-default
sudo systemctl set-default graphical.target
```

#### Enable autologin and hide cursor

`/etc/lightdm/lightdm.conf`

```txt
...
[Seat:*]
...
xserver-command=X -s 0 dpms :0 -nocursor
...
autologin-user=<USER_NAME>
autologin-user-timeout=0
...
```

#### Change the greeter's background

`/etc/lightdm/lightdm-gtk-greeter.conf`

```txt
...
[greeter]
background=#000000
...
```

### NetworkManager

#### Disable MAC address randomization

`/etc/NetworkManager/conf.d/wifi_rand_mac.conf`

```txt
[device]
wifi.scan-rand-mac-address=no
```

## Raspberry PI4

Enable power button. `GPIO3` by default e.g., physical pins 5 and 6

`/boot/firmware/config.txt`

```txt
dtoverlay=gpio-shutdown
```

## Notes

Static files address: <http://IP_ADDRESS:5000/static/public/>

## Links

### system

<https://wiki.archlinux.org/title/LightDM>

### systemd

<https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html>

<https://wiki.archlinux.org/title/systemd>

### VLC

<https://wiki.videolan.org/VLC_command-line_help/>

<https://wiki.videolan.org/Image/>

<https://wiki.videolan.org/VLC_Features_Formats/>

### Chromium

<https://www.chromium.org/developers/how-tos/run-chromium-with-flags/>
<https://peter.sh/experiments/chromium-command-line-switches/>

### Desktop Entry Specification

<https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#introduction>

### Debian X session

<https://wiki.debian.org/Xsession>
