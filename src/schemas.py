from typing import Annotated
from pydantic import BaseModel, StringConstraints


class ConfigSchema(BaseModel):
    host: str = None
    port: int = None
    reload: bool = None
    debug: bool = None
    openapi: bool = None
    nodeName: Annotated[str, StringConstraints(
        strip_whitespace=True, max_length=40)] = None
