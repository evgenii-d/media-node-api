from typing import Annotated
from pydantic import BaseModel, StringConstraints, field_validator

from src.core.filesys import secure_filename


class PlaylistSchema(BaseModel):
    name: Annotated[str, StringConstraints(max_length=40)]
    files: list[str]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return secure_filename(value).lower()
