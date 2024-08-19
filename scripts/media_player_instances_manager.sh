#!/bin/bash
command="$1"
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
configs_dir="$app_dir/resources/configs/media_player"

# Check if a command was provided
if [ -z "$command" ]; then
    echo "Command is not provided." >&2
    exit 1
fi

case "${command,,}" in

"autostart")
    echo "Start instances with enabled 'autostart'"

    for file in "$configs_dir"/*; do
        autostart=$(grep "autostart" "$file" |
            cut -d "=" -f2 | tr -d "\r" | xargs)
        uuid=$(grep "uuid" "$file" | cut -d "=" -f2 | tr -d "\r" | xargs)

        if [[ "${autostart,,}" == "true" ]]; then
            echo "'$uuid' - enabled, starting ..."
            if ! systemctl --user start media-player@"$uuid".service; then
                echo "Error starting service for instance '$uuid'" >&2
            fi
        else
            echo "'$uuid' - disabled"
        fi
    done
    ;;

"start-all")
    echo "Start all available instances"

    for config in "$configs_dir"/*.ini; do
        uuid="$(basename "$config" .ini)"

        echo "Start '$uuid' instance"
        if ! systemctl --user start media-player@"$uuid".service; then
            echo "Error starting service for instance '$uuid'" >&2
        fi
    done
    ;;

# Default
*)
    echo "Unknown command '$command'"
    ;;

esac
