from fastapi import APIRouter, Body, HTTPException, Response

from src.constants import AppDir
from src.core.vlcrc import VLCRemoteControl
from src.core.syscmd import SysCmdExec
from src.api.media_player.config import config_manager, vlc_rc
from src.api.media_player.schemas import ConfigSchema

router = APIRouter(prefix="/media-player", tags=["media player"])

service_responses = {
    200: {"description": "Service operation completed"},
    500: {"description": "Service operation failed"}
}

player_responses = {
    200: {"description": "Command executed successfully"},
    503: {"description": "Command execution failed"}
}


@router.get("/config")
def player_config() -> ConfigSchema:
    return ConfigSchema.model_validate(config_manager.load_section())


@router.post("/config")
def set_player_config(data: ConfigSchema) -> Response:
    config_manager.save_section(data.model_dump(exclude_none=True))
    return Response(status_code=200)


@router.post("/start-service", responses={**service_responses})
def start_player() -> Response:
    args = ["systemctl", "--user", "start", "media-player.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 500)


@router.post("/stop-service", responses={**service_responses})
def stop_player() -> Response:
    args = ["systemctl", "--user", "stop", "media-player.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 500)


@router.post("/restart-service", responses={**service_responses})
def restart_player() -> Response:
    args = ["systemctl", "--user", "restart", "media-player.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 500)


@router.post("/play", responses={**player_responses})
def play() -> Response:
    return Response(status_code=200 if vlc_rc.play() else 503)


@router.post("/stop", responses={**player_responses})
def stop() -> Response:
    return Response(status_code=200 if vlc_rc.stop() else 503)


@router.post("/next", responses={**player_responses})
def next_item() -> Response:
    return Response(status_code=200 if vlc_rc.next() else 503)


@router.post("/previous", responses={**player_responses})
def previous_item() -> Response:
    return Response(status_code=200 if vlc_rc.prev() else 503)


@router.post("/goto", responses={**player_responses})
def goto_index(index: int = Body(gt=0)) -> Response:
    return Response(status_code=200 if vlc_rc.goto(index) else 503)


@router.post("/clear", responses={**player_responses})
def clear_playlist() -> Response:
    return Response(status_code=200 if vlc_rc.clear() else 503)


@router.get("/status", responses={
    200: {"description": "Playlist status retrieved successfully"},
    503: {"description": "Failed to retrieve playlist status"}
})
def playlist_status() -> list[str]:
    response = vlc_rc.status()
    if response.success:
        return [i for i in response.data if "new input:" not in i]
    raise HTTPException(503, "Failed to retrieve playlist status")


@router.post("/pause", responses={**player_responses})
def toggle_pause() -> Response:
    return Response(status_code=200 if vlc_rc.pause() else 503)


@router.get("/volume", responses={
    200: {"description": "Current volume level retrieved successfully"},
    503: {"description": "Failed to retrieve volume level"}
})
def volume_level() -> int:
    value = vlc_rc.get_volume()
    if value == -1:
        raise HTTPException(503, "Failed to retrieve volume level")
    return int((value / 320) * 125)


@router.post("/volume", responses={**player_responses})
def set_volume(percent: int = Body(ge=0, le=125)) -> Response:
    value = int((percent / 125) * 320)
    if vlc_rc.set_volume(value):
        data = ConfigSchema(volume=str(value))
        config_manager.save_section(data.model_dump(exclude_none=True))
        return Response(status_code=200)
    return Response(status_code=503)


@router.get("/audio-devices", responses={
    200: {"description": "Audio devices retrieved"},
    503: {"description": "Failed to retrieve audio devices"}
})
def audio_devices() -> list[VLCRemoteControl.AudioDevice]:
    devices = vlc_rc.get_adev()
    if devices:
        return devices
    return Response(status_code=503)


@router.post("/default-audio-device", responses={**player_responses})
def set_default_audio_device(device_id: str = Body()) -> Response:
    if vlc_rc.set_adev(device_id):
        data = ConfigSchema(audioDevice=device_id)
        config_manager.save_section(data.model_dump(exclude_none=True))
        return Response(status_code=200)
    return Response(status_code=503)


@router.post("/change-playlist", responses={
    200: {"description": "Playlist updated successfully"},
    404: {"description": "Playlist not found"},
    503: {"description": "Command execution failed"}
})
def change_playlist(playlist_name: str = Body()) -> Response:
    playlist = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if not playlist.is_file():
        raise HTTPException(404, "Playlist not found")
    if vlc_rc.clear() and vlc_rc.add(playlist):
        return Response(status_code=200)
    raise HTTPException(503, "Command execution failed")
