#!/bin/bash
# Environment Variables: hotkeys, interface
main_options=(
    "$playlist"
    -f
    -V "$videoOutput"
    -A "$audioOutput"
)

playlist_options=(
    "$playback"
    --no-interact
    --no-stats
)

extraintf_options=(
    --extraintf oldrc
    --rc-fake-tty
    --rc-host=127.0.0.1:"$rcPort"
)

qt_options=(
    --qt-notification=0
    --no-qt-name-in-title
    --no-qt-fs-controller
    --qt-continue=0
    --no-qt-error-dialogs
    --no-qt-privacy-ask
    --qt-minimal-view
    --no-qt-bgcone
    --qt-fullscreen-screennumber="$screenNumber"
)

misc_options=(
    --video-on-top
    --no-video-title-show
    --image-duration="$imageDuration"
    --meta-title=
)

# shellcheck disable=SC2154
if [[ "${hotkeys,,}" == "true" ]]; then
    hotkeys_options=(
        --global-key-play-pause="Tab"
        --key-next="Page Up"
        --key-prev="Page Down"
    )
fi

# shellcheck disable=SC2154
case "${interface,,}" in

"dummy")
    main_options+=('-I dummy')
    ;;

*)
    main_options+=('-I qt')
    main_options=("${main_options[@]}" "${qt_options[@]}")
    ;;

esac

vlc "${main_options[@]}" \
    "${playlist_options[@]}" \
    "${extraintf_options[@]}" \
    "${misc_options[@]}" \
    "${hotkeys_options[@]}"
