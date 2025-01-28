from pathlib import Path
from functools import wraps
from fastapi import HTTPException
from vlcrc import VLCRemoteControl, PausedPlayerError

from src.constants import AppDir
from src.core.configmgr import ConfigManager
from src.api.media_player.schemas import ConfigFileSchema


def handle_vlc_exceptions(func):
    """Decorator to handle exceptions raised by VLC Remote control.

    Args:
        func (Callable): The function to be wrapped.

    Raises:
        HTTPException: 
            502: If a `ConnectionError` occurs, indicating the player is unavailable.
            409: If a `PausedPlayerError` occurs, indicating the player is paused.

    Returns:
        Callable: The wrapped function with exception handling applied.
    """
    # Preserves the metadata of the wrapped function
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Call the original function
            return func(*args, **kwargs)
        except ConnectionError as e:
            # Handle a ConnectionError by raising an HTTP 502 error
            raise HTTPException(502, "Player unavailable") from e
        except PausedPlayerError as e:
            # Handle a PausedPlayerError by raising an HTTP 409 error
            raise HTTPException(409, "Player is paused") from e
    # Return the wrapped function
    return wrapper


def get_player_config(instance_uuid: str) -> Path:
    """Retrieve the configuration file path for a player instance.

    Args:
        instance_uuid (str): Unique identifier of the player instance.

    Raises:
        HTTPException: The configuration file does not exist.

    Returns:
        Path: Path to the configuration file.
    """
    file_path = AppDir.PLAYER_CONFIGS.value/f"{instance_uuid}.ini"
    if file_path.exists():
        return file_path
    raise HTTPException(404, "Player instance not found")


def vlc_remote_control(instance_uuid: str) -> VLCRemoteControl:
    """Initialize a VLC remote control instance.

    Args:
        instance_uuid (str): Unique identifier of the player instance.

    Returns:
        VLCRemoteControl: A remote control object for managing VLC.
    """
    config_path = get_player_config(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    return VLCRemoteControl("127.0.0.1", config.rcPort)
