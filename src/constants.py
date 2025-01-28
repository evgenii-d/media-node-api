from enum import Enum
from pathlib import Path


class AppDir(Enum):
    ROOT = Path(__file__).parent.parent
    RESOURCES = ROOT/"resources"
    SCRIPTS = ROOT/"scripts"
    CONFIGS = RESOURCES/"configs"
    PLAYER_CONFIGS = CONFIGS/"media_player"
    BROWSER_CONFIGS = CONFIGS/"web_browser"
    MEDIA = RESOURCES/"media"
    PLAYLISTS = RESOURCES/"playlists"
    STATIC_FILES = RESOURCES/"static_files"
    STATIC_FILES_PUBLIC = STATIC_FILES/"public"


class SystemctlCommand(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
