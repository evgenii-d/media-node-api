#!/bin/bash
command="$1"
app_dir="$(dirname "$(dirname "$(realpath "$0")")")"
configs_dir="$app_dir/resources/configs/web_browser"

# Check if a command was provided
if [ -z "$command" ]; then
    echo "Command is not provided." >&2
    exit 1
fi

case "${command,,}" in

"autostart")
    echo "Start instances with enabled 'autostart'"

    configs_array=()
    profiles_array=()
    profiles_dir="$HOME/.config/browser-profiles"

    # Fix chromium bug (won't start after changing hostname)
    rm -rf "$HOME/.config/chromium/Singleton*"

    # Gather config filenames
    for c in "$configs_dir"/*.ini; do
        configs_array+=("$(basename "$c" .ini)")
    done

    # Gather profile directory names
    for p in "$profiles_dir"/*; do
        if [[ -d "$p" ]]; then
            profiles_array+=("$(basename "$p")")
        fi
    done

    # Remove profiles that don't have a corresponding config
    for profile in "${profiles_array[@]}"; do
        for config in "${configs_array[@]}"; do
            if [[ "$profile" == "$config" ]]; then
                continue 2 # Match found, skip to the next profile
            fi
        done

        echo "Remove browser profile '$profile'"
        rm -rf "${profiles_dir:?}/$profile"
    done

    # Start instances with enabled 'autostart'
    for file in "$configs_dir"/*; do
        autostart=$(grep "autostart" "$file" |
            cut -d "=" -f2 | tr -d "\r" | xargs)
        uuid=$(grep "uuid" "$file" | cut -d "=" -f2 | tr -d "\r" | xargs)

        if [[ "${autostart^^}" == "TRUE" ]]; then
            echo "'$uuid' - enabled, starting ..."
            if ! systemctl --user start web-browser@"$uuid".service; then
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
        if ! systemctl --user start web-browser@"$uuid".service; then
            echo "Error starting service for instance '$uuid'" >&2
        fi
    done
    ;;

# Default
*)
    echo "Unknown command '$command'"
    ;;
esac
