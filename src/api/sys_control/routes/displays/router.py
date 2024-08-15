import re
from typing import Literal
from fastapi import APIRouter, HTTPException

from src.core.syscmd import SysCmdExec
from src.api.sys_control.config import xrandr_config
from src.api.sys_control.routes.displays.schemas import (
    ConnectedDisplay,
    DisplayPosition,
    DisplayResolution,
    DisplayConfig
)


router = APIRouter(prefix="/displays")


def xrandr_to_dict(xrandr_args: list[str]) -> dict[str, str]:
    result = {}
    for i, word in enumerate(xrandr_args):
        if word in ["xrandr", "--primary"]:
            result.update({word: None})
        elif "--" in word:
            result.update({word: xrandr_args[i+1]})
    return result


@router.get("/", responses={
    200: {"description": "List of connected displays retrieved successfully"},
    404: {"description": "Connected displays not found"},
    502: {"description": "Failed to retrieve connected displays"}
}, status_code=200)
def connected_displays() -> list[ConnectedDisplay]:
    command = SysCmdExec.run(["xrandr"])
    if not command.success:
        raise HTTPException(502, "Failed to retrieve connected displays")

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
    if result:
        return result
    raise HTTPException(404, "Connected displays not found")


@router.post("/detect/{command}", responses={
    204: {"description": "Display detection command executed successfully"},
    502: {"description": "Failed to execute display detection command"}
}, status_code=204)
def displays_detection(command: Literal["start", "stop", "restart"]) -> None:

    args = ["systemctl", "--user", command, "display-detector.service"]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to {command} the display detection")


@router.get("/config", responses={
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

        display.primary = True if "--primary" in args else None
        if "--mode" in args:
            width, height = args["--mode"].split("x")
            display.resolution = DisplayResolution(width=width, height=height)
        if "--rotation" in args:
            display.rotation = args["--rotation"]
        if "--position" in args:
            x, y = args["--position"].split("x")
            display.position = DisplayPosition(x=x, y=y)
        if "--reflect" in args:
            display.reflect = args["--reflect"]
        result.append(display)
    return result


@router.post("/config", responses={
    204: {"description": "Display configuration applied successfully"},
    502: {"description": "Failed to process display configuration"}
}, status_code=204)
def apply_display_config(display: DisplayConfig) -> None:
    args = ["xrandr", "--output", display.name]
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

    if not SysCmdExec.run(args).success:
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


@router.delete("/config/{display_name}", responses={
    204: {"description": "Display configuration deleted successfully"},
    404: {"description": "Display configuration not found"}
}, status_code=204)
def delete_display_config(display_name: str) -> None:
    if not xrandr_config.exists():
        raise HTTPException(404, "Displays configuration not created")

    xrandr_data = xrandr_config.read_text("utf-8").splitlines()
    for line in xrandr_data:
        if display_name in line.split():
            xrandr_data.remove(line)
            xrandr_config.write_text("\n".join(xrandr_data), "utf-8")
            return
    raise HTTPException(404, "Display configuration not found")
