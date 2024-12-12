from typing import Literal, Optional
from pydantic import BaseModel

DisplayRotation = Literal["normal", "left", "inverted", "right"]
DisplayReflect = Literal["normal", "x", "y", "xy"]


class DisplayPosition(BaseModel):
    x: int
    y: int


class DisplayResolution(BaseModel):
    width: int
    height: int


class ConnectedDisplay(BaseModel):
    name: str
    primary: bool
    resolution: DisplayResolution
    rate: float
    position: DisplayPosition
    rotation: DisplayRotation
    reflect: DisplayReflect
    resolutions: list[DisplayResolution]


class DisplayConfig(BaseModel):
    name: str
    resolution: Optional[DisplayResolution] = None
    rate: Optional[float] = None
    rotation: Optional[DisplayRotation] = None
    position: Optional[DisplayPosition] = None
    reflect: Optional[DisplayReflect] = None
    primary: Optional[bool] = None
