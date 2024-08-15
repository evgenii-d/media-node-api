from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse

from src.constants import AppDir
from src.api.media_files.constants import MIMEType
from src.api.media_files.schemas import (
    AvailableFilesSchema,
    UploadOutSchema,
    MimeTypeSchema
)
from src.core.filesys import (
    get_dir_files, get_dir_size,
    aio_save_files_to_dir
)


router = APIRouter(prefix="/media-files", tags=["media files"])


@router.get("/", responses={
    200: {"description": "Media files retrieved successfully"},
    404: {"description": "Media files not found"},
    500: {"description": "Failed to retrieve media files"}
}, status_code=200)
def available_files() -> AvailableFilesSchema:
    files = get_dir_files(AppDir.MEDIA.value)
    if files:
        return AvailableFilesSchema(
            totalFiles=len(files),
            totalSizeBytes=get_dir_size(AppDir.MEDIA.value),
            list=files
        )
    raise HTTPException(404, "Media files not found")


@router.post("/", responses={
    200: {"description": "Files uploaded successfully"},
}, status_code=200)
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
    return UploadOutSchema(
        accepted=[i.filename for i in accepted_files],
        rejected=[i.filename for i in rejected_files]
    )


@router.delete("/{filename}", responses={
    204: {"description": "File deleted successfully"},
    404: {"description": "File not found"},
}, status_code=204)
def delete_files(filename: str) -> None:
    file = AppDir.MEDIA.value/filename
    if not file.exists():
        raise HTTPException(404, "File not found")
    file.unlink()


@router.get("/download/{filename}", responses={
    200: {"description": "File successfully downloaded"},
    404: {"description": "File not found"}
}, status_code=200)
def download_file(filename: str) -> FileResponse:
    if (AppDir.MEDIA.value/filename).exists():
        return FileResponse(AppDir.MEDIA.value/filename, 200)
    raise HTTPException(404, "File not found")


@router.get("/mime-types", responses={
    200: {"description": "Supported MIME types retrieved successfully"}
}, status_code=200)
def supported_types() -> list[MimeTypeSchema]:
    return [
        MimeTypeSchema(extension=member.name.lower(), type=member.value)
        for member in MIMEType
    ]
