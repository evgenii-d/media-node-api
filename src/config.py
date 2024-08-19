from src.constants import AppDir
from src.schemas import ConfigSchema
from src.core.configmgr import ConfigManager

for directory in AppDir:
    directory.value.mkdir(exist_ok=True)

APP_CONFIG = AppDir.CONFIGS.value/"app.ini"
DEFAULT_DATA = {
    "DEFAULT": ConfigSchema(
        host="0.0.0.0",
        port=5000,
        reload=False,
        debug=False,
        openapi=False,
        nodeName="Media Node"
    ).model_dump()
}
config_manager = ConfigManager(APP_CONFIG, DEFAULT_DATA)
