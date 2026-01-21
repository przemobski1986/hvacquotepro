"""Rule engine stub for BOM generation.

In MVP we keep it simple:
- quote_params are stored
- this function can translate them into quote_lines based on tenant-configured rules
- For now, we only provide a placeholder that can be extended.

Recommended next:
- create table bom_rules as described in earlier spec
- implement safe evaluator for qty formulas
"""

from sqlalchemy.orm import Session
from app.models.quoting import QuoteParam, QuoteLine
from app.services.pricing import recalc_line_prices

def generate_lines_from_rules(db: Session, tenant_id: str, quote_id: str) -> int:
    # Placeholder: do nothing by default.
    # Return number of lines created.
    # You can implement rules based on params here.
    _ = db.query(QuoteParam).filter(QuoteParam.tenant_id == tenant_id, QuoteParam.quote_id == quote_id).all()
    return 0
