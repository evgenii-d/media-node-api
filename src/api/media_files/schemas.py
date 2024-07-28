from pydantic import BaseModel


class AvailableFilesSchema(BaseModel):
    totalFiles: int
    totalSizeBytes: float
    list: list[str]


class UploadOutSchema(BaseModel):
    accepted: list[str]
    rejected: list[str]


class DeletedFilesSchema(BaseModel):
    deleted: list[str]
    missing: list[str]


class MimeTypeSchema(BaseModel):
    extension: str
    type: str
