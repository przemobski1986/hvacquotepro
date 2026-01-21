from pydantic import BaseModel, EmailStr

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class MeOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    tenant_id: str
