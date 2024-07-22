from typing import Optional
from pydantic import BaseModel


class WindowPosition(BaseModel):
    x: int
    y: int


class ConfigSchema(BaseModel):
    autostart: Optional[bool] = None
    url: Optional[str] = None
    position: Optional[WindowPosition] = None
