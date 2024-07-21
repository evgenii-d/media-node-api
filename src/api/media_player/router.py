from typing import Literal
from fastapi import APIRouter, Body, HTTPException

from src.constants import AppDir
from src.core.vlcrc import VLCRemoteControl
from src.core.syscmd import SysCmdExec
from src.api.media_player.config import config_manager, vlc_rc
from src.api.media_player.schemas import ConfigSchema, PlayerControlCommands

router = APIRouter(prefix="/media-player", tags=["media player"])


@router.get("/config", responses={
    200: {"description": "Media player configuration retrieved successfully"}
}, status_code=200)
def player_config() -> ConfigSchema:
    return ConfigSchema.model_validate(config_manager.load_section())


@router.patch("/config", responses={
    204: {"description": "Media player configuration updated successfully"}
}, status_code=204)
def update_player_config(data: ConfigSchema) -> None:
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.post("/service/{command}", responses={
    204: {"description": "Media player service command executed"},
    502: {"description": "Failed to execute media player service command"}
}, status_code=204)
def player_service(command: Literal["start", "stop", "restart"]) -> None:
    args = ["systemctl", "--user", command, "media-player.service"]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")


@router.post("/control/{command}", responses={
    204: {"description": "Media player command executed successfully"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def player_control(command: PlayerControlCommands) -> None:
    if not vlc_rc.exec(command).success:
        raise HTTPException(502, "Media player unavailable")


@router.post("/playlist/goto", responses={
    204: {"description": "Successfully navigated to the playlist index"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def goto_playlist_index(index: int = Body(gt=0)) -> None:
    if not vlc_rc.goto(index):
        raise HTTPException(502, "Media player unavailable")


@router.post("/playlist/clear", responses={
    204: {"description": "Playlist cleared successfully"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def clear_playlist() -> None:
    if not vlc_rc.clear():
        raise HTTPException(502, "Media player unavailable")


@router.get("/playlist/status", responses={
    200: {"description": "Playlist status retrieved successfully"},
    502: {"description": "Failed to retrieve playlist status"}
}, status_code=200)
def playlist_status() -> list[str]:
    response = vlc_rc.status()
    if response.success:
        return [i for i in response.data if "new input:" not in i]
    raise HTTPException(502, "Failed to retrieve playlist status")


@router.post("/playlist/change", responses={
    204: {"description": "Playlist changed successfully"},
    404: {"description": "Playlist not found"},
    502: {"description": "Media player unavailable"}
}, status_code=204)
def change_playlist(playlist_name: str = Body()) -> None:
    playlist = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if not playlist.exists():
        raise HTTPException(404, "Playlist not found")
    if not all(vlc_rc.clear(),  vlc_rc.add(playlist)):
        raise HTTPException(502, "Command execution failed")


@router.get("/audio/volume", responses={
    200: {"description": "Current volume level retrieved successfully"},
    502: {"description": "Media player unavailable"}
}, status_code=200)
def volume_level() -> int:
    value = vlc_rc.get_volume()
    if value == -1:
        raise HTTPException(502, "Media player unavailable")
    return int((value / 320) * 125)


@router.post("/audio/volume", responses={
    204: {"description": "Volume set successfully"},
    502: {"description": "Media player unavailable"},
}, status_code=204)
def set_volume(percent: int = Body(ge=0, le=125)) -> None:
    value = int((percent / 125) * 320)
    if not vlc_rc.set_volume(value):
        raise HTTPException(502, "Media player unavailable")
    data = ConfigSchema(volume=str(value))
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get("/audio/devices", responses={
    200: {"description": "Audio devices retrieved"},
    502: {"description": "Media player unavailable"}
}, status_code=200)
def audio_devices() -> list[VLCRemoteControl.AudioDevice]:
    devices = vlc_rc.get_adev()
    if devices:
        return devices
    raise HTTPException(502, "Media player unavailable")


@router.post("/audio/default-device", responses={
    204: {"description": "Default audio device set successfully"},
    502: {"description": "Media player unavailable"},
}, status_code=204)
def set_default_audio_device(device_id: str = Body()) -> None:
    if not vlc_rc.set_adev(device_id):
        raise HTTPException(502, "Media player unavailable")
    data = ConfigSchema(audioDevice=device_id)
    config_manager.save_section(data.model_dump(exclude_none=True))
