import uuid

from src.constants import AppDir
from src.core.configmgr import ConfigManager
from src.api.sys_control.schemas import ConfigSchema

config_path = AppDir.CONFIGS.value/"sys_control.ini"
xrandr_config = AppDir.CONFIGS.value/"xrandr.txt"
default_config = {
    "DEFAULT": ConfigSchema(
        nodeName="Media Node",
        generatedHostname=f"node-{uuid.uuid4().hex}",
        audioDevice="",
        volume=50
    ).model_dump()
}
config_manager = ConfigManager(config_path, default_config)
