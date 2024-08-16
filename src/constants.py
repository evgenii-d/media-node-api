from enum import Enum
from pathlib import Path


class AppDir(Enum):
    BASE = Path(__file__).parent.parent
    RESOURCES = BASE/"resources"
    CONFIGS = RESOURCES/"configs"
    MEDIA = RESOURCES/"media"
    PLAYLISTS = RESOURCES/"playlists"
    STATIC = RESOURCES/"static"
    STATIC_PUBLIC = RESOURCES/"static/public"


class AppFile(Enum):
    APP_VERSION = AppDir.BASE.value/"VERSION"
    APP_CONFIG = AppDir.CONFIGS.value/"app.ini"


class SystemctlCommand(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
