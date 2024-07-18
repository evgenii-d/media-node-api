import re
import uuid
import shutil
import socket
import zipfile
from typing import Literal
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
    502: {"description": "Command execution failed"}
}

service_responses = {
    204: {"description": "Service operation completed"},
    500: {"description": "Service operation failed"}
}


def xrandr_to_dict(xrandr_args: list[str]) -> dict[str, str]:
    result = {}
    for i, word in enumerate(xrandr_args):
        if word in ["sudo", "xrandr", "--primary"]:
            result.update({word: None})
        elif "--" in word:
            result.update({word: xrandr_args[i+1]})
    return result


@router.get("/name", status_code=200)
def node_name() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return config.nodeName


@router.put("/name", status_code=204)
def update_node_name(value: str = Body(max_length=40)) -> None:
    data = ConfigSchema(nodeName=value.strip())
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get("/hostname", status_code=200)
def hostname() -> str:
    return socket.gethostname()


@router.post("/hostname", responses={
    200: {"description": "New hostname generated successfully"}
}, status_code=200)
def change_hostname() -> str:
    data = ConfigSchema(generatedHostname=f"node-{uuid.uuid4().hex}")
    config_manager.save_section(data.model_dump(exclude_none=True))
    return data.generatedHostname


@router.post("/poweroff", responses={**system_responses}, status_code=200)
def system_poweroff() -> Response:
    args = ["sudo", "shutdown", "now"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 502)


@router.post("/reboot", responses={**system_responses}, status_code=200)
def system_reboot() -> Response:
    args = ["sudo", "shutdown", "-r", "now"]
    command = SysCmdExec.run(args)
    return Response(status_code=200 if command.success else 502)


@router.put("/static", responses={
    200: {"description": "File successfully uploaded"},
    400: {"description": "Invalid file type. Accept only .zip files"}
}, status_code=200)
async def static_upload(file: UploadFile) -> Response:
    file.filename = "archive.zip"
    archive = AppDir.STATIC.value/file.filename
    await aio_save_files_to_dir([file], AppDir.STATIC.value)

    if not zipfile.is_zipfile(archive):
        archive.unlink()
        raise HTTPException(400, (f"Invalid file type: {file.content_type}. "
                                  "Only .zip files allowed."))

    # remove all files and folders from the "public" directory
    for item in (AppDir.STATIC_PUBLIC.value).glob("*"):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(True)
    shutil.unpack_archive(archive, AppDir.STATIC_PUBLIC.value)


@router.get("/audio/devices", responses={
    200: {"description": "Audio devices retrieved successfully"},
    502: {"description": "Failed to retrieve audio devices"}
}, status_code=200)
def audio_devices() -> list[AudioDeviceSchema]:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    result = []
    devices = re.findall(r"index: (\d+)\n.*name: <(.*)>", command.output)
    try:
        for d in devices:
            result.append(AudioDeviceSchema(id=int(d[0]), name=d[1]))
    except IndexError as e:
        raise HTTPException(502, "Failed to retrieve audio devices") from e
    return result


