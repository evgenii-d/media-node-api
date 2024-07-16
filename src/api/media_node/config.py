import uuid

from src.constants import AppDir
from src.core.syscmd import SysCmdExec
from src.core.configmgr import ConfigManager
from src.api.media_node.schemas import ConfigSchema

config_path = AppDir.CONFIGS.value/"media_node.ini"
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
node_config = ConfigSchema.model_validate(config_manager.load_section())

if node_config.audioDevice:
    args = ["pacmd", "set-default-sink", node_config.audioDevice]
    SysCmdExec.run(args)

if node_config.volume:
    args = ["pactl", "set-sink-volume",
            "@DEFAULT_SINK@", f"{node_config.volume}%"]
    SysCmdExec.run(args)
