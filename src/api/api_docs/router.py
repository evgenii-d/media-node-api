from fastapi import APIRouter, FastAPI
from fastapi.openapi.docs import (get_redoc_html, get_swagger_ui_html,
                                  get_swagger_ui_oauth2_redirect_html)

STATIC_FILES = "/static/api-docs"
router = APIRouter(include_in_schema=False)
default_title = FastAPI().title
openapi_url = FastAPI().openapi_url
swagger_ui_oauth2_redirect_url = FastAPI().swagger_ui_oauth2_redirect_url


@router.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=default_title + " - Swagger UI",
        oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
        swagger_js_url=f"{STATIC_FILES}/swagger-ui-bundle.js",
        swagger_css_url=f"{STATIC_FILES}/swagger-ui.css",
        swagger_favicon_url=f"{STATIC_FILES}/favicon.png")


@router.get(swagger_ui_oauth2_redirect_url)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@router.get("/redoc")
async def redoc_html():
    return get_redoc_html(
        openapi_url=openapi_url,
        title=default_title + " - ReDoc",
        redoc_js_url=f"{STATIC_FILES}/redoc.standalone.js",
        redoc_favicon_url=f"{STATIC_FILES}/favicon.png",
        with_google_fonts=False)
