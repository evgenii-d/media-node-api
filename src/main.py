import logging
from typing import Annotated
import uvicorn
from fastapi import FastAPI, HTTPException, Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.config import VERSION_FILE, config_manager
from src.schemas import ConfigSchema
from src.constants import AppDir
from src.api.openapi.router import router as openapi
from src.api.media_files.router import router as media_files
from src.api.media_player.router import router as media_player
from src.api.playlists.router import router as playlists
from src.api.system_control.router import router as system_control
from src.api.web_browser.router import router as web_browser

app_config = ConfigSchema.model_validate(config_manager.load_section())
app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static",
          StaticFiles(directory=AppDir.STATIC.value, html=True),
          name="static_files")

if app_config.openapi:
    app.include_router(openapi)
else:
    app.openapi_url = None
app.include_router(system_control)
app.include_router(web_browser)
app.include_router(media_player)
app.include_router(media_files)
app.include_router(playlists)


@app.get("/app/node-name", responses={
    200: {"description": "Node name retrieved successfully"}
}, status_code=200)
def node_name() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return config.nodeName


@app.put("/app/node-name/{new_name}", responses={
    204: {"description": "Node name updated successfully"}
}, status_code=204)
def change_node_name(new_name: Annotated[str, Path(max_length=40)]) -> None:
    data = ConfigSchema(nodeName=new_name.strip())
    config_manager.save_section(data.model_dump(exclude_none=True))


@app.get("/app/version", responses={
    200: {"description": "App version retrieved successfully"},
    404: {"description": "App version not found"}
}, status_code=200)
def app_version() -> str:
    try:
        return VERSION_FILE.read_text("utf-8")
    except FileNotFoundError as error:
        raise HTTPException(404, "App version not found") from error


if __name__ == "__main__":
    uvicorn.run(
        app="src.main:app",
        host=app_config.host,
        port=app_config.port,
        reload=app_config.reload,
        log_level=logging.DEBUG if app_config.debug else logging.INFO
    )
