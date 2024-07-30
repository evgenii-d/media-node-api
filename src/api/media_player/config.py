import logging
from src.constants import AppDir
from src.core.vlcrc import VLCRemoteControl
from src.core.syscmd import SysCmdExec
from src.core.configmgr import ConfigManager
from src.api.media_player.schemas import ConfigSchema
from src.api.media_player.constants import (PlaybackOption,
                                            VideoOutputModule,
                                            AudioOutputModule)

logger = logging.getLogger(__name__)
config_path = AppDir.CONFIGS.value/"media_player.ini"
default_config = {
    "DEFAULT": ConfigSchema(
        autostart=False,
        volume=0,
        videoOutput=VideoOutputModule.AUTO,
        audioOutput=AudioOutputModule.AUTO,
        audioDevice="",
        playback=PlaybackOption.LOOP.value,
        imageDuration=10,
        screen=0
    ).model_dump()
}
config_manager = ConfigManager(config_path, default_config)
vlc_config = ConfigSchema.model_validate(config_manager.load_section())
vlc_rc = VLCRemoteControl("127.0.0.1", 50000)

if vlc_config.autostart:
    args = ["systemctl", "--user", "start", "media-player.service"]
    SysCmdExec.run(args)
