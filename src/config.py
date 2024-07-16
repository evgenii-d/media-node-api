from src.constants import AppDir
from src.schemas import AppConfigSchema
from src.core.configmgr import ConfigManager

for directory in AppDir:
    directory.value.mkdir(exist_ok=True)

config_path = AppDir.CONFIGS.value/"app.ini"
default_config = {"DEFAULT": AppConfigSchema().model_dump()}
config_manager = ConfigManager(config_path, default_config)
app_config = AppConfigSchema.model_validate(config_manager.load_section())
