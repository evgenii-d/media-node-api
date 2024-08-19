#!/bin/bash
command="$1"
lightdm_config_path="/etc/lightdm/lightdm.conf"
xresources_file="/home/$SUDO_USER/.Xresources"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run with root privileges." >&2
    exit 1
fi

# Check if a cursor command was provided
if [ -z "$command" ]; then
    echo "A cursor 'command' is required but was not provided." >&2
    exit 1
fi

case "${command,,}" in

"enable")
    echo "Enable mouse cursor"
    sed -i \
        's/^\(xserver-command\s*=\s*\)\(.*\)$/\1X -s 0 dpms :0/' \
        "$lightdm_config_path"
    ;;

"disable")
    echo "Disable mouse cursor"
    sed -i \
        's/^\(xserver-command\s*=\s*\)\(.*\)$/\1X -s 0 dpms :0 -nocursor/' \
        "$lightdm_config_path"
    ;;

"get-size")
    if [ ! -f "$xresources_file" ]; then
        echo -1
    elif grep -qF "Xcursor.size:" "$xresources_file"; then
        sed -n "s/Xcursor.size: //p" "$xresources_file" | xargs
    else
        echo -1
    fi
    exit 0
    ;;

"set-size")
    # Check if size was provided
    if [ -z "$2" ]; then
        echo "Missing cursor size parameter." >&2
        exit 2
    fi

    echo "Setting mouse cursor size to '$2'"
    # Create .Xresources if it doesn't exist
    if [ ! -f "$xresources_file" ]; then
        sudo -u "$SUDO_USER" touch "$xresources_file"
    fi

    # Check if the cursor size exist in the file
    if grep -qF "Xcursor.size:" "$xresources_file"; then
        # If cursor size exist, replace the line containing it
        sudo -u "$SUDO_USER" sed -i \
            "s/^Xcursor.size:\s.*$/Xcursor.size: $2/" \
            "$xresources_file"
    else
        # If it doesn't exist, add the new line to the end of the file
        echo "Xcursor.size: $2" |
            sudo -u "$SUDO_USER" tee -a "$xresources_file" >/dev/null
    fi
    ;;

*)
    echo "Unknown command '$command'"
    exit 2
    ;;

esac
echo "Reboot the system to apply changes."
