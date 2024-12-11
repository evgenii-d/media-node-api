from typing import Literal
from fastapi import APIRouter, HTTPException

from src.api.system_control.config import CURSOR_MANAGER
from src.core.syscmd import SysCmdExec

router = APIRouter(prefix="/mouse-cursor", tags=["mouse cursor"])


@router.post("/visibility/{value}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Command execution failed"}
}, status_code=204)
def toggle_mouse_cursor(value: Literal["show", "hide"]) -> None:
    args = ["sudo", str(CURSOR_MANAGER), value]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to change visibility to '{value}'")


@router.get("/size", responses={
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


@router.post("/size/{value}", responses={
    200: {"description": "Command executed successfully"},
    502: {"description": "Command execution failed"}
}, status_code=200)
def set_mouse_cursor_size(
    value: Literal["16", "24", "32", "48", "64", "96", "128", "256"]
) -> None:
    args = ["sudo", str(CURSOR_MANAGER), "set-size", value]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, "Failed to execute 'set-size' command")
