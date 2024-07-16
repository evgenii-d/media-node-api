from src.constants import AppDir
from src.core.configmgr import ConfigManager
from src.api.playlists.schemas import ConfigSchema

config_path = AppDir.CONFIGS.value/"playlists.ini"
default_config = {
    "DEFAULT": ConfigSchema(
        defaultPlaylist=""
    ).model_dump()
}
config_manager = ConfigManager(config_path, default_config)
