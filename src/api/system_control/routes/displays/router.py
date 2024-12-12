import re
from typing import Literal
from fastapi import APIRouter, HTTPException

from src.core.syscmd import SysCmdExec
from src.api.system_control.config import XRANDR_CONFIG
from src.api.system_control.routes.displays.schemas import (
    ConnectedDisplay,
    DisplayPosition,
    DisplayResolution,
    DisplayConfig
)


router = APIRouter(prefix="/displays", tags=["displays"])


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
def list_connected_displays() -> list[ConnectedDisplay]:
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
        display_resolutions: list[DisplayResolution] = []
        refresh_rate: float = 0.0

        # Display width and height
        width, height = map(int, i[2].split("x"))

        # Display position
        x, y = map(int, i[3].split("+"))

        # Rotation and reflect
        if i[4]:
            rotation = i[4].split()[0]
            reflect = "".join(filter(str.isupper, i[4])).lower()
        else:
            rotation, reflect = "normal", "normal"

        # Current refresh rate
        rate_line = next(
            (line for line in i[5].splitlines() if "*" in line), None
        )
        if rate_line:
            match_rate = re.search(r"(\d+\.\d+)\*", rate_line)
            if match_rate:
                refresh_rate = float(match_rate.group(1))

        # Available display resolutions
        for line in i[5].splitlines():
            try:
                values = line.split()[0].split("x")
                display_resolutions.append(
                    DisplayResolution(
                        width=int(values[0]), height=int(values[1])
                    )
                )
            except ValueError:
                pass

        result.append(ConnectedDisplay(
            name=i[0],
            primary=bool(i[1]),
            resolution=DisplayResolution(width=width, height=height),
            rate=refresh_rate,
            position=DisplayPosition(x=x, y=y),
            rotation=rotation,
            reflect=reflect,
            resolutions=display_resolutions
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
    if not XRANDR_CONFIG.exists():
        raise HTTPException(404, "Displays configuration not created")

    xrandr_data = XRANDR_CONFIG.read_text("utf-8")
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
        if "--rate" in args:
            display.rate = args["--rate"]
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
    if display.rate:
        args.extend(["--rate", str(display.rate)])
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

    if not XRANDR_CONFIG.exists():
        XRANDR_CONFIG.write_text(" ".join(args), "utf-8")
        return

    xrandr_data = XRANDR_CONFIG.read_text("utf-8")
    if display.name not in xrandr_data:
        xrandr_data = f'{" ".join(args)}\n{xrandr_data}'
        XRANDR_CONFIG.write_text(xrandr_data, "utf-8")
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
    XRANDR_CONFIG.write_text("\n".join(xrandr_data), "utf-8")


@router.delete("/config/{display_name}", responses={
    204: {"description": "Display configuration deleted successfully"},
    404: {"description": "Display configuration not found"}
}, status_code=204)
def delete_display_config(display_name: str) -> None:
    if not XRANDR_CONFIG.exists():
        raise HTTPException(404, "Displays configuration not created")

    xrandr_data = XRANDR_CONFIG.read_text("utf-8").splitlines()
    for line in xrandr_data:
        if display_name in line.split():
            xrandr_data.remove(line)
            XRANDR_CONFIG.write_text("\n".join(xrandr_data), "utf-8")
            return
    raise HTTPException(404, "Display configuration not found")
