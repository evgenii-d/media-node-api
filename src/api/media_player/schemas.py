from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from src.constants import AppDir
from src.api.media_player.constants import (AudioOutputModule,
                                            VideoOutputModule,
                                            PlaybackOption)

PlayerControlCommands = Literal["play", "stop", "next", "prev", "pause"]


class ConfigSchemaIn(BaseModel, use_enum_values=True):
    name: str
    autostart: Optional[bool] = False
    volume: Optional[int] = Field(default=0, ge=0, le=320)
    videoOutput: Optional[VideoOutputModule] = VideoOutputModule.AUTO
    audioOutput: Optional[AudioOutputModule] = AudioOutputModule.AUTO
    audioDevice: Optional[str] = ""
    playback: Optional[str] = "-L"
    imageDuration: Optional[float] = 10.0
    screenNumber: int = Field(ge=0)
    playlist: str

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

    @field_validator("playlist")
    @classmethod
    def validate_playlist(cls, value: str) -> str:
        path = AppDir.PLAYLISTS.value/f"{value}.m3u"
        if path.exists():
            return path.as_posix()
        raise ValueError(f"Playlist '{value}' not found")


class ConfigFileSchema(ConfigSchemaIn):
    playlist: str
    rcPort: int
    uuid: str

    @field_validator("playlist")
    @classmethod
    def validate_playlist(cls, value: str) -> str:
        return value


class ConfigSchemaOut(ConfigFileSchema):
    @field_validator("playlist")
    @classmethod
    def validate_playlist(cls, value: str) -> str:
        return Path(value).stem


class ConfigSchemaUpdate(ConfigSchemaIn):
    name: Optional[str] = None
    autostart: Optional[bool] = None
    volume: Optional[int] = Field(default=None, ge=0, le=320)
    videoOutput: Optional[VideoOutputModule] = None
    audioOutput: Optional[AudioOutputModule] = None
    audioDevice: Optional[str] = None
    playback: Optional[str] = None
    imageDuration: Optional[float] = None
    screenNumber: Optional[int] = Field(default=None, ge=0)
    playlist: Optional[str] = None
