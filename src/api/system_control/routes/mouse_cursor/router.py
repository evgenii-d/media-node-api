from typing import Literal
from fastapi import APIRouter, HTTPException

from src.api.system_control.config import CURSOR_CONTROL
from src.core.syscmd import SysCmdExec

router = APIRouter(prefix="/mouse-cursor", tags=["mouse cursor"])


@router.post("/visibility/{state}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Command execution failed"}
}, status_code=204)
def set_mouse_cursor_visibility(state: Literal["on", "off"]) -> None:
    args = ["sudo", str(CURSOR_CONTROL), state]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to change visibility to '{state}'")


@router.get("/size", responses={
    200: {"description": "Cursor size retrieved successfully"},
    500: {"description": "Failed to retrieve cursor size"},
    502: {"description": "Failed to execute 'get-size' command"}
}, status_code=200)
def mouse_cursor_size() -> int:
    command = SysCmdExec.run(["sudo", str(CURSOR_CONTROL), "get-size"])
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
    args = ["sudo", str(CURSOR_CONTROL), "set-size", value]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, "Failed to execute 'set-size' command")
