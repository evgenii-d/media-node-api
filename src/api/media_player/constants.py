from enum import Enum


class VideoOutputModule(Enum):
    AUTO = "any"
    DIRECT3D11 = "direct3d11"
    DIRECT3D9 = "direct3d9"
    OPENGLWINDOWS = "glwin32"
    OPENGL = "gl"
    OPENGL_ES2 = "gles2"
    DIRECTDRAW = "directdraw"
    WINDOWSGDI = "wingdi"
    XVIDEO_XCB = "xcb_xv"
    X11_XCB = "xcb_x11"
    MMAL_X11_RPI2 = "mmal_xsplitter"


class AudioOutputModule(Enum):
    AUTO = "any"
    ALSA = "alsa"
    PULSE = "pulse"
    MMDEVICE = "mmdevice"
    DIRECTSOUND = "directsound"
    WAVEOUT = "waveout"
    AMEM = "amem"
    AFILE = "afile"
    ADUMMY = "adummy"
    NONE = "none"


class PlayerControlCommands(Enum):
    PLAY = "play"
    STOP = "stop"
    NEXT = "next"
    PREVIOUS = "prev"
    PAUSE = "pause"


class PlaybackOption(Enum):
    LOOP = "-L"
    REPEAT = "-R"
    RANDOM = "-Z"


class MediaPlayerInterface(Enum):
    QT = "qt"
    DUMMY = "dummy"
