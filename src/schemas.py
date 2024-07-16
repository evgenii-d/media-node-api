from pydantic import BaseModel


class AppConfigSchema(BaseModel):
    host: str = "0.0.0.0"
    port: int = 5000
    reload: bool = False
    debug: bool = False
    openapi: bool = False
