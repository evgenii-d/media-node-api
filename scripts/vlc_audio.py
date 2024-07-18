""" 
Set volume and audio device for a VLC player using the RC interface
"""

import os
import socket


class VLCRemoteControl:
    # pylint: disable=too-few-public-methods
    def __init__(self, host: str, port: int, timeout: float = 0.1) -> None:
        """Initialize VLCRemoteControl.

        Args:
            host (str): Hostname or IP address of the VLC instance.
            port (int): Port number of the VLC RC interface.
            timeout (float, optional): 
                Socket connection timeout in seconds. Defaults to 0.1.
        """
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, command: str) -> bool:
        """Sends a command to the VLC RC interface.

        Args:
            command (str): The command to send.

        Returns:
            bool: 
                True if the command was sent successfully, 
                False otherwise.
        """
        address = (self.host, self.port)
        try:
            with socket.create_connection(address, self.timeout) as rc_socket:
                rc_socket.sendall(str(command).encode() + b"\n")
                rc_socket.shutdown(1)
        except (TimeoutError, ConnectionRefusedError, socket.error):
            return False
        return True


volume = os.getenv("volume")
audio_device = os.getenv("audioDevice")
vlc_rc = VLCRemoteControl("127.0.0.1", 50000)

if volume:
    vlc_rc.send(f"volume {volume}")

if audio_device:
    vlc_rc.send(f"adev {audio_device}")
