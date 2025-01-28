""" 
Set volume and audio device for a VLC player.
"""

import os

from vlcrc import VLCRemoteControl


def main():
    volume = os.getenv("volume")
    audio_device = os.getenv("audioDevice")
    rc_port = os.getenv("rcPort")
    vlcrc = VLCRemoteControl("127.0.0.1", int(rc_port))

    if not rc_port:
        return

    if volume:
        vlcrc.set_volume(volume)

    if audio_device:
        vlcrc.set_adev(audio_device)


if __name__ == "__main__":
    main()
