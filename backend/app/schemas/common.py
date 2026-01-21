from pydantic import BaseModel

class Msg(BaseModel):
    message: str

class IdResponse(BaseModel):
    id: str
