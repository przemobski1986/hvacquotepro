from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user
from app.i18n import t
from app.models.quoting import Deal, Quote, QuoteParam, QuoteLine, QuoteOverhead
from app.models.core import TenantSettings
from app.schemas.quoting import (
    DealIn, DealOut, QuoteCreate, QuoteOut, QuoteParamIn,
    QuoteLineIn, QuoteLineOut, QuoteOverheadIn, QuoteTotalsOut, ValidationIssue
)
from app.services.pricing import recalc_line_prices, recalc_quote_totals
from app.services.validation import validate_quote
from app.services.rules import generate_lines_from_rules
import datetime

router = APIRouter(prefix="/quoting", tags=["quoting"])

def _quote_no(prefix: str, seq: int) -> str:
    year = datetime.date.today().year
    return f"{prefix}-{year}-{seq:04d}"

@router.get("/deals", response_model=list[DealOut])
def list_deals(status: str | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Deal).filter(Deal.tenant_id == user.tenant_id)
    if status:
        q = q.filter(Deal.status == status)
    rows = q.order_by(Deal.updated_at.desc()).all()
    return [DealOut(**{k:getattr(r,k) for k in DealOut.model_fields.keys() if k != "id"}, id=r.id) for r in rows]

@router.post("/deals", response_model=DealOut)
def create_deal(payload: DealIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    d = Deal(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(d); db.commit(); db.refresh(d)
    return DealOut(**payload.model_dump(), id=d.id)

@router.patch("/deals/{deal_id}/status")
def set_deal_status(deal_id: str, payload: dict, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    d = db.query(Deal).filter(Deal.tenant_id == user.tenant_id, Deal.id == deal_id).first()
    if not d:
        raise HTTPException(status_code=404, detail=t(request, "common.not_found"))
    d.status = payload.get("status", d.status)
    db.commit()
    return {"ok": True}

@router.post("/deals/{deal_id}/quotes", response_model=QuoteOut)
def create_quote(deal_id: str, payload: QuoteCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == user.tenant_id).first()
    if not settings:
        settings = TenantSettings(tenant_id=user.tenant_id)
        db.add(settings); db.commit(); db.refresh(settings)

    # simple per-tenant sequence: count quotes
    seq = db.query(Quote).filter(Quote.tenant_id == user.tenant_id).count() + 1
    qno = _quote_no(settings.quote_prefix or "Q", seq)
    quote = Quote(
        tenant_id=user.tenant_id,
        deal_id=deal_id,
        quote_no=qno,
        scenario=payload.scenario,
        vat_rate=float(settings.default_vat_rate),
        created_by_user_id=user.id,
    )
    db.add(quote); db.commit(); db.refresh(quote)
    return QuoteOut(
        id=quote.id, deal_id=quote.deal_id, quote_no=quote.quote_no,
        scenario=quote.scenario, currency=quote.currency, vat_rate=float(quote.vat_rate),
        pricing_version=int(quote.pricing_version),
    )

@router.get("/quotes/{quote_id}", response_model=QuoteOut)
def get_quote(quote_id: str, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Quote).filter(Quote.tenant_id == user.tenant_id, Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail=t(request, "common.not_found"))
    return QuoteOut(
        id=q.id, deal_id=q.deal_id, quote_no=q.quote_no, scenario=q.scenario,
        currency=q.currency, vat_rate=float(q.vat_rate), pricing_version=int(q.pricing_version),
    )

@router.put("/quotes/{quote_id}/params")
def upsert_params(quote_id: str, payload: list[QuoteParamIn], user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Replace all params for simplicity
    db.query(QuoteParam).filter(QuoteParam.tenant_id == user.tenant_id, QuoteParam.quote_id == quote_id).delete()
    for p in payload:
        db.add(QuoteParam(tenant_id=user.tenant_id, quote_id=quote_id, **p.model_dump()))
    db.commit()
    return {"ok": True, "count": len(payload)}

@router.post("/quotes/{quote_id}/generate-lines")
def generate_lines(quote_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    created = generate_lines_from_rules(db, user.tenant_id, quote_id)
    db.commit()
    return {"ok": True, "created": created}

@router.get("/quotes/{quote_id}/lines", response_model=list[QuoteLineOut])
def list_lines(quote_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(QuoteLine).filter(QuoteLine.tenant_id == user.tenant_id, QuoteLine.quote_id == quote_id).order_by(QuoteLine.sort_order.asc()).all()
    out=[]
    for r in rows:
        d = {
            "id": r.id,
            "line_type": r.line_type,
            "name": r.name,
            "unit": r.unit,
            "qty": float(r.qty),
            "purchase_price_net": float(r.purchase_price_net),
            "markup_pct": float(r.markup_pct),
            "sell_price_net_unit": float(r.sell_price_net_unit),
            "sell_price_net_total": float(r.sell_price_net_total),
            "source": r.source,
            "sort_order": int(r.sort_order),
            "ref_id": r.ref_id,
        }
        out.append(QuoteLineOut(**d))
    return out

@router.post("/quotes/{quote_id}/lines", response_model=dict)
def add_line(quote_id: str, payload: QuoteLineIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    line = QuoteLine(tenant_id=user.tenant_id, quote_id=quote_id, **payload.model_dump(exclude={"sell_price_net_unit","sell_price_net_total"}))
    recalc_line_prices(line)
    db.add(line); db.commit(); db.refresh(line)
    return {"id": line.id}

@router.put("/quotes/{quote_id}/lines/{line_id}")
def update_line(quote_id: str, line_id: str, payload: QuoteLineIn, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    line = db.query(QuoteLine).filter(QuoteLine.tenant_id == user.tenant_id, QuoteLine.quote_id == quote_id, QuoteLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail=t(request, "common.not_found"))
    for k,v in payload.model_dump().items():
        setattr(line, k, v)
    recalc_line_prices(line)
    db.commit()
    return {"ok": True}

@router.delete("/quotes/{quote_id}/lines/{line_id}")
def delete_line(quote_id: str, line_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(QuoteLine).filter(QuoteLine.tenant_id == user.tenant_id, QuoteLine.quote_id == quote_id, QuoteLine.id == line_id).delete()
    db.commit()
    return {"ok": True}

@router.put("/quotes/{quote_id}/overheads")
def set_overheads(quote_id: str, payload: list[QuoteOverheadIn], user=Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(QuoteOverhead).filter(QuoteOverhead.tenant_id == user.tenant_id, QuoteOverhead.quote_id == quote_id).delete()
    for oh in payload:
        db.add(QuoteOverhead(tenant_id=user.tenant_id, quote_id=quote_id, **oh.model_dump()))
    db.commit()
    return {"ok": True, "count": len(payload)}

@router.post("/quotes/{quote_id}/recalculate", response_model=QuoteTotalsOut)
def recalc(quote_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Quote).filter(Quote.tenant_id == user.tenant_id, Quote.id == quote_id).first()
    totals = recalc_quote_totals(db, user.tenant_id, quote_id, float(q.vat_rate))
    return QuoteTotalsOut(
        cost_net=float(totals.cost_net), sell_net=float(totals.sell_net),
        vat_amount=float(totals.vat_amount), sell_gross=float(totals.sell_gross),
        margin_net=float(totals.margin_net), margin_pct=float(totals.margin_pct),
    )

@router.get("/quotes/{quote_id}/validation", response_model=list[ValidationIssue])
def validation(quote_id: str, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return validate_quote(db, request, user.tenant_id, quote_id)
