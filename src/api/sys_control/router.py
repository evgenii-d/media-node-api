import socket
from uuid import uuid4
from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException, Path

from src.core.syscmd import SysCmdExec
from src.api.sys_control.config import config_manager
from src.api.sys_control.schemas import ConfigSchema
from src.api.sys_control.routes.wifi.router import router as wifi_router
from src.api.sys_control.routes.audio.router import router as audio_router
from src.api.sys_control.routes.displays.router import (router as
                                                        displays_router)

router = APIRouter(prefix="/sys-control", tags=["system control"])
router.include_router(displays_router)
router.include_router(audio_router)
router.include_router(wifi_router)


@router.get("/name", responses={
    200: {"description": "Node name retrieved successfully"}
}, status_code=200)
def node_name() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return config.nodeName


@router.put("/name/{new_name}", responses={
    204: {"description": "Node name updated successfully"}
}, status_code=204)
def change_node_name(new_name: Annotated[str, Path(max_length=40)]) -> None:
    data = ConfigSchema(nodeName=new_name.strip())
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get("/hostname", responses={
    200: {"description": "Hostname retrieved successfully"}
}, status_code=200)
def hostname() -> str:
    return socket.gethostname()


@router.post("/hostname", responses={
    200: {"description": "New hostname generated successfully"}
}, status_code=200)
def change_hostname() -> str:
    data = ConfigSchema(generatedHostname=f"node-{uuid4().hex}")
    config_manager.save_section(data.model_dump(exclude_none=True))
    return data.generatedHostname


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
