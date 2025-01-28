import logging
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.config import config_manager
from src.schemas import ConfigSchema
from src.constants import AppDir
from src.api.openapi.router import router as openapi
from src.api.app.router import router as app_router
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
app.mount(
    "/static_files",
    StaticFiles(directory=AppDir.STATIC_FILES.value, html=True),
    name="static_files"
)

if app_config.openapi:
    app.include_router(openapi)
else:
    app.openapi_url = None
app.include_router(app_router)
app.include_router(system_control)
app.include_router(web_browser)
app.include_router(media_player)
app.include_router(media_files)
app.include_router(playlists)


if __name__ == "__main__":
    uvicorn.run(
        app="src.main:app",
        host=app_config.host,
        port=app_config.port,
        reload=app_config.reload,
        log_level=logging.DEBUG if app_config.debug else logging.INFO
    )
