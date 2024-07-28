from enum import Enum
from pathlib import Path


class AppDir(Enum):
    BASE = Path(__file__).parent.parent/"resources"
    CONFIGS = BASE/"configs"
    MEDIA = BASE/"media"
    PLAYLISTS = BASE/"playlists"
    STATIC = BASE/"static"
    STATIC_PUBLIC = BASE/"static/public"


class SystemctlCommand(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
