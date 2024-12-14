import re
import pathlib
from uuid import uuid4
from fastapi import APIRouter, HTTPException

from src.constants import SystemctlCommand
from src.core.syscmd import SysCmdExec
from src.core.filesys import get_dir_files
from src.core.configmgr import ConfigManager
from src.api.media_player.config import PLAYER_CONFIGS
from src.api.media_player.schemas import (
    ConfigFileSchema,
    ConfigSchemaIn,
    ConfigSchemaOut,
    ConfigSchemaUpdate
)

router = APIRouter(prefix="/instances")


@router.get("/", responses={
    200: {"description": "Player instances retrieved successfully"},
    404: {"description": "No player instances found"},
    502: {"description": "Failed to execute command"}
}, status_code=200)
def list_player_instances() -> list[ConfigSchemaOut]:
    files = get_dir_files(PLAYER_CONFIGS)
    if not files:
        raise HTTPException(404, "No player instances found")

    instances = []
    for file in files:
        data = ConfigManager(PLAYER_CONFIGS/file).load_section()
        config = ConfigSchemaOut(**data)
        config.playlist = pathlib.Path(config.playlist).stem
        instances.append(config)
    return instances


@router.post("/", responses={
    201: {"description": "Player instance created successfully"}
}, status_code=201)
def create_player_instance(data: ConfigSchemaIn) -> ConfigSchemaOut:
    port = 50000
    ports: list[int] = []

    # Extract port numbers from player configuration files
    for file in PLAYER_CONFIGS.iterdir():
        value = ConfigSchemaOut(**ConfigManager(file).load_section()).rcPort
        ports.append(value)

    # If there are any missing ports, use the smallest missing port.
    # Otherwise, use the next available port number after the highest.
    if ports:
        ports_range = list(range(min(ports), max(ports) + 1))
        missing_ports = list(set(ports_range) - set(ports))
        port = min(missing_ports) if missing_ports else max(ports) + 1

    new_config_path = PLAYER_CONFIGS/f"{uuid4().hex}.ini"
    new_config = ConfigFileSchema(
        **data.model_dump(),
        rcPort=port,
        uuid=new_config_path.stem
    )
    ConfigManager(new_config_path).save_section(new_config.model_dump())
    return ConfigSchemaOut(**new_config.model_dump())


@router.get("/running", responses={
    200: {"description": "Running instances retrieved successfully"},
    404: {"description": "No running instances found"},
    502: {"description": "Failed to retrieve running instances"}
}, status_code=200)
def list_running_instances() -> list[str]:
    args = [
        "systemctl", "--user", "list-units",
        "--type", "service", "--state", "active,running"
    ]
    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(502, "Failed to retrieve running instances")

    result = re.findall(r"media-player@(.*).service", command.output)
    if result:
        return result
    raise HTTPException(404, "No running instances found")


@router.post("/control/{command}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Failed to execute command"}
}, status_code=204)
def control_available_instances(command: SystemctlCommand) -> None:
    args = ["systemctl", "--user"]
    match command:
        case SystemctlCommand.START:
            args.extend([
                "start",
                "media-player-instances-control@start-all.service"
            ])
        case _:
            args.extend([command.value, "media-player@*.service"])
    if not SysCmdExec.run(args).success:
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)


@router.patch("/{instance_uuid}", responses={
    204: {"description": "Player instance updated successfully"},
    404: {"description": "Player instance not found"}
}, status_code=204)
def update_player_instance(instance_uuid: str,
                           data: ConfigSchemaUpdate) -> None:
    file = PLAYER_CONFIGS/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Player instance not found")
    ConfigManager(file).save_section(data.model_dump(exclude_none=True))


@router.delete("/{instance_uuid}", responses={
    204: {"description": "Player instance deleted successfully"},
    404: {"description": "Player instance not found"}
}, status_code=204)
def delete_player_instance(instance_uuid: str) -> None:
    file = PLAYER_CONFIGS/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Player instance not found")
    file.unlink()
