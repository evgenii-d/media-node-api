from typing import Optional
from pydantic import BaseModel, field_validator


class ConfigSchemaIn(BaseModel):
    name: str
    autostart: bool
    url: str
    position: str

    @field_validator("position")
    @classmethod
    def validate_playback(cls, value: str) -> str:
        position = [i.strip() for i in value.split(",")]
        try:
            if len(position) != 2:
                raise ValueError
            for i in position:
                int(i)
        except ValueError as error:
            raise ValueError(
                "Position string can only contain "
                "two int values separated by comma."
            ) from error
        return ",".join(position)


class ConfigSchemaOut(ConfigSchemaIn):
    uuid: str


class ConfigSchemaUpdate(ConfigSchemaIn):
    name: Optional[str] = None
    autostart: Optional[bool] = None
    url: Optional[str] = None
    position: Optional[str] = None
