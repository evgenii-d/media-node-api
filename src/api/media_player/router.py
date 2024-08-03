from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, Body, HTTPException

from src.constants import AppDir, SystemctlCommand
from src.core.vlcrc import VLCRemoteControl
from src.core.syscmd import SysCmdExec
from src.core.filesys import get_dir_files
from src.core.configmgr import ConfigManager
from src.api.media_player.constants import PlayerControlCommands
from src.api.media_player.schemas import (ConfigFileSchema, ConfigSchemaIn,
                                          ConfigSchemaOut, ConfigSchemaUpdate)

router = APIRouter(prefix="/media-player", tags=["media player"])
player_configs = AppDir.CONFIGS.value/"media_player"
player_configs.mkdir(exist_ok=True)


def get_config_path(instance_uuid: str) -> Path:
    file_path = player_configs/f"{instance_uuid}.ini"
    if file_path.exists():
        return file_path
    raise HTTPException(404, "Player instance not found")


@router.get("/instances", responses={
    200: {"description": "Player instances retrieved successfully"},
    404: {"description": "No player instances found"}
}, status_code=200)
def player_instances() -> list[ConfigSchemaOut]:
    files = get_dir_files(player_configs)
    if not files:
        raise HTTPException(404, "No player instances found")

    instances = []
    for file in files:
        data = ConfigManager(player_configs/file).load_section()
        config = ConfigSchemaOut(**data)
        config.playlist = Path(config.playlist).stem
        instances.append(config)
    return instances


@router.post("/instances", responses={
    201: {"description": "Player instance created successfully"}
}, status_code=201)
def create_player_instance(data: ConfigSchemaIn) -> ConfigSchemaOut:
    port = 50000
    ports: list[int] = []

    # Extract port numbers from player configuration files
    for file in player_configs.iterdir():
        value = ConfigSchemaOut(**ConfigManager(file).load_section()).rcPort
        ports.append(value)

    # If there are any missing ports, use the smallest missing port.
    # Otherwise, use the next available port number after the highest.
    if ports:
        ports_range = list(range(min(ports), max(ports) + 1))
        missing_ports = list(set(ports_range) - set(ports))
        port = min(missing_ports) if missing_ports else max(ports) + 1

    new_config_path = player_configs/f"{uuid4().hex}.ini"
    new_config = ConfigFileSchema(
        **data.model_dump(),
        rcPort=port,
        uuid=new_config_path.stem
    )
    ConfigManager(new_config_path).save_section(new_config.model_dump())
    return ConfigSchemaOut(**new_config.model_dump())


@router.patch("/instances/{instance_uuid}", responses={
    204: {"description": "Player instance updated successfully"},
    404: {"description": "Player instance not found"}
}, status_code=204)
def update_player_instance(instance_uuid: str,
                           data: ConfigSchemaUpdate) -> None:
    file = player_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Player instance not found")
    ConfigManager(file).save_section(data.model_dump(exclude_none=True))


@router.delete("/instances/{instance_uuid}", responses={
    204: {"description": "Player instance deleted successfully"},
    404: {"description": "Player instance not found"}
}, status_code=204)
def delete_player_instance(instance_uuid: str) -> None:
    file = player_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Player instance not found")
    file.unlink()


@router.post("/instances/manager/{command}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Failed to execute command"}
}, status_code=204)
def manage_player_instances(command: SystemctlCommand) -> None:
    args = ["systemctl", "--user"]
    match command:
        case SystemctlCommand.START:
            args.extend(["start",
                         "media-player-instances-manager@start-all.service"])
        case _:
            args.extend([command.value, "media-player@*.service"])
    if not SysCmdExec.run(args).success:
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)


@router.post("/{instance_uuid}/service/{command}", responses={
    204: {"description": "Command executed successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Failed to execute command"}
}, status_code=204)
def command_player_service(instance_uuid: str,
                           command: SystemctlCommand) -> None:
    file = player_configs/f"{instance_uuid}.ini"
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
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    if not vlcrc.exec(command.value).success:
        raise HTTPException(502, "Media player unavailable")


@router.post("/{instance_uuid}/playlist/goto", responses={
    204: {"description": "Successfully navigated to the playlist index"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def goto_playlist_index(instance_uuid: str, index: int = Body(gt=0)) -> None:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    if not vlcrc.goto(index):
        raise HTTPException(502, "Media player unavailable")


@router.post("/{instance_uuid}/playlist/clear", responses={
    204: {"description": "Playlist cleared successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def clear_playlist(instance_uuid: str) -> None:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    if not vlcrc.clear():
        raise HTTPException(502, "Media player unavailable")


@router.get("/{instance_uuid}/playlist/status", responses={
    200: {"description": "Playlist status retrieved successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Failed to retrieve playlist status"}
}, status_code=200)
def playlist_status(instance_uuid: str) -> list[str]:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    response = vlcrc.status()
    if response.success:
        return [i for i in response.data if "new input:" not in i]
    raise HTTPException(502, "Failed to retrieve playlist status")


@router.post("/{instance_uuid}/playlist/change", responses={
    204: {"description": "Playlist changed successfully"},
    404: {"description": "Player instance or playlist not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def change_playlist(instance_uuid: str, playlist_name: str = Body()) -> None:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    playlist = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if not playlist.exists():
        raise HTTPException(404, "Playlist not found")

    if not all(vlcrc.clear(),  vlcrc.add(playlist)):
        raise HTTPException(502, "Command execution failed")


@router.get("/{instance_uuid}/audio/volume", responses={
    200: {"description": "Current volume level retrieved successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=200)
def volume_level(instance_uuid: str) -> int:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    value = vlcrc.get_volume()
    if value == -1:
        raise HTTPException(502, "Media player unavailable")
    return value


@router.post("/{instance_uuid}/audio/volume", responses={
    204: {"description": "Volume set successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"},
}, status_code=204)
def set_volume(instance_uuid: str, value: int = Body(ge=0, le=320)) -> None:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    if not vlcrc.set_volume(value):
        raise HTTPException(502, "Media player unavailable")
    data = ConfigSchemaUpdate(volume=value).model_dump(exclude_none=True)
    ConfigManager(config_path).save_section(data)


@router.get("/{instance_uuid}/audio/devices", responses={
    200: {"description": "Audio devices retrieved"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"}
}, status_code=200)
def audio_devices(instance_uuid: str) -> list[VLCRemoteControl.AudioDevice]:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    devices = vlcrc.get_adev()
    if devices:
        return devices
    raise HTTPException(502, "Media player unavailable")


@router.post("/{instance_uuid}/audio/devices/default", responses={
    204: {"description": "Default audio device set successfully"},
    404: {"description": "Player instance not found"},
    502: {"description": "Media player unavailable"},
}, status_code=204)
def set_default_audio_device(instance_uuid: str,
                             device_id: str = Body()) -> None:
    config_path = get_config_path(instance_uuid)
    config = ConfigFileSchema(**ConfigManager(config_path).load_section())
    vlcrc = VLCRemoteControl("127.0.0.1", config.rcPort)

    if not vlcrc.set_adev(device_id):
        raise HTTPException(502, "Media player unavailable")
    data = ConfigSchemaUpdate(
        audioDevice=device_id
    ).model_dump(exclude_none=True)
    ConfigManager(config_path).save_section(data)
