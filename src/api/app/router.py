import shutil
import zipfile
from typing import Annotated
from fastapi import APIRouter, UploadFile, HTTPException, Path

from src.config import config_manager, VERSION_FILE
from src.schemas import ConfigSchema
from src.constants import AppDir
from src.core.filesys import aio_save_files_to_dir


router = APIRouter(prefix="/app", tags=["app"])


@router.get(
    "/node-name",
    responses={200: {"description": "Node name retrieved successfully"}},
    status_code=200
)
def node_name() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return config.nodeName


@router.put(
    "/node-name/{new_name}",
    responses={204: {"description": "Node name updated successfully"}},
    status_code=204
)
def change_node_name(new_name: Annotated[str, Path(max_length=40)]) -> None:
    data = ConfigSchema(nodeName=new_name.strip())
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get(
    "/version",
    responses={
        200: {"description": "App version retrieved successfully"},
        404: {"description": "App version not found"}
    },
    status_code=200
)
def app_version() -> str:
    try:
        return VERSION_FILE.read_text("utf-8")
    except FileNotFoundError as e:
        raise HTTPException(404, "App version not found") from e


@router.post(
    "/static_files",
    responses={
        204: {"description": "File successfully uploaded"},
        400: {"description": "Invalid file type. Accept only .zip file"}
    },
    status_code=204
)
async def upload_static_files(file: UploadFile) -> None:
    file.filename = "archive.zip"
    archive = AppDir.STATIC_FILES.value/file.filename
    await aio_save_files_to_dir([file], AppDir.STATIC_FILES.value)

    if not zipfile.is_zipfile(archive):
        archive.unlink()
        raise HTTPException(400, "Only a .zip file is allowed.")

    # remove all files and folders from the "public" directory
    for item in (AppDir.STATIC_FILES_PUBLIC.value).glob("*"):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(True)
    shutil.unpack_archive(archive, AppDir.STATIC_FILES_PUBLIC.value)
