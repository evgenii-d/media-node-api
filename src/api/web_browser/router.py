import re
import shutil
import zipfile
from uuid import uuid4
from fastapi import APIRouter, HTTPException, UploadFile

from src.constants import AppDir, SystemctlCommand
from src.core.syscmd import SysCmdExec
from src.core.filesys import get_dir_files, aio_save_files_to_dir
from src.core.configmgr import ConfigManager
from src.api.web_browser.schemas import (WindowPosition,
                                         ConfigSchemaIn,
                                         ConfigSchemaOut,
                                         ConfigFileSchema,
                                         ConfigFileSchemaIn,
                                         ConfigFileSchemaUpdate)

router = APIRouter(prefix="/web-browser", tags=["web browser"])
browser_configs = AppDir.CONFIGS.value/"web_browser"
browser_configs.mkdir(exist_ok=True)


@router.post("/static", responses={
    204: {"description": "File successfully uploaded"},
    400: {"description": "Invalid file type. Accept only .zip files"}
}, status_code=204)
async def upload_static_files(file: UploadFile) -> None:
    file.filename = "archive.zip"
    archive = AppDir.STATIC.value/file.filename
    await aio_save_files_to_dir([file], AppDir.STATIC.value)

    if not zipfile.is_zipfile(archive):
        archive.unlink()
        raise HTTPException(400, (f"Invalid file type: {file.content_type}. "
                                  "Only .zip files allowed."))

    # remove all files and folders from the "public" directory
    for item in (AppDir.STATIC_PUBLIC.value).glob("*"):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(True)
    shutil.unpack_archive(archive, AppDir.STATIC_PUBLIC.value)


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


@router.post("/instances", responses={
    201: {"description": "Browser instance created successfully"}
}, status_code=201)
def create_browser_instance(data: ConfigSchemaIn) -> ConfigSchemaOut:
    config_path = browser_configs/f"{uuid4().hex}.ini"
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


@router.get("/instances/active", responses={
    200: {"description": "Active instances retrieved successfully"},
    404: {"description": "No active instances found"},
    502: {"description": "Failed to retrieve active instances"}
}, status_code=200)
def active_instances() -> list[str]:
    args = ["systemctl", "--user", "list-units",
            "--type", "service", "--state", "active,running"]
    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(502, "Failed to retrieve active instances")

    result = re.findall(r"web-browser@(.*).service", command.output)
    if result:
        return result
    raise HTTPException(404, "No active instances found")


@router.patch("/instances/{instance_uuid}", responses={
    204: {"description": "Browser instance updated successfully"},
    404: {"description": "Browser instance not found"}
}, status_code=204)
def update_browser_instance(instance_uuid: str,
                            data: ConfigFileSchemaIn) -> None:
    file = browser_configs/f"{instance_uuid}.ini"
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


@router.delete("/instances/{instance_uuid}", responses={
    204: {"description": "Browser instance deleted successfully"},
    404: {"description": "Browser instance not found"}
}, status_code=204)
def delete_browser_instance(instance_uuid: str) -> None:
    file = browser_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    file.unlink()


@router.post("/instances/manager/{command}", responses={
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
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)


@router.post("/{instance_uuid}/service/{command}", responses={
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
        message = f"Failed to execute '{command.value}' command"
        raise HTTPException(502, message)
