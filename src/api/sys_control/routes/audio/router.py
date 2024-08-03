import re
from fastapi import APIRouter, Body, HTTPException

from src.core.syscmd import SysCmdExec
from src.api.sys_control.config import config_manager
from src.api.sys_control.schemas import ConfigSchema, AudioDeviceSchema

router = APIRouter(prefix="/audio")


@router.get("/devices", responses={
    200: {"description": "Audio devices retrieved successfully"},
    502: {"description": "Failed to retrieve audio devices"}
}, status_code=200)
def audio_devices() -> list[AudioDeviceSchema]:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    result = []
    devices = re.findall(r"index: (\d+)\n.*name: <(.*)>", command.output)
    try:
        for d in devices:
            result.append(AudioDeviceSchema(id=int(d[0]), name=d[1]))
    except IndexError as e:
        raise HTTPException(502, "Failed to retrieve audio devices") from e
    return result


@router.get("/devices/default", responses={
    200: {"description": "Default Audio device retrieved successfully"},
    502: {"description": "Failed to retrieve default audio device"}
}, status_code=200)
def default_audio_device() -> AudioDeviceSchema:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    device = re.search(r"\* index: (\d+)\n.*name: <(.+)>", command.output)
    try:
        device_id, device_name = int(device.group(1)), device.group(2)
        return AudioDeviceSchema(id=device_id, name=device_name)
    except (IndexError, AttributeError) as e:
        message = "Failed to retrieve default audio device"
        raise HTTPException(502, message) from e


@router.post("/devices/default", responses={
    204: {"description": "Default audio device set successfully"},
    502: {"description": "Command execution failed"}
}, status_code=204)
def set_default_audio_device(device: str = Body()) -> None:
    command = SysCmdExec.run(["pacmd", "set-default-sink", device])
    if not command.success:
        raise HTTPException(502, "Command execution failed")
    data = ConfigSchema(audioDevice=device)
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get("/volume", responses={
    200: {"description": "Current audio volume retrieved successfully"},
    502: {"description": "Failed to retrieve current audio volume"}
}, status_code=200)
def audio_volume() -> int:
    command = SysCmdExec.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    if not command.success:
        raise HTTPException(502, "Failed to retrieve current audio volume")
    volume_level = int(command.output.strip().split()[4][:-1])
    return volume_level


@router.post("/volume", responses={
    204: {"description": "Audio volume set successfully"},
    502: {"description": "Failed to set audio volume"}
}, status_code=204)
def set_audio_volume(level: int = Body(ge=0, le=150)) -> None:
    args = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"]
    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(502, "Failed to set audio volume")
    data = ConfigSchema(volume=level)
    config_manager.save_section(data.model_dump(exclude_none=True))
