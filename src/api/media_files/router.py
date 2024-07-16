from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse

from src.constants import AppDir
from src.api.media_files.constants import MIMEType
from src.api.media_files.schemas import (AvailableFilesSchema,
                                         UploadOutSchema,
                                         DeletedFilesSchema)
from src.core.filesys import (get_dir_files, del_files_from_dir,
                              get_dir_size, check_dir_files,
                              aio_save_files_to_dir)


router = APIRouter(prefix="/media-files", tags=["media files"])


@router.get("/")
def available_files() -> AvailableFilesSchema:
    files = get_dir_files(AppDir.MEDIA.value)
    return AvailableFilesSchema(
        totalFiles=len(files),
        totalSizeBytes=get_dir_size(AppDir.MEDIA.value),
        list=files
    )


@router.post("/")
async def upload_files(files: list[UploadFile]) -> UploadOutSchema:
    accepted_files: list[UploadFile] = []
    rejected_files: list[UploadFile] = []
    file_types = [member.value for member in MIMEType]
    for file in files:
        if file.content_type.lower() in file_types:
            accepted_files.append(file)
        else:
            rejected_files.append(file)
    await aio_save_files_to_dir(accepted_files, AppDir.MEDIA.value)
    return UploadOutSchema(accepted=[i.filename for i in accepted_files],
                           rejected=[i.filename for i in rejected_files])


@router.delete("/")
def delete_files(files: list[str]) -> DeletedFilesSchema:
    dir_files = check_dir_files(files, AppDir.MEDIA.value)
    del_files_from_dir(dir_files.available, AppDir.MEDIA.value)
    return DeletedFilesSchema(
        deleted=dir_files.available,
        missing=dir_files.missing
    )


@router.get("/download/{filename}", responses={
    200: {"description": "File successfully downloaded"},
    404: {"description": "File not found"}
})
def download_file(filename: str) -> FileResponse:
    if (AppDir.MEDIA.value/filename).exists():
        return FileResponse(AppDir.MEDIA.value/filename, 200)
    raise HTTPException(404, "File not found")


@router.get("/types")
def supported_types() -> list[str]:
    return [member.name.lower() for member in MIMEType]
