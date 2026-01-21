from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.i18n import t
from app.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.core import User
from app.schemas.auth import LoginIn, TokenOut, MeOut

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.invalid_credentials"))
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.inactive_user"))

    access = create_access_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    refresh = create_refresh_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    # HTTP-only cookie for refresh token
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=False,  # set True behind TLS
        samesite="lax",
        max_age=14 * 24 * 3600,
        path="/",
    )
    return TokenOut(access_token=access)

@router.post("/refresh", response_model=TokenOut)
def refresh(request: Request, response: Response):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.unauthorized"))
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.unauthorized"))
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t(request, "auth.unauthorized"))
    access = create_access_token(subject=payload["sub"], tenant_id=payload["tenant_id"], role=payload["role"])
    return TokenOut(access_token=access)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return {"ok": True}
