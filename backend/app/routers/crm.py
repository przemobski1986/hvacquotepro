from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user
from app.i18n import t
from app.models.crm import Client, Site
from app.schemas.crm import ClientIn, ClientOut, SiteIn, SiteOut

router = APIRouter(prefix="/crm", tags=["crm"])

@router.get("/clients", response_model=list[ClientOut])
def list_clients(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Client).filter(Client.tenant_id == user.tenant_id).order_by(Client.created_at.desc()).all()
    return [ClientOut(**{k:getattr(r,k) for k in ClientOut.model_fields.keys()}) | {"id": r.id} for r in rows]

@router.post("/clients", response_model=ClientOut)
def create_client(payload: ClientIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    c = Client(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return ClientOut(**payload.model_dump(), id=c.id)

@router.put("/clients/{client_id}", response_model=ClientOut)
def update_client(client_id: str, payload: ClientIn, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.tenant_id == user.tenant_id, Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=t(request, "common.not_found"))
    for k,v in payload.model_dump().items():
        setattr(c,k,v)
    db.commit(); db.refresh(c)
    return ClientOut(**payload.model_dump(), id=c.id)

@router.get("/sites", response_model=list[SiteOut])
def list_sites(client_id: str | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Site).filter(Site.tenant_id == user.tenant_id)
    if client_id:
        q = q.filter(Site.client_id == client_id)
    rows = q.order_by(Site.created_at.desc()).all()
    out=[]
    for r in rows:
        d = {k:getattr(r,k) for k in SiteOut.model_fields.keys() if k != "id"}
        out.append(SiteOut(**d, id=r.id))
    return out

@router.post("/sites", response_model=SiteOut)
def create_site(payload: SiteIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    s = Site(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return SiteOut(**payload.model_dump(), id=s.id)
