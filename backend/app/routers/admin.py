from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import require_roles
from app.i18n import t
from app.models.core import TenantSettings, User
from app.schemas.common import Msg
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/settings")
def get_settings(user=Depends(require_roles("admin")), db: Session = Depends(get_db)):
    s = db.query(TenantSettings).filter(TenantSettings.tenant_id == user.tenant_id).first()
    if not s:
        s = TenantSettings(tenant_id=user.tenant_id)
        db.add(s); db.commit(); db.refresh(s)
    return s.__dict__ | {"tenant_id": user.tenant_id}

@router.put("/settings")
def update_settings(payload: dict, user=Depends(require_roles("admin")), db: Session = Depends(get_db)):
    s = db.query(TenantSettings).filter(TenantSettings.tenant_id == user.tenant_id).first()
    if not s:
        s = TenantSettings(tenant_id=user.tenant_id)
        db.add(s)
    for k in ["min_margin_pct","block_below_min_margin","default_vat_rate","quote_prefix","logo_url","company_name","company_address","company_nip"]:
        if k in payload:
            setattr(s, k, payload[k])
    db.commit()
    return {"ok": True}

@router.get("/users")
def list_users(user=Depends(require_roles("admin")), db: Session = Depends(get_db)):
    rows = db.query(User).filter(User.tenant_id == user.tenant_id).all()
    return [{"id": r.id, "email": r.email, "role": r.role, "is_active": r.is_active} for r in rows]

@router.post("/users")
def create_user(payload: dict, request: Request, user=Depends(require_roles("admin")), db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")
    role = payload.get("role", "sales")
    if not email or not password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=t(request, "common.validation_failed"))
    u = User(tenant_id=user.tenant_id, email=email, password_hash=hash_password(password), role=role, is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id}

@router.patch("/users/{user_id}/deactivate")
def deactivate(user_id: str, user=Depends(require_roles("admin")), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.tenant_id == user.tenant_id, User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="not found")
    u.is_active = False
    db.commit()
    return {"ok": True}
