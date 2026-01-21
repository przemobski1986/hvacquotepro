from sqlalchemy.orm import Session
from fastapi import Request
from app.i18n import t
from app.models.core import TenantSettings
from app.models.quoting import QuoteTotals
from app.schemas.quoting import ValidationIssue

def validate_quote(db: Session, request: Request, tenant_id: str, quote_id: str) -> list[ValidationIssue]:
    settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
    totals = db.query(QuoteTotals).filter(QuoteTotals.tenant_id == tenant_id, QuoteTotals.quote_id == quote_id).first()
    issues: list[ValidationIssue] = []
    if not totals or not settings:
        return issues

    if float(totals.sell_net) < float(totals.cost_net):
        issues.append(ValidationIssue(level="block", code="SELL_BELOW_COST", message=t(request, "quote.sell_below_cost")))

    if float(totals.margin_pct) < float(settings.min_margin_pct):
        level = "block" if settings.block_below_min_margin else "warning"
        issues.append(ValidationIssue(level=level, code="MARGIN_BELOW_MIN", message=t(request, "quote.margin_below_min")))

    return issues