@router.get("/audio/default-device", responses={
    200: {"description": "Default Audio device retrieved successfully"},
    502: {"description": "Failed to retrieve default audio device"}
}, status_code=200)
def default_audio_device() -> AudioDeviceSchema:
    command = SysCmdExec.run(["pacmd", "list-sinks"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    device = re.search(r"\* index: (\d+)\n.*name: <(.+)>", command.output)
    try:
        device_id, device_name = int(device.group(1)), device.group(2)
        return AudioDeviceSchema(id=device_id, name=device_name)
    except (IndexError, AttributeError) as e:
        message = "Failed to retrieve default audio device"
        raise HTTPException(502, message) from e


@router.post("/audio/default-device", responses={
    204: {"description": "Default audio device set successfully"},
    502: {"description": "Command execution failed"}
}, status_code=204)
def set_default_audio_device(device: str = Body()) -> None:
    command = SysCmdExec.run(["pacmd", "set-default-sink", device])
    if not command.success:
        raise HTTPException(502, "Command execution failed")
    data = ConfigSchema(audioDevice=device)
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get("/audio/volume", responses={
    200: {"description": "Current audio volume retrieved successfully"},
    502: {"description": "Failed to retrieve current audio volume"}
}, status_code=200)
def audio_volume() -> int:
    command = SysCmdExec.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    if not command.success:
        raise HTTPException(502, "Failed to retrieve current audio volume")
    volume_level = int(command.output.strip().split()[4][:-1])
    return volume_level


@router.post("/audio/volume", responses={
    204: {"description": "Audio volume set successfully"},
    502: {"description": "Failed to set audio volume"}
}, status_code=204)
def set_audio_volume(level: int = Body(ge=0, le=150)) -> None:
    args = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"]
    command = SysCmdExec.run(args)
    if not command.success:
        raise HTTPException(502, "Failed to set audio volume")
    data = ConfigSchema(volume=level)
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.get("/wifi/interfaces", responses={
    200: {"description": "List of Wi-Fi interfaces retrieved successfully"},
    502: {"description": "Failed to retrieve list of Wi-Fi interfaces"}
}, status_code=200)
def wifi_interfaces() -> list[WifiInterfaceSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "device", "status"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    result = re.findall(r"(\S.+)(?:\:wifi\:)(.+?):", command.output)
    return [WifiInterfaceSchema(name=i[0], status=i[1]) for i in result]


@router.get("/wifi/connections", responses={
    200: {"description": "Wi-Fi connections retrieved successfully"},
    502: {"description": "Failed to retrieve Wi-Fi connections"}
}, status_code=200)
def saved_wifi_connections() -> list[SavedWifiConnectionSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "connection", "show"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    result = []
    for line in command.output.splitlines():
        if "wireless" in line:
            data = [i.strip() for i in line.split(":")]
            item = SavedWifiConnectionSchema(ssid=data[0], interface=data[3])
            result.append(item)
    return result


@router.delete("/wifi/connections/{ssid}", responses={
    204: {"description": "Wi-Fi connection deleted successfully"},
    502: {"description": "Failed to delete Wi-Fi connection"}
}, status_code=204)
def delete_saved_wifi_connection(ssid: str) -> None:
    args = ["sudo", "nmcli", "connection", "delete", ssid]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to delete {ssid}")


@router.get("/wifi/{interface}/networks", responses={
    200: {"description": "Available Wi-Fi networks retrieved successfully"},
    502: {"description": "Failed to retrieve Wi-Fi networks"}
}, status_code=200)
def available_wifi_networks(interface: str) -> list[WifiNetworkSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "device",
                              "wifi", "list", "ifname", interface])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

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
    return result


@router.post("/wifi/connect", responses={
    204: {"description": "Successfully connected to the Wi-Fi network"},
    500: {"description": "Failed to connect to the Wi-Fi network"},
    502: {"description": "Failed to enable autoconnect for the Wi-Fi network"}
}, status_code=204)
def connect_wifi_network(data: ConnectWifiNetworkSchema) -> None:
    connect_args = ["sudo", "nmcli", "device", "wifi", "connect", data.ssid]

    if data.password:
        connect_args.extend(["password", data.password])

    if data.interface:
        connect_args.extend(["ifname", data.interface])

    connect = SysCmdExec.run(connect_args)
    if not connect.success:
        raise HTTPException(500, "Failed to connect to the Wi-Fi network")

    enable_autoconnect = SysCmdExec.run(["sudo", "nmcli", "connection",
                                         "modify", data.ssid,
                                         "connection.autoconnect", "yes"])
    if not enable_autoconnect.success:
        message = "Failed to enable autoconnect for the Wi-Fi network"
        raise HTTPException(502, message)


@router.post("/wifi/disconnect", responses={
    204: {"description": "Successfully disconnected from the Wi-Fi network"},
    500: {"description": "Failed to disconnect from the Wi-Fi network"},
    502: {"description": "Failed to disable autoconnect for the Wi-Fi network"}
}, status_code=204)
def disconnect_wifi_network(ssid: str = Body()) -> None:
    disconnect = SysCmdExec.run(["sudo", "nmcli", "connection", "down", ssid])
    if not disconnect.success:
        raise HTTPException(500, "Failed to disconnect interface")

    disable_autoconnect = SysCmdExec.run(["sudo", "nmcli", "connection",
                                          "modify", ssid,
                                          "connection.autoconnect", "no"])
    if not disable_autoconnect.success:
        raise HTTPException(502, "Failed to disable autoconnect")


@router.get("/displays", responses={
    200: {"description": "List of connected displays retrieved successfully"},
    502: {"description": "Failed to retrieve list of connected displays"}
}, status_code=200)
def connected_displays() -> list[ConnectedDisplay]:
    command = SysCmdExec.run(["sudo", "xrandr"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

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
            rotation = i[4].split()[0]
            reflect = "".join(filter(str.isupper, i[4])).lower()
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
    return result


@router.post("/displays/detect/{action}", responses={**service_responses},
             status_code=204)
def toggle_displays_detection(action: Literal["start", "stop"]) -> None:
    args = ["systemctl", "--user", action, "display-detector.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=204 if command.success else 500)


@ router.get("/displays/config", responses={
    200: {"description": "Displays configuration retrieved successfully"},
    404: {"description": "Displays configuration not created"}
}, status_code=200, response_model_exclude_none=True)
def displays_config() -> list[DisplayConfig]:
    if not xrandr_config.exists():
        raise HTTPException(404, "Displays configuration not created")

    xrandr_data = xrandr_config.read_text("utf-8")
    if not xrandr_data:
        raise HTTPException(404, "Displays configuration not created")

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


@ router.put("/displays/config", responses={
    204: {"description": "Display configuration updated successfully"},
    500: {"description": "Failed to update display configuration"}
}, status_code=204)
def update_display_config(display: DisplayConfig) -> None:
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
        raise HTTPException(502, "Command execution failed")

    if not xrandr_config.exists():
        xrandr_config.write_text(" ".join(args), "utf-8")
        return

    xrandr_data = xrandr_config.read_text("utf-8")
    if display.name not in xrandr_data:
        xrandr_data = f'{" ".join(args)}\n{xrandr_data}'
        xrandr_config.write_text(xrandr_data, "utf-8")
        return

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


@ router.delete("/displays/config/{display_name}", responses={
    204: {"description": "Display configuration deleted successfully"},
    404: {"description": "Display configuration not found"}
}, status_code=204)
def delete_display_config(display_name: str) -> None:
    if not xrandr_config.exists():
        raise HTTPException(404, "Displays configuration not created")

    xrandr_data = xrandr_config.read_text("utf-8")
    if display_name not in xrandr_data:
        raise HTTPException(404, "Display configuration not found")

    xrandr_data = xrandr_data.splitlines()
    for line in xrandr_data:
        if display_name in line:
            xrandr_data.remove(line)
            xrandr_config.write_text("\n".join(xrandr_data), "utf-8")
            break
