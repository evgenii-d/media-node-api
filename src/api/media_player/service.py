import pathlib
from fastapi import HTTPException

from src.core.vlcrc import VLCRemoteControl
from src.core.configmgr import ConfigManager
from src.api.media_player.config import configs_dir
from src.api.media_player.schemas import ConfigFileSchema


def get_player_config(instance_uuid: str) -> pathlib.Path:
    file_path = configs_dir/f"{instance_uuid}.ini"
    if file_path.exists():
        return file_path
    raise HTTPException(404, "Player instance not found")


def vlc_remote_control(instance_uuid: str) -> VLCRemoteControl:
    config_path = get_player_config(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    return VLCRemoteControl("127.0.0.1", config.rcPort)
