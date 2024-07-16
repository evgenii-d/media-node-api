from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, StringConstraints

DisplayRotation = Literal["normal", "left", "inverted", "right"]
DisplayReflect = Literal["normal", "x", "y", "xy"]


class ConfigSchema(BaseModel):
    nodeName: Optional[Annotated[str, StringConstraints(
        strip_whitespace=True, max_length=40)]] = None
    generatedHostname: Optional[str] = None
    audioDevice: Optional[str] = None
    volume: Optional[int] = Field(default=None, ge=0, le=150)


class AudioDeviceSchema(BaseModel):
    id: int
    name: str


class WifiInterfaceSchema(BaseModel):
    name: str
    status: str


class SavedWifiConnectionSchema(BaseModel):
    ssid: str
    interface: str


class ToggleWifiInterfaceSchema(BaseModel):
    name: str
    state: bool


class WifiNetworkSchema(BaseModel):
    connected: bool
    bssid: str
    ssid: str
    mode: str
    chan: int
    rate: str
    signal: int
    bars: str
    security: list[str]


class ConnectWifiNetworkSchema(BaseModel):
    ssid: str
    password: Optional[str] = None
    interface: Optional[str] = None


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
    position: DisplayPosition
    rotation: DisplayRotation
    reflect: str
    resolutions: list[str]


class DisplayConfig(BaseModel):
    name: str
    resolution: Optional[DisplayResolution] = None
    rotation: Optional[DisplayRotation] = None
    position: Optional[DisplayPosition] = None
    reflect: Optional[DisplayReflect] = None
    primary: Optional[bool] = None
