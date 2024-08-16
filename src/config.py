from src.constants import AppDir, AppFile
from src.schemas import AppConfigSchema
from src.core.configmgr import ConfigManager

for directory in AppDir:
    directory.value.mkdir(exist_ok=True)

default_config = {"DEFAULT": AppConfigSchema().model_dump()}
config_manager = ConfigManager(AppFile.APP_CONFIG.value, default_config)
app_config = AppConfigSchema.model_validate(config_manager.load_section())
