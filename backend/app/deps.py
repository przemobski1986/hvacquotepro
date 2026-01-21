from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db import get_db
from app.security import decode_token
from app.i18n import t
from app.models.core import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.unauthorized"))
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.unauthorized"))
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.inactive_user"))
    return user

def require_roles(*roles: str):
    def _checker(request: Request, user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t(request, "auth.forbidden"))
        return user
    return _checker
