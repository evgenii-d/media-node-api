from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from src.api.media_player.constants import (AudioOutputModule,
                                            VideoOutputModule,
                                            PlaybackOption)

PlayerControlCommands = Literal["play", "stop", "next", "prev", "pause"]


class ConfigSchema(BaseModel, use_enum_values=True):
    autostart: Optional[bool] = None
    volume: Optional[int] = Field(default=None, ge=0, le=320)
    videoOutput: Optional[VideoOutputModule] = None
    audioOutput: Optional[AudioOutputModule] = None
    audioDevice: Optional[str] = None
    playback: Optional[str] = None
    imageDuration: Optional[float] = None

    @field_validator("playback")
    @classmethod
    def validate_playback(cls, value: str) -> str:
        value = value.split()
        options = [po.value for po in PlaybackOption]
        if not all(part in options for part in value):
            raise ValueError(
                "Playback string can only contain "
                f"{', '.join(options)} separated by spaces."
            )
        return " ".join(value)
