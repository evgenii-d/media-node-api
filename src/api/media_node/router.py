import re
import uuid
import shutil
import socket
import zipfile
from fastapi import APIRouter, HTTPException, Response, UploadFile, Body

from src.constants import AppDir
from src.core.syscmd import SysCmdExec
from src.core.filesys import aio_save_files_to_dir
from src.api.media_node.config import config_manager, xrandr_config
from src.api.media_node.schemas import (ConfigSchema, AudioDeviceSchema,
                                        WifiInterfaceSchema,
                                        SavedWifiConnectionSchema,
                                        ConnectWifiNetworkSchema,
                                        WifiNetworkSchema,
                                        ConnectedDisplay, DisplayPosition,
                                        DisplayResolution, DisplayConfig)


router = APIRouter(prefix="/media-node", tags=["media node"])

system_responses = {
    200: {"description": "Command executed successfully"},
    500: {"description": "Command execution failed"}
}


def xrandr_to_dict(xrandr_args: list[str]) -> dict[str, str]:
    result = {}
    for i, word in enumerate(xrandr_args):
        if word in ["sudo", "xrandr", "--primary"]:
            result.update({word: None})
        elif "--" in word:
            result.update({word: xrandr_args[i+1]})
    return result


@router.get("/name")
def node_name() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return config.nodeName


@router.post("/name")
def set_name(value: str = Body(max_length=40)) -> Response:
    data = ConfigSchema(nodeName=value.strip())
    config_manager.save_section(data.model_dump(exclude_none=True))
    return Response(status_code=200)


@router.get("/hostname")
def hostname() -> str:
    return socket.gethostname()


@router.post("/hostname", responses={
    200: {"description": "New hostname generated successfully"}
})
def change_hostname() -> str:
    data = ConfigSchema(generatedHostname=f"node-{uuid.uuid4().hex}")
    config_manager.save_section(data.model_dump(exclude_none=True))
    return data.generatedHostname


@router.post("/poweroff", responses={**system_responses})
def system_poweroff() -> Response:
    args = ["sudo", "shutdown", "now"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 500)


@router.post("/reboot", responses={**system_responses})
def system_reboot() -> Response:
    args = ["sudo", "shutdown", "-r", "now"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 500)


@router.post("/static-upload", responses={
    200: {"description": "File successfully uploaded"},
    400: {"description": "Accept only .zip files"}
})
async def static_upload(file: UploadFile) -> Response:
    file.filename = "archive.zip"
    archive = AppDir.STATIC.value/file.filename
    await aio_save_files_to_dir([file], AppDir.STATIC.value)

    if not zipfile.is_zipfile(archive):
        archive.unlink()
        raise HTTPException(400, "Accept only .zip files")

    # remove all files and folders from the "public" directory
    for item in (AppDir.STATIC_PUBLIC.value).glob("*"):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(True)

    shutil.unpack_archive(archive, AppDir.STATIC_PUBLIC.value)
    return Response(status_code=200)


@router.get("/audio/devices", responses={
    200: {"description": "Audio devices retrieved successfully"},
    500: {"description": "Failed to retrieve audio devices"}
})
def audio_devices() -> list[AudioDeviceSchema]:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    result = []
    devices = re.findall(r"index: (\d+)\n.*name: <(.*)>", command.output)
    try:
        for d in devices:
            result.append(AudioDeviceSchema(id=d[0], name=d[1]))
    except IndexError as e:
        raise HTTPException(500, "Failed to retrieve audio devices") from e
    return result


@router.get("/audio/default-device", responses={
    200: {"description": "Default Audio device retrieved successfully"},
    500: {"description": "Failed to retrieve default audio device"}
})
def default_audio_device() -> AudioDeviceSchema:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    device = re.search(r"\* index: (\d+)\n.*name: <(.+)>", command.output)
    try:
        return AudioDeviceSchema(id=device.group(1), name=device.group(2))
    except (IndexError, AttributeError) as e:
        message = "Failed to retrieve default audio device"
        raise HTTPException(500, message) from e


@router.post("/audio/default-device", responses={
    200: {"description": "Default audio device set successfully"},
    500: {"description": "Command execution failed"}
})
def set_default_audio_device(device: str = Body()) -> Response:
    command = SysCmdExec.run(["pacmd", "set-default-sink", device])
    if not command.success:
        raise HTTPException(500, "Command execution failed")
    data = ConfigSchema(audioDevice=device)
    config_manager.save_section(data.model_dump(exclude_none=True))
    return Response(status_code=200)


@router.get("/audio/volume", responses={
    200: {"description": "Current audio volume retrieved successfully"},
    500: {"description": "Failed to retrieve current audio volume"}
})
def audio_volume() -> int:
    command = SysCmdExec.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    if not command.success:
        raise HTTPException(500, "Failed to retrieve current audio volume")
    volume_level = int(command.output.strip().split()[4][:-1])
    return volume_level


