from fastapi import APIRouter, Response

from src.core.syscmd import SysCmdExec
from src.api.web_browser.config import config_manager
from src.api.web_browser.schemas import ConfigSchema


router = APIRouter(prefix="/web-browser", tags=["web browser"])

service_responses = {
    204: {"description": "Service operation completed"},
    500: {"description": "Service operation failed"}
}


@router.get("/config")
def web_browser_config() -> ConfigSchema:
    return ConfigSchema.model_validate(config_manager.load_section())


@router.post("/config")
def set_web_browser_config(data: ConfigSchema) -> Response:
    if data.webPage == "":
        data.webPage = "about:blank"
    config_manager.save_section(data.model_dump(exclude_none=True))
    return Response(status_code=200)


@router.post("/start-service",
             status_code=204, responses={**service_responses})
def start_web_browser() -> Response:
    args = ["systemctl", "--user", "start", "web-browser.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=204 if command.success else 500)


@router.post("/stop-service",
             status_code=204, responses={**service_responses})
def stop_web_browser() -> Response:
    args = ["systemctl", "--user", "stop", "web-browser.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=204 if command.success else 500)


@router.post("/restart-service",
             status_code=204, responses={**service_responses})
def restart_web_browser() -> Response:
    args = ["systemctl", "--user", "restart", "web-browser.service"]
    command = SysCmdExec.run(args)
    return Response(status_code=204 if command.success else 500)
