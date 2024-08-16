from src.constants import AppDir
from src.core.configmgr import ConfigManager
from src.api.system_control.schemas import ConfigSchema

MODULE_CONFIG = AppDir.CONFIGS.value/"system_control.ini"
XRANDR_CONFIG = AppDir.CONFIGS.value/"xrandr.txt"
DEFAULT_DATA = {
    "DEFAULT": ConfigSchema(
        nodeName="Media Node",
        audioDevice="",
        volume=50
    ).model_dump()
}
config_manager = ConfigManager(MODULE_CONFIG, DEFAULT_DATA)
