import re
from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException, Path

from src.core.syscmd import SysCmdExec
from src.api.system_control.config import config_manager
from src.api.system_control.schemas import ConfigSchema
from src.api.system_control.routes.audio.schemas import AudioDeviceSchema

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get(
    "/devices",
    responses={
        200: {"description": "Audio devices retrieved successfully"},
        404: {"description": "Audio devices not found"},
        502: {"description": "Failed to retrieve audio devices"}
    },
    status_code=200
)
def list_audio_devices() -> list[AudioDeviceSchema]:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(502, "Failed to retrieve audio devices")

    result = []
    devices = re.findall(r"index: (\d+)\n.*name: <(.*)>", command.output)
    try:
        for d in devices:
            result.append(AudioDeviceSchema(id=int(d[0]), name=d[1]))
    except IndexError as e:
        raise HTTPException(502, "Failed to retrieve audio devices") from e

    if result:
        return result
    raise HTTPException(404, "Audio devices not found")


@router.get(
    "/devices/default",
    responses={
        200: {"description": "Default Audio device retrieved successfully"},
        502: {"description": "Failed to retrieve default audio device"}
    },
    status_code=200
)
def default_audio_device() -> AudioDeviceSchema:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(502, "Failed to retrieve default audio device")

    device = re.search(r"\* index: (\d+)\n.*name: <(.+)>", command.output)
    try:
        device_id, device_name = int(device.group(1)), device.group(2)
        return AudioDeviceSchema(id=device_id, name=device_name)
    except (IndexError, AttributeError) as e:
        message = "Failed to retrieve default audio device"
        raise HTTPException(502, message) from e


@router.post(
    "/devices/{device}/default",
    responses={
        204: {"description": "Default audio device set successfully"},
        502: {"description": "Failed to set default audio device"}
    },
    status_code=204
)
def set_default_audio_device(device: str) -> None:
    command = SysCmdExec.run(["pacmd", "set-default-sink", device])
    if not command.success:
        raise HTTPException(502, "Failed to set default audio device")
    data = ConfigSchema(audioDevice=device)
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.post(
    "/devices/{device}/mute",
    responses={
        204: {"description": "Mute state changed successfully"},
        502: {"description": "Failed to execute the command"}
    },
    status_code=204
)
def mute_audio_device(device: str, value: Literal["true", "false"]) -> None:
    command = SysCmdExec.run(["pactl", "set-sink-mute", device, value])
    if not command.success:
        raise HTTPException(502, "Failed to execute the command")


@router.get(
    "/devices/{device}/volume",
    responses={
        200: {"description": "Current audio volume retrieved successfully"},
        502: {"description": "Failed to retrieve current audio volume"}
    },
    status_code=200
)
def get_audio_volume(device: str) -> int:
    command = SysCmdExec.run(["pactl", "get-sink-volume", device])
    if not command.success:
        raise HTTPException(502, "Failed to retrieve current audio volume")
    volume_level = int(command.output.strip().split()[4][:-1])
    return volume_level


@router.post(
    "/devices/{device}/volume/{level}",
    responses={
        204: {"description": "Audio volume set successfully"},
        502: {"description": "Failed to set audio volume"}
    },
    status_code=204
)
def set_audio_volume(
    device: str,
    level: Annotated[int, Path(ge=0, le=150)]
) -> None:
    args = ["pactl", "set-sink-volume", device, f"{level}%"]
    command = SysCmdExec.run(args)

    if not command.success:
        raise HTTPException(502, "Failed to set audio volume")
    data = ConfigSchema(volume=level)
    config_manager.save_section(data.model_dump(exclude_none=True))
