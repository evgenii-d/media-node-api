from enum import Enum
from pathlib import Path


class AppDir(Enum):
    BASE = Path(__file__).parent.parent
    RESOURCES = BASE/"resources"
    CONFIGS = RESOURCES/"configs"
    MEDIA = RESOURCES/"media"
    PLAYLISTS = RESOURCES/"playlists"
    STATIC_FILES = RESOURCES/"static_files"
    STATIC_FILES_PUBLIC = STATIC_FILES/"public"


class SystemctlCommand(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
