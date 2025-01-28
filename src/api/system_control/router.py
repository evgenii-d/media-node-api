import socket
from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException, Path

from src.core.syscmd import SysCmdExec
from src.api.system_control.config import DUMMY_HOSTNAME, config_manager
from src.api.system_control.schemas import ConfigSchema
from src.api.system_control.routes.audio.router import router as audio_router
from src.api.system_control.routes.network.router import (
    router as network_router
)
from src.api.system_control.routes.displays.router import (
    router as displays_router
)
from src.api.system_control.routes.mouse_cursor.router import (
    router as mouse_cursor_router
)

router = APIRouter(prefix="/system-control", tags=["system control"])
router.include_router(displays_router)
router.include_router(audio_router)
router.include_router(network_router)
router.include_router(mouse_cursor_router)


@router.get(
    "/hostname",
    responses={
        200: {"description": "Hostname retrieved successfully"}
    },
    status_code=200
)
def hostname() -> str:
    return socket.gethostname()


@router.post(
    "/hostname",
    responses={
        204: {"description": "Command executed successfully"}
    },
    status_code=204
)
def generate_new_hostname() -> None:
    DUMMY_HOSTNAME.touch()


@router.post(
    "/power/{command}",
    responses={
        204: {"description": "Command executed successfully"},
        502: {"description": "Command execution failed"}
    },
    status_code=204
)
def system_control(command: Literal["shutdown", "reboot"]) -> None:
    args: list[str] = []
    match command:
        case "shutdown":
            args = ["sudo", "shutdown", "now"]
        case "reboot":
            args = ["sudo", "shutdown", "-r", "now"]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")


@router.get(
    "/autostart/delay",
    responses={200: {"description": "Value retrieved successfully"}},
    status_code=200
)
def autostart_delay() -> int:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return config.autostartDelay


@router.put(
    "/autostart/delay/{value}",
    responses={204: {"description": "Value updated successfully"}},
    status_code=204
)
def change_autostart_delay(value: Annotated[int, Path(ge=10)]) -> None:
    data = ConfigSchema(autostartDelay=value)
    config_manager.save_section(data.model_dump(exclude_none=True))
