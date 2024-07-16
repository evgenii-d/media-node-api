from typing import Optional
from pydantic import BaseModel


class ConfigSchema(BaseModel):
    autostart: Optional[bool] = None
    webPage: Optional[str] = None
