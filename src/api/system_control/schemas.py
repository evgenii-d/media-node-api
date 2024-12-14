from typing import Optional
from pydantic import BaseModel, Field


class ConfigSchema(BaseModel):
    audioDevice: Optional[str] = None
    volume: Optional[int] = Field(default=None, ge=0, le=150)
    autostartDelay: Optional[int] = Field(default=None, ge=10)
