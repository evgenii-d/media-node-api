from typing import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints


class ConfigSchema(BaseModel):
    nodeName: Optional[Annotated[str, StringConstraints(
        strip_whitespace=True, max_length=40)]] = None
    audioDevice: Optional[str] = None
    volume: Optional[int] = Field(default=None, ge=0, le=150)
