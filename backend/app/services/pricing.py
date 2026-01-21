from sqlalchemy.orm import Session
from app.models.quoting import QuoteLine, QuoteOverhead, QuoteTotals

def recalc_quote_totals(db: Session, tenant_id: str, quote_id: str, vat_rate: float) -> QuoteTotals:
    lines = db.query(QuoteLine).filter(QuoteLine.tenant_id == tenant_id, QuoteLine.quote_id == quote_id).all()
    overheads = db.query(QuoteOverhead).filter(QuoteOverhead.tenant_id == tenant_id, QuoteOverhead.quote_id == quote_id).all()

    cost_net = sum(float(l.qty) * float(l.purchase_price_net) for l in lines)
    sell_net_before = sum(float(l.sell_price_net_total) for l in lines)

    overhead_amount = 0.0
    for oh in overheads:
        overhead_amount += sell_net_before * float(oh.pct)

    sell_net = sell_net_before + overhead_amount
    vat_amount = sell_net * float(vat_rate)
    sell_gross = sell_net + vat_amount

    margin_net = sell_net - cost_net
    margin_pct = (margin_net / sell_net) if sell_net > 0 else 0.0

    totals = db.query(QuoteTotals).filter(QuoteTotals.quote_id == quote_id, QuoteTotals.tenant_id == tenant_id).first()
    if not totals:
        totals = QuoteTotals(quote_id=quote_id, tenant_id=tenant_id)
        db.add(totals)

    totals.cost_net = cost_net
    totals.sell_net = sell_net
    totals.vat_amount = vat_amount
    totals.sell_gross = sell_gross
    totals.margin_net = margin_net
    totals.margin_pct = margin_pct

    db.commit()
    db.refresh(totals)
    return totals

def recalc_line_prices(line: QuoteLine) -> None:
    unit = float(line.purchase_price_net) * (1.0 + float(line.markup_pct))
    total = float(line.qty) * unit
    line.sell_price_net_unit = unit
    line.sell_price_net_total = total
