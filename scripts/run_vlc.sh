#!/bin/bash

vlc "$defaultPlaylist" -f -I qt \
    -V "$videoOutput" -A "$audioOutput" "$playback" \
    --qt-fullscreen-screennumber="$screen" \
    --qt-minimal-view --no-qt-bgcone \
    --extraintf oldrc --rc-fake-tty --rc-host=127.0.0.1:50000 \
    --image-duration="$imageDuration" \
    --one-instance --video-on-top --no-video-title-show \
    --meta-title="" \
    --global-key-play-pause="Tab" \
    --key-next="Page Up" --key-prev="Page Down"
