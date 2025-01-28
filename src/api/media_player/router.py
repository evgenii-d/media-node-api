from typing import Annotated
from fastapi import APIRouter, HTTPException, Path
from vlcrc import AudioDevice

from src.constants import AppDir, SystemctlCommand
from src.core.syscmd import SysCmdExec
from src.core.configmgr import ConfigManager
from src.api.media_player.schemas import ConfigSchemaUpdate
from src.api.media_player.constants import PlayerControlCommands
from src.api.media_player.service import (
    handle_vlc_exceptions,
    get_player_config,
    vlc_remote_control
)
from src.api.media_player.routes.instances_control.router import (
    router as instances_control
)

COMMON_RESPONSES = {
    404: {"description": "Player instance not found"},
    409: {"description": "Player is paused"},
    502: {"description": "Player unavailable"},
}

router = APIRouter(prefix="/media-player", tags=["media player"])
router.include_router(instances_control)


@router.post(
    "/instances/{instance_uuid}/control/{command}",
    responses={
        204: {"description": "Command executed successfully"},
        404: {"description": "Player instance not found"},
        502: {"description": "Failed to execute command"}
    },
    status_code=204
)
def control_instance_service(
    instance_uuid: str,
    command: SystemctlCommand
) -> None:
    file = AppDir.PLAYER_CONFIGS.value/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Player instance not found")
    args = [
        "systemctl", "--user", command.value,
        f"media-player@{instance_uuid}.service"
    ]
    if not SysCmdExec.run(args).success:
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)


@router.post(
    "/instances/{instance_uuid}/playback-control/{command}",
    responses={
        **COMMON_RESPONSES,
        204: {"description": "Player command executed successfully"}
    },
    status_code=204
)
@handle_vlc_exceptions
def player_playback_control(
    instance_uuid: str,
    command: PlayerControlCommands
) -> None:
    vlc = vlc_remote_control(instance_uuid)
    match command:
        case PlayerControlCommands.PLAY:
            vlc.play()
        case PlayerControlCommands.STOP:
            vlc.stop()
        case PlayerControlCommands.NEXT:
            vlc.next()
        case PlayerControlCommands.PREVIOUS:
            vlc.prev()
        case PlayerControlCommands.PAUSE:
            vlc.pause()


@router.post(
    "/instances/{instance_uuid}/playlist/goto/{index}",
    responses={
        **COMMON_RESPONSES,
        204: {"description": "Successfully navigated to the playlist index"}
    },
    status_code=204
)
@handle_vlc_exceptions
def goto_playlist_index(
    instance_uuid: str,
    index: Annotated[int, Path(gt=0)]
) -> None:
    vlc = vlc_remote_control(instance_uuid)
    vlc.goto(index)


@router.post(
    "/instances/{instance_uuid}/playlist/clear",
    responses={
        **COMMON_RESPONSES,
        204: {"description": "Playlist cleared successfully"}
    },
    status_code=204
)
@handle_vlc_exceptions
def clear_playlist(instance_uuid: str) -> None:
    vlc = vlc_remote_control(instance_uuid)
    vlc.clear()


@router.get(
    "/instances/{instance_uuid}/playlist/status",
    responses={
        **COMMON_RESPONSES,
        200: {"description": "Playlist status retrieved successfully"}
    },
    status_code=200
)
@handle_vlc_exceptions
def playlist_status(instance_uuid: str) -> list[str]:
    vlc = vlc_remote_control(instance_uuid)
    status = vlc.status()
    return [i for i in status if "new input:" not in i]


@router.post(
    "/instances/{instance_uuid}/playlist/change/{playlist_name}",
    responses={
        204: {"description": "Playlist changed successfully"},
        404: {"description": "Player instance or playlist not found"},
        409: {"description": "Player is paused"},
        502: {"description": "Player unavailable"}
    },
    status_code=204
)
@handle_vlc_exceptions
def change_playlist(instance_uuid: str, playlist_name: str) -> None:
    playlist = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if not playlist.exists():
        raise HTTPException(404, "Playlist not found")

    vlc = vlc_remote_control(instance_uuid)
    vlc.clear()
    vlc.add(playlist)


@router.get(
    "/instances/{instance_uuid}/audio/volume",
    responses={
        **COMMON_RESPONSES,
        200: {"description": "Current volume level retrieved successfully"},
        500: {"description": "Failed to retrieve volume level"}
    },
    status_code=200
)
@handle_vlc_exceptions
def volume_level(instance_uuid: str) -> int:
    vlc = vlc_remote_control(instance_uuid)
    value = vlc.get_volume()
    if value == -1:
        raise HTTPException(500, "Failed to retrieve volume level")
    return value


@router.post(
    "/instances/{instance_uuid}/audio/volume/{level}",
    responses={
        **COMMON_RESPONSES,
        204: {"description": "Volume set successfully"}
    },
    status_code=204
)
@handle_vlc_exceptions
def set_volume(
    instance_uuid: str,
    level: Annotated[int, Path(ge=0, le=320)]
) -> None:
    config_path = get_player_config(instance_uuid)
    vlc = vlc_remote_control(instance_uuid)
    vlc.set_volume(level)
    data = ConfigSchemaUpdate(volume=level).model_dump(exclude_none=True)
    ConfigManager(config_path).save_section(data)


@router.get(
    "/instances/{instance_uuid}/audio/devices",
    responses={
        **COMMON_RESPONSES,
        200: {"description": "Audio devices retrieved"}
    },
    status_code=200
)
@handle_vlc_exceptions
def audio_devices(instance_uuid: str) -> list[AudioDevice]:
    vlc = vlc_remote_control(instance_uuid)
    return vlc.get_adev()


@router.post(
    "/instances/{instance_uuid}/audio/devices/default/{device_id}",
    responses={
        **COMMON_RESPONSES,
        204: {"description": "Default audio device set successfully"}
    },
    status_code=204
)
@handle_vlc_exceptions
def set_default_audio_device(instance_uuid: str, device_id: str) -> None:
    config_path = get_player_config(instance_uuid)
    vlc = vlc_remote_control(instance_uuid)
    vlc.set_adev(device_id)
    data = ConfigSchemaUpdate(
        audioDevice=device_id
    ).model_dump(exclude_none=True)
    ConfigManager(config_path).save_section(data)