@router.post("/audio/volume", responses={
    200: {"description": "Audio volume set successfully"},
    500: {"description": "Failed to set audio volume"}
})
def set_audio_volume(level: int = Body(ge=0, le=150)) -> Response:
    args = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"]
    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(500, "Failed to set audio volume")
    data = ConfigSchema(volume=level)
    config_manager.save_section(data.model_dump(exclude_none=True))
    return Response(status_code=200)


@router.get("/wifi/interfaces", responses={
    200: {"description": "List of Wi-Fi interfaces retrieved successfully"},
    204: {"description": "No Wi-Fi interfaces found"},
    500: {"description": "Failed to retrieve list of Wi-Fi interfaces"}
})
def wifi_interfaces() -> list[WifiInterfaceSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "device", "status"])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    result = re.findall(r"(\S.+)(?:\:wifi\:)(.+?):", command.output)
    if not result:
        return Response(status_code=204)
    return [WifiInterfaceSchema(name=i[0], status=i[1]) for i in result]


@router.get("/wifi/saved-connections", responses={
    200: {"description": "Wi-Fi connections retrieved successfully"},
    204: {"description": "No Wi-Fi connections found"},
    500: {"description": "Failed to retrieve Wi-Fi connections"}
})
def saved_wifi_connections() -> list[SavedWifiConnectionSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "connection", "show"])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    result = []
    for line in command.output.splitlines():
        if "wireless" in line:
            data = [i.strip() for i in line.split(":")]
            item = SavedWifiConnectionSchema(ssid=data[0], interface=data[3])
            result.append(item)
    return result if result else Response(status_code=204)


@router.delete("/wifi/saved-connections", responses={**system_responses})
def delete_saved_wifi_connections() -> Response:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "connection", "show"])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    for line in command.output.splitlines():
        if "wireless" in line:
            connection_uuid = [i.strip() for i in line.split(":")][1]
            delete_connection = SysCmdExec.run(["sudo", "nmcli", "connection",
                                                "delete", connection_uuid])
            if not delete_connection.success:
                raise HTTPException(500, f"Failed to delete {connection_uuid}")
    return Response(status_code=200)


@router.get("/wifi/{interface}/networks", responses={
    200: {"description": "Available Wi-Fi networks retrieved successfully"},
    204: {"description": "No available Wi-Fi networks found"},
    500: {"description": "Failed to retrieve Wi-Fi networks"}
})
def available_wifi_networks(interface: str) -> list[WifiNetworkSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "device",
                              "wifi", "list", "ifname", interface])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    result: list[WifiNetworkSchema] = []
    for line in command.output.splitlines():
        data = re.search(
            r"(?P<connected>\*| )"
            r":(?P<bssid>(?:..\\:){5}..)"
            r":(?P<ssid>.*?)"
            r":(?P<mode>.*?)"
            r":(?P<chan>\d+)"
            r":(?P<rate>.*?)"
            r":(?P<signal>\d+)"
            r":(?P<bars>.*?)"
            r":(?P<security>.+)", line)
        if data:
            network = data.groupdict()
            network["connected"] = network["connected"] == "*"
            network["bssid"] = network["bssid"].replace("\\", "")
            network["chan"] = int(network["chan"])
            network["signal"] = int(network["signal"])
            network["security"] = network["security"].split(" ")
            result.append(WifiNetworkSchema(**network))
    return result if result else Response(status_code=204)


@router.post("/wifi/connect", responses={**system_responses})
def connect_wifi_network(data: ConnectWifiNetworkSchema) -> Response:
    connect_args = ["sudo", "nmcli", "device", "wifi", "connect", data.ssid]

    if data.password:
        connect_args.extend(["password", data.password])

    if data.interface:
        connect_args.extend(["ifname", data.interface])

    connect = SysCmdExec.run(connect_args)
    if not connect.success:
        raise HTTPException(500, "Failed to connect interface")

    enable_autoconnect = SysCmdExec.run(["sudo", "nmcli", "connection",
                                         "modify", data.ssid,
                                         "connection.autoconnect", "yes"])
    if not enable_autoconnect.success:
        raise HTTPException(500, "Failed to enable autoconnect")
    return Response(status_code=200)


@router.post("/wifi/disconnect", responses={**system_responses})
def disconnect_wifi_network(ssid: str = Body()) -> Response:
    disconnect = SysCmdExec.run(["sudo", "nmcli", "connection", "down", ssid])
    if not disconnect.success:
        raise HTTPException(500, "Failed to disconnect interface")

    disable_autoconnect = SysCmdExec.run(["sudo", "nmcli", "connection",
                                          "modify", ssid,
                                          "connection.autoconnect", "no"])
    if not disable_autoconnect.success:
        raise HTTPException(500, "Failed to disable autoconnect")
    return Response(status_code=200)


