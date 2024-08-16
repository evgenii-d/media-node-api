from typing import Annotated
from fastapi import APIRouter, HTTPException, Path

from src.constants import AppDir, SystemctlCommand
from src.core.vlcrc import VLCRemoteControl
from src.core.syscmd import SysCmdExec
from src.core.configmgr import ConfigManager
from src.api.media_player.config import PLAYER_CONFIGS
from src.api.media_player.schemas import ConfigSchemaUpdate
from src.api.media_player.service import get_player_config, vlc_remote_control
from src.api.media_player.constants import PlayerControlCommands
from src.api.media_player.routes.instances_control.router import (
    router as instances_control
)

router = APIRouter(prefix="/media-player", tags=["media player"])
router.include_router(instances_control)


@router.post("/{instance_uuid}/service/{command}", responses={
    204: {"description": "Command executed successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Failed to execute command"}
}, status_code=204)
def command_player_service(instance_uuid: str,
                           command: SystemctlCommand) -> None:
    file = PLAYER_CONFIGS/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Player instance not found")
    args = ["systemctl", "--user", command.value,
            f"media-player@{instance_uuid}.service"]
    if not SysCmdExec.run(args).success:
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)


@router.post("/{instance_uuid}/control/{command}", responses={
    204: {"description": "Media player command executed successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def player_control(instance_uuid: str,
                   command: PlayerControlCommands) -> None:
    vlcrc = vlc_remote_control(instance_uuid)
    if not vlcrc.exec(command.value).success:
        raise HTTPException(502, "Media player unavailable")


@router.post("/{instance_uuid}/playlist/goto/{index}", responses={
    204: {"description": "Successfully navigated to the playlist index"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def goto_playlist_index(instance_uuid: str,
                        index: Annotated[int, Path(gt=0)]) -> None:
    vlcrc = vlc_remote_control(instance_uuid)
    if not vlcrc.goto(index):
        raise HTTPException(502, "Media player unavailable")


@router.post("/{instance_uuid}/playlist/clear", responses={
    204: {"description": "Playlist cleared successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def clear_playlist(instance_uuid: str) -> None:
    vlcrc = vlc_remote_control(instance_uuid)
    if not vlcrc.clear():
        raise HTTPException(502, "Media player unavailable")


@router.get("/{instance_uuid}/playlist/status", responses={
    200: {"description": "Playlist status retrieved successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Failed to retrieve playlist status"}
}, status_code=200)
def playlist_status(instance_uuid: str) -> list[str]:
    vlcrc = vlc_remote_control(instance_uuid)
    response = vlcrc.status()
    if response.success:
        return [i for i in response.data if "new input:" not in i]
    raise HTTPException(502, "Failed to retrieve playlist status")


@router.post(
    "/{instance_uuid}/playlist/change/{playlist_name}",
    responses={
        204: {"description": "Playlist changed successfully"},
        404: {"description": "Player instance or playlist not found"},
        502: {"description": "Media player unavailable"}
    }, status_code=204)
def change_playlist(instance_uuid: str, playlist_name: str) -> None:
    vlcrc = vlc_remote_control(instance_uuid)
    playlist = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if not playlist.exists():
        raise HTTPException(404, "Playlist not found")

    if not all([vlcrc.clear(),  vlcrc.add(playlist)]):
        raise HTTPException(502, "Command execution failed")


@router.get("/{instance_uuid}/audio/volume", responses={
    200: {"description": "Current volume level retrieved successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=200)
def volume_level(instance_uuid: str) -> int:
    vlcrc = vlc_remote_control(instance_uuid)
    value = vlcrc.get_volume()
    if value == -1:
        raise HTTPException(502, "Media player unavailable")
    return value


@router.post("/{instance_uuid}/audio/volume/{level}", responses={
    204: {"description": "Volume set successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"},
}, status_code=204)
def set_volume(instance_uuid: str,
               level: Annotated[int, Path(ge=0, le=320)]) -> None:
    config_path = get_player_config(instance_uuid)
    vlcrc = vlc_remote_control(instance_uuid)
    if not vlcrc.set_volume(level):
        raise HTTPException(502, "Media player unavailable")
    data = ConfigSchemaUpdate(volume=level).model_dump(exclude_none=True)
    ConfigManager(config_path).save_section(data)


@router.get("/{instance_uuid}/audio/devices", responses={
    200: {"description": "Audio devices retrieved"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=200)
def audio_devices(instance_uuid: str) -> list[VLCRemoteControl.AudioDevice]:
    vlcrc = vlc_remote_control(instance_uuid)
    devices = vlcrc.get_adev()
    if devices:
        return devices
    raise HTTPException(502, "Media player unavailable")


@router.post("/{instance_uuid}/audio/devices/default/{device_id}", responses={
    204: {"description": "Default audio device set successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"},
}, status_code=204)
def set_default_audio_device(instance_uuid: str, device_id: str) -> None:
    config_path = get_player_config(instance_uuid)
    vlcrc = vlc_remote_control(instance_uuid)
    if not vlcrc.set_adev(device_id):
        raise HTTPException(502, "Media player unavailable")
    data = ConfigSchemaUpdate(
        audioDevice=device_id
    ).model_dump(exclude_none=True)
    ConfigManager(config_path).save_section(data)
