#!/bin/bash
playlist="$defaultPlaylist"
vlc $playlist -f -I dummy \
    --extraintf oldrc --rc-fake-tty --rc-host=127.0.0.1:50000 \
    -V "$videoOutput" -A "$audioOutput" "$playback" \
    --image-duration="$imageDuration" \
    --one-instance --video-on-top --no-video-title-show \
    --global-key-play-pause="Tab" \
    --key-next="Page Up" --key-prev="Page Down"
