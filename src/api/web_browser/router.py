from typing import Literal
from fastapi import APIRouter, HTTPException

from src.core.syscmd import SysCmdExec
from src.api.web_browser.config import config_manager
from src.api.web_browser.schemas import ConfigSchema


router = APIRouter(prefix="/web-browser", tags=["web browser"])


@router.get("/config", responses={
    200: {"description": "Web browser configuration retrieved successfully"}
}, status_code=200)
def web_browser_config() -> ConfigSchema:
    return ConfigSchema.model_validate(config_manager.load_section())


@router.patch("/config", responses={
    204: {"description": "Web browser configuration updated successfully"}
}, status_code=204)
def update_web_browser_config(data: ConfigSchema) -> None:
    if data.url == "":
        data.url = "about:blank"
    config_manager.save_section(data.model_dump(exclude_none=True))


@router.post("/service/{command}", responses={
    204: {"description": "Web browser service command executed successfully"},
    502: {"description": "Failed to execute web browser service command"}
}, status_code=204)
def web_browser_service(command: Literal["start", "stop", "restart"]) -> None:
    args = ["systemctl", "--user", command, "web-browser.service"]
    if not SysCmdExec.run(args).success:
        raise HTTPException(502, f"Failed to execute '{command}' command")
