from typing import Optional
from pydantic import BaseModel


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
    password: Optional[str] = None
    interface: Optional[str] = None
