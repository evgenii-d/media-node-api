import shutil
import zipfile
from uuid import uuid4
from fastapi import APIRouter, HTTPException, UploadFile

from src.constants import AppDir, SystemctlCommand
from src.core.syscmd import SysCmdExec
from src.core.filesys import get_dir_files, aio_save_files_to_dir
from src.core.configmgr import ConfigManager
from src.api.web_browser.schemas import (ConfigSchemaIn, ConfigSchemaOut,
                                         ConfigSchemaUpdate)

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
        instances.append(ConfigSchemaOut(**config))
    return instances


@router.post("/instances", responses={
    201: {"description": "Browser instance created successfully"}
}, status_code=201)
def create_browser_instance(data: ConfigSchemaIn) -> ConfigSchemaOut:
    config_path = browser_configs/f"{uuid4().hex}.ini"
    data = ConfigSchemaOut(**data.model_dump(), uuid=config_path.stem)
    ConfigManager(config_path).save_section(data.model_dump())
    return data


@router.patch("/instances/{instance_uuid}", responses={
    204: {"description": "Browser instance updated successfully"},
    404: {"description": "Browser instance not found"}
}, status_code=204)
def update_browser_instance(instance_uuid: str,
                            data: ConfigSchemaUpdate) -> None:
    file = browser_configs/f"{instance_uuid}.ini"
    if not file.exists():
        raise HTTPException(404, "Browser instance not found")
    if data.url == "":
        data.url = "about:blank"
    ConfigManager(file).save_section(data.model_dump(exclude_none=True))


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
        raise HTTPException(502, f"Failed to execute '{command}' command")


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
        raise HTTPException(502, f"Failed to execute '{command}' command")
