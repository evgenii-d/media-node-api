from src.constants import AppDir
from src.core.configmgr import ConfigManager
from src.api.system_control.schemas import ConfigSchema

MODULE_CONFIG = AppDir.CONFIGS.value/"system_control.ini"
XRANDR_CONFIG = AppDir.CONFIGS.value/"xrandr.txt"
DUMMY_HOSTNAME = AppDir.CONFIGS.value/"hostname.txt"
CURSOR_CONTROL = AppDir.SCRIPTS.value/"mouse_cursor_control.sh"
DEFAULT_DATA = {
    "DEFAULT": ConfigSchema(
        audioDevice="",
        volume=50,
        autostartDelay=10
    ).model_dump()
}
config_manager = ConfigManager(MODULE_CONFIG, DEFAULT_DATA)
