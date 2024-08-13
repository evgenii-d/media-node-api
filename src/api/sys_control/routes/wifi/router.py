import re
from fastapi import APIRouter, Body, HTTPException

from src.core.syscmd import SysCmdExec
from src.api.sys_control.schemas import (WifiInterfaceSchema,
                                         SavedWifiConnectionSchema,
                                         ConnectWifiNetworkSchema,
                                         WifiNetworkSchema)

router = APIRouter(prefix="/wifi")


@router.get("/interfaces", responses={
    200: {"description": "Wi-Fi interfaces retrieved successfully"},
    404: {"description": "Wi-Fi interfaces not found"},
    502: {"description": "Failed to retrieve Wi-Fi interfaces"}
}, status_code=200)
def wifi_interfaces() -> list[WifiInterfaceSchema]:
    command = SysCmdExec.run(["sudo", "nmcli", "-t", "device", "status"])
    if not command.success:
        raise HTTPException(502, "Command execution failed")

    result = re.findall(r"(\S.+)(?:\:wifi\:)(.+?):", command.output)
    if result:
        return [WifiInterfaceSchema(name=i[0], status=i[1]) for i in result]
    raise HTTPException(404, "Wi-Fi interfaces not found")


@router.get("/connections", responses={
    200: {"description": "Wi-Fi connections retrieved successfully"},
    404: {"description": "Wi-Fi connections not found"},
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
    if result:
        return result
    raise HTTPException(404, "Wi-Fi connections not found")


@router.delete("/connections/{ssid}", responses={
    204: {"description": "Wi-Fi connection deleted successfully"},
    502: {"description": "Failed to delete Wi-Fi connection"}
}, status_code=204)
def delete_saved_wifi_connection(ssid: str) -> None:
    args = ["sudo", "nmcli", "connection", "delete", ssid]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to delete {ssid}")


@router.post("/connect/{ssid}", responses={
    204: {"description": "Successfully connected to the Wi-Fi network"},
    502: {"description": "An error occurred while attempting to "
          "connect to the Wi-Fi network"}
}, status_code=204)
def connect_wifi_network(ssid: str,
                         data: ConnectWifiNetworkSchema | None = None
                         ) -> None:
    connect_args = ["sudo", "nmcli", "device", "wifi", "connect", ssid]

    if data:
        if data.password:
            connect_args.extend(["password", data.password])

        if data.interface:
            connect_args.extend(["ifname", data.interface])

    connect = SysCmdExec.run(connect_args)
    if not connect.success:
        raise HTTPException(502, f"Failed to connect to '{ssid}'")

    enable_autoconnect = SysCmdExec.run(["sudo", "nmcli", "connection",
                                         "modify", ssid,
                                         "connection.autoconnect", "yes"])
    if not enable_autoconnect.success:
        message = f"Failed to enable autoconnect for '{ssid}'"
        raise HTTPException(502, message)


@router.post("/disconnect/{ssid}", responses={
    204: {"description": "Successfully disconnected from the Wi-Fi network"},
    502: {"description": "An error occurred while attempting to "
          "disconnect from the Wi-Fi network"}
}, status_code=204)
def disconnect_wifi_network(ssid: str) -> None:
    disconnect = SysCmdExec.run(["sudo", "nmcli", "connection", "down", ssid])
    if not disconnect.success:
        raise HTTPException(502, f"Failed to disconnect '{ssid}'")

    disable_autoconnect = SysCmdExec.run(["sudo", "nmcli", "connection",
                                          "modify", ssid,
                                          "connection.autoconnect", "no"])
    if not disable_autoconnect.success:
        raise HTTPException(502, "Failed to disable autoconnect")


@router.get("/{interface}/networks", responses={
    200: {"description": "Available Wi-Fi networks retrieved successfully"},
    404: {"description": "Wi-Fi networks not found"},
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
    if result:
        return result
    raise HTTPException(404, "Wi-Fi networks not found")
