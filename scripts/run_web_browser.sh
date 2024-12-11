#!/bin/bash
# shellcheck disable=SC2154
# Environment Variables: uuid, position, url
profile_dir="$HOME/.config/browser-profiles/$uuid"

rm -rf "$profile_dir"
mkdir -p "$profile_dir"

chromium --autoplay-policy=no-user-gesture-required --no-session-restore \
    --disable-cache --disk-cache-size=1 --disk-cache-dir=/dev/null \
    --window-position="$position" \
    --user-data-dir="$profile_dir" \
    --kiosk "$url"
