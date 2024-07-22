#!/bin/bash
# Fix chromium bug (won't start after changing hostname)
rm -rf ~/.config/chromium/Singleton*

chromium --autoplay-policy=no-user-gesture-required --no-session-restore \
    --disable-cache --disk-cache-size=1 --disk-cache-dir=/dev/null \
    --kiosk $url
