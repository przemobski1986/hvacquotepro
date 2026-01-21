from pydantic import BaseModel

class ClientIn(BaseModel):
    type: str
    name: str
    nip: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None

class ClientOut(ClientIn):
    id: str

class SiteIn(BaseModel):
    client_id: str
    name: str
    address_line: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    notes: str | None = None

class SiteOut(SiteIn):
    id: str
