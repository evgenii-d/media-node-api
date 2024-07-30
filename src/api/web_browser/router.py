from uuid import uuid4
from fastapi import APIRouter, HTTPException

from src.constants import AppDir, SystemctlCommand
from src.core.syscmd import SysCmdExec
from src.core.filesys import get_dir_files
from src.core.configmgr import ConfigManager
from src.api.web_browser.schemas import (ConfigSchemaIn, ConfigSchemaOut,
                                         ConfigSchemaUpdate)

router = APIRouter(prefix="/web-browser", tags=["web browser"])
browser_configs = AppDir.CONFIGS.value/"web_browser"
browser_configs.mkdir(exist_ok=True)


@router.get("/instances", responses={
    200: {"description": "Browser instances retrieved successfully"},
    404: {"description": "No browser instances found"}
}, status_code=200)
def browser_instances() -> list[ConfigSchemaOut]:
    files = get_dir_files(browser_configs)
    if not files:
        raise HTTPException(404, "No browser instances found")
    instances = []
    for file in files:
        config = ConfigManager(browser_configs/file).load_section()
        instances.append(ConfigSchemaOut(**config))
    return instances


@router.post("/instances/{command}", responses={
    204: {"description": "Command executed successfully"},
    502: {"description": "Failed to execute command"}
}, status_code=204)
def command_all_instancies(command: SystemctlCommand) -> None:
    args = ["systemctl", "--user"]
    match command:
        case SystemctlCommand.START:
            args.extend(["start",
                         "web-browser-instances-manager@start-all.service"])
        case _:
            args.extend([command.value, "web-browser@*.service"])
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")


@router.post("/instances/{instance_uuid}/{command}", responses={
    204: {"description": "Command executed successfully"},
    404: {"description": "Browser instance not found"},
    502: {"description": "Failed to execute command"}
}, status_code=204)
def command_browser_instance(instance_uuid: str,
                             command: SystemctlCommand) -> None:
    file = browser_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    args = ["systemctl", "--user", command.value,
            f"web-browser@{instance_uuid}.service"]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")


@router.post("/instances/config", responses={
    201: {"description": "Browser instance created successfully"}
}, status_code=201)
def create_browser_instance_config(data: ConfigSchemaIn) -> ConfigSchemaOut:
    config_path = browser_configs/f"{uuid4().hex}.ini"
    data = ConfigSchemaOut(**data.model_dump(), uuid=config_path.stem)
    ConfigManager(config_path).save_section(data.model_dump())
    return data


@router.patch("/instances/config/{instance_uuid}", responses={
    204: {"description": "Browser instance updated successfully"},
    404: {"description": "Browser instance not found"}
}, status_code=204)
def update_browser_instance_config(instance_uuid: str,
                                   data: ConfigSchemaUpdate) -> None:
    file = browser_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    if data.url == "":
        data.url = "about:blank"
    ConfigManager(file).save_section(data.model_dump(exclude_none=True))


@router.delete("/instances/config/{instance_uuid}", responses={
    204: {"description": "Browser instance deleted successfully"},
    404: {"description": "Browser instance not found"}
}, status_code=204)
def delete_browser_instance_config(instance_uuid: str) -> None:
    file = browser_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    file.unlink()
