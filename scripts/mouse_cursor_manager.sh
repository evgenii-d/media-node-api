#!/bin/bash
command="$1"
lightdm_config_path="/etc/lightdm/lightdm.conf"
xresources_file="/home/$SUDO_USER/.Xresources"

# Check if a cursor command was provided
if [ -z "$command" ]; then
    echo "A cursor 'command' is required but was not provided." >&2
    exit 1
fi

case "${command,,}" in

# Show mouse cursor
"show")
    sudo sed -i \
        's/^\(xserver-command\s*=\s*\)\(.*\)$/\1X -s 0 dpms :0/' \
        "$lightdm_config_path"
    ;;

# Hide mouse cursor
"hide")
    sudo sed -i \
        's/^\(xserver-command\s*=\s*\)\(.*\)$/\1X -s 0 dpms :0 -nocursor/' \
        "$lightdm_config_path"
    ;;

# Get mouse cursor size
"get-size")
    if [ ! -f "$xresources_file" ]; then
        echo -1
    elif grep -qF "Xcursor.size:" "$xresources_file"; then
        sudo sed -n "s/Xcursor.size: //p" "$xresources_file" | xargs
    else
        echo -1
    fi
    exit 0
    ;;

# Set mouse cursor size
"set-size")
    # Check if size was provided
    if [ -z "$2" ]; then
        echo "Missing cursor size parameter." >&2
        exit 2
    fi

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
