import re
from uuid import uuid4
from fastapi import APIRouter, HTTPException

from src.constants import AppDir, SystemctlCommand
from src.core.syscmd import SysCmdExec
from src.core.filesys import get_dir_files
from src.core.configmgr import ConfigManager
from src.api.web_browser.schemas import (
    WindowPosition,
    ConfigSchemaIn,
    ConfigSchemaOut,
    ConfigFileSchema,
    ConfigFileSchemaIn,
    ConfigFileSchemaUpdate
)

router = APIRouter(prefix="/web-browser", tags=["web browser"])


@router.get(
    "/instances",
    responses={
        200: {"description": "Browser instances retrieved successfully"},
        404: {"description": "No browser instances found"}
    },
    status_code=200
)
def list_browser_instances() -> list[ConfigSchemaOut]:
    files = get_dir_files(AppDir.BROWSER_CONFIGS.value)
    if not files:
        raise HTTPException(404, "No browser instances found")
    instances = []
    for file in files:
        config = ConfigManager(
            AppDir.BROWSER_CONFIGS.value/file).load_section()
        config = ConfigFileSchema(**config)
        x, y = config.position.split(",")
        instances.append(ConfigSchemaOut(
            name=config.name,
            autostart=config.autostart,
            url=config.url,
            position=WindowPosition(x=x, y=y),
            uuid=config.uuid
        ))
    return instances


@router.post(
    "/instances",
    responses={201: {"description": "Browser instance created successfully"}},
    status_code=201
)
def create_browser_instance(data: ConfigSchemaIn) -> ConfigSchemaOut:
    config_path = AppDir.BROWSER_CONFIGS.value/f"{uuid4().hex}.ini"
    data_out = ConfigSchemaOut(**data.model_dump(), uuid=config_path.stem)
    file_data = ConfigFileSchema(
        name=data_out.name,
        autostart=data_out.autostart,
        url=data_out.url,
        position=f"{data_out.position.x},{data_out.position.y}",
        uuid=data_out.uuid
    )
    ConfigManager(config_path).save_section(file_data.model_dump())
    return data_out


@router.get(
    "/instances/running",
    responses={
        200: {"description": "Running instances retrieved successfully"},
        404: {"description": "No running instances found"},
        502: {"description": "Failed to retrieve running instances"}
    },
    status_code=200
)
def list_running_instances() -> list[str]:
    args = ["systemctl", "--user", "list-units",
            "--type", "service", "--state", "active,running"]
    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(502, "Failed to retrieve running instances")

    result = re.findall(r"web-browser@(.*).service", command.output)
    if result:
        return result
    raise HTTPException(404, "No running instances found")


@router.post(
    "/instances/control/{command}",
    responses={
        204: {"description": "Command executed successfully"},
        502: {"description": "Failed to execute command"}
    },
    status_code=204
)
def control_available_instances(command: SystemctlCommand) -> None:
    args = ["systemctl", "--user"]
    match command:
        case SystemctlCommand.START:
            args.extend([
                "start", "web-browser-instances-control@start-all.service"
            ])
        case _:
            args.extend([command.value, "web-browser@*.service"])
    if not SysCmdExec.run(args).success:
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)


@router.patch(
    "/instances/{instance_uuid}",
    responses={
        204: {"description": "Browser instance updated successfully"},
        404: {"description": "Browser instance not found"}
    },
    status_code=204
)
def update_browser_instance(
    instance_uuid: str,
    data: ConfigFileSchemaIn
) -> None:
    file = AppDir.BROWSER_CONFIGS.value/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    position = None
    if data.position:
        position = f"{data.position.x},{data.position.y}"
    file_data = ConfigFileSchemaUpdate(
        name=data.name,
        autostart=data.autostart,
        url="about:blank" if data.url == "" else data.url,
        position=position,
    ).model_dump(exclude_none=True)
    ConfigManager(file).save_section(file_data)


@router.delete(
    "/instances/{instance_uuid}",
    responses={
        204: {"description": "Browser instance deleted successfully"},
        404: {"description": "Browser instance not found"}
    },
    status_code=204
)
def delete_browser_instance(instance_uuid: str) -> None:
    file = AppDir.BROWSER_CONFIGS.value/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    file.unlink()


@router.post(
    "/instances/{instance_uuid}/control/{command}",
    responses={
        204: {"description": "Command executed successfully"},
        404: {"description": "Browser instance not found"},
        502: {"description": "Failed to execute command"}
    },
    status_code=204
)
def control_instance_service(instance_uuid: str,
                             command: SystemctlCommand) -> None:
    file = AppDir.BROWSER_CONFIGS.value/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    args = [
        "systemctl", "--user", command.value,
        f"web-browser@{instance_uuid}.service"
    ]
    if not SysCmdExec.run(args).success:
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)
