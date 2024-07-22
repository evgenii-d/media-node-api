from src.constants import AppDir
from src.core.syscmd import SysCmdExec
from src.core.configmgr import ConfigManager
from src.api.web_browser.schemas import ConfigSchema, WindowPosition

config_path = AppDir.CONFIGS.value/"web_browser.ini"
service_configs_path = AppDir.CONFIGS.value/"web_browser"
default_config = {
    "DEFAULT": ConfigSchema(
        autostart=False,
        url="about:blank",
        position=WindowPosition(x=0, y=0)
    ).model_dump()
}
config_manager = ConfigManager(config_path, default_config)
browser_config = ConfigSchema.model_validate(config_manager.load_section())

if browser_config.autostart:
    args = ["systemctl", "--user", "start", "web-browser.service"]
    SysCmdExec.run(args)
