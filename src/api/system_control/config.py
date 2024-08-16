from src.constants import AppDir
from src.core.configmgr import ConfigManager
from src.api.system_control.schemas import ConfigSchema

config_path = AppDir.CONFIGS.value/"system_control.ini"
xrandr_config = AppDir.CONFIGS.value/"xrandr.txt"
default_config = {
    "DEFAULT": ConfigSchema(
        nodeName="Media Node",
        audioDevice="",
        volume=50
    ).model_dump()
}
config_manager = ConfigManager(config_path, default_config)
