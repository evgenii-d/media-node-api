from pydantic import BaseModel


class AudioDeviceSchema(BaseModel):
    id: int
    name: str
