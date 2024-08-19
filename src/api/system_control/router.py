import socket
from typing import Literal
from fastapi import APIRouter, HTTPException

from src.core.syscmd import SysCmdExec
from src.api.system_control.config import HOSTNAME_TXT, CURSOR_MANAGER
from src.api.system_control.routes.wifi.router import router as wifi_router
from src.api.system_control.routes.audio.router import router as audio_router
from src.api.system_control.routes.displays.router import (
    router as displays_router
)

router = APIRouter(prefix="/system-control", tags=["system control"])
router.include_router(displays_router)
router.include_router(audio_router)
router.include_router(wifi_router)


@router.get("/hostname", responses={
    200: {"description": "Hostname retrieved successfully"}
}, status_code=200)
def hostname() -> str:
    return socket.gethostname()


@router.post("/hostname", responses={
    204: {"description": "Hostname file created successfully"}
}, status_code=204)
def create_hostname_file() -> None:
    HOSTNAME_TXT.touch()


@router.post("/power/{command}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Command execution failed"}
}, status_code=204)
def system_control(command: Literal["poweroff", "reboot"]) -> None:
    args: list[str] = []
    match command:
        case "poweroff":
            args = ["sudo", "shutdown", "now"]
        case "reboot":
            args = ["sudo", "shutdown", "-r", "now"]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")


@router.post("/mouse-cursor/control/{command}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Command execution failed"}
}, status_code=204)
def toggle_mouse_cursor(command: Literal["enable", "disable"]) -> None:
    args = ["sudo", str(CURSOR_MANAGER), command]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")


@router.get("/mouse-cursor/size", responses={
    200: {"description": "Cursor size retrieved successfully"},
    500: {"description": "Failed to retrieve cursor size"},
    502: {"description": "Failed to execute 'get-size' command"}
}, status_code=200)
def mouse_cursor_size() -> int:
    command = SysCmdExec.run(["sudo", str(CURSOR_MANAGER), "get-size"])
    if not command.success:
        raise HTTPException(502, "Failed to execute 'get-size' command")
    try:
        result = int(command.output)
        if result == -1:
            raise ValueError
        return result
    except ValueError as error:
        raise HTTPException(500, "Failed to retrieve cursor size") from error


@router.post("/mouse-cursor/size/{value}", responses={
    200: {"description": "Command executed successfully"},
    502: {"description": "Command execution failed"}
}, status_code=200)
def set_mouse_cursor_size(
    value: Literal["16", "24", "32", "48", "64", "128", "256"]
) -> None:
    args = ["sudo", str(CURSOR_MANAGER), "set-size", value]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, "Failed to execute 'set-size' command")