@router.get("/displays", responses={
    200: {"description": "List of connected displays retrieved successfully"},
    204: {"description": "No connected displays found"},
    500: {"description": "Failed to retrieve list of connected displays"}
})
def connected_displays() -> list[ConnectedDisplay]:
    command = SysCmdExec.run(["sudo", "xrandr"])
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    regex = (r"(.+)\s(?:connected)(.*)\s(\d+x\d+)\+(\d+\+\d+)\s(.*?)\(.+\n"
             r"((\s+\d+x\d+\w*\s+.*\n)+)")
    data: list[tuple[str]] = re.findall(regex, command.output)
    result = []
    for i in data:
        # i[0] - display name, i[1] - is primary?, i[2] - resolution
        # i[3] - position, i[4] - rotation and reflect, i[5] - resolutions
        width, height = map(int, i[2].split("x"))
        x, y = map(int, i[3].split("+"))
        if i[4]:
            rotation, reflect = i[4].split()[0], " ".join(i[4].split()[1:])
        else:
            rotation, reflect = "normal", "normal"
        result.append(ConnectedDisplay(
            name=i[0],
            primary=bool(i[1]),
            resolution=DisplayResolution(width=width, height=height),
            position=DisplayPosition(x=x, y=y),
            rotation=rotation,
            reflect=reflect,
            resolutions=[s.split()[0] for s in i[5].splitlines()]
        ))
    return result if result else Response(status_code=204)


@router.get("/displays/config", response_model_exclude_none=True,
            responses={**system_responses})
def displays_config() -> list[DisplayConfig]:
    if not xrandr_config.exists():
        return Response(status_code=204)

    xrandr_data = xrandr_config.read_text("utf-8")
    if not xrandr_data:
        return Response(status_code=204)

    result = []
    for line in xrandr_data.splitlines():
        args = xrandr_to_dict(line.split())
        display = DisplayConfig(name=args["--output"])

        display.primary = "--primary" in args
        if "--resolution" in args:
            width, height = args["--mode"].split("x")
            display.resolution.width, display.resolution.height = width, height
        if "--rotation" in args:
            display.rotation = args["--rotation"]
        if "--position" in args:
            x, y = args["--position"].split("x")
            display.position = DisplayPosition(x=x, y=y)
        if "--reflect" in args:
            display.reflect = args["--reflect"]
        result.append(display)

    return result


@router.post("/displays/config", responses={**system_responses})
def set_display_config(display: DisplayConfig) -> Response:
    args = ["sudo", "xrandr", "--output", display.name]
    if display.resolution:
        width, height = display.resolution.width, display.resolution.height
        args.extend(["--mode", f"{width}x{height}"])
    if display.rotation:
        args.extend(["--rotation", display.rotation])
    if display.position:
        x, y = display.position.x, display.position.y
        args.extend(["--pos", f"{x}x{y}"])
    if display.reflect:
        args.extend(["--reflect", display.reflect])
    if display.primary:
        args.append("--primary")

    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(500, "Command execution failed")

    if not xrandr_config.exists():
        xrandr_config.write_text(" ".join(args), "utf-8")
        return Response(status_code=200)

    xrandr_data = xrandr_config.read_text("utf-8")
    if display.name not in xrandr_data:
        xrandr_data = f'{" ".join(args)}\n{xrandr_data}'
        xrandr_config.write_text(xrandr_data, "utf-8")
        return Response(status_code=200)

    stored_args = []
    xrandr_data = xrandr_data.splitlines()
    for line in xrandr_data:
        if display.name in line:
            stored_args = line.split()
            xrandr_data.remove(line)
            break

    merged_args = xrandr_to_dict(stored_args) | xrandr_to_dict(args)
    merged_args = [f"{k} {v}" if v else k for (k, v) in merged_args.items()]
    if display.primary:
        xrandr_data = [i.replace(" --primary", "")
                       if " --primary" in i else i for i in xrandr_data]
    xrandr_data.insert(0, " ".join(merged_args))
    xrandr_config.write_text("\n".join(xrandr_data), "utf-8")
    return Response(status_code=200)


@router.delete("/displays/config", responses={
    200: {"description": "Display configuration deleted successfully"},
    204: {"description": "Displays configuration not created"},
    404: {"description": "Display configuration not found"}
})
def delete_display_config(display_name: str = Body()) -> Response:
    if not xrandr_config.exists():
        return Response(status_code=204)

    xrandr_data = xrandr_config.read_text("utf-8")
    if display_name not in xrandr_data:
        raise HTTPException(404, "Display configuration not found")

    xrandr_data = xrandr_data.splitlines()
    for line in xrandr_data:
        if display_name in line:
            xrandr_data.remove(line)
            xrandr_config.write_text("\n".join(xrandr_data), "utf-8")
            break
    return Response(status_code=200)
