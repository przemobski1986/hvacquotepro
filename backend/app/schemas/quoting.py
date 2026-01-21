from pydantic import BaseModel

class DealIn(BaseModel):
    site_id: str
    title: str
    status: str = "new"
    source: str | None = None
    owner_user_id: str | None = None

class DealOut(DealIn):
    id: str

class QuoteCreate(BaseModel):
    scenario: str  # split/vrf/vent

class QuoteOut(BaseModel):
    id: str
    deal_id: str
    quote_no: str
    scenario: str
    currency: str
    vat_rate: float
    pricing_version: int

class QuoteParamIn(BaseModel):
    key: str
    value_num: float | None = None
    value_text: str | None = None

class QuoteLineIn(BaseModel):
    line_type: str
    name: str
    unit: str = "szt"
    qty: float = 1
    purchase_price_net: float = 0
    markup_pct: float = 0.2
    source: str = "manual"
    sort_order: int = 0
    ref_id: str | None = None

class QuoteLineOut(QuoteLineIn):
    id: str
    sell_price_net_unit: float
    sell_price_net_total: float

class QuoteOverheadIn(BaseModel):
    overhead_type: str
    pct: float
    note: str | None = None

class QuoteTotalsOut(BaseModel):
    cost_net: float
    sell_net: float
    vat_amount: float
    sell_gross: float
    margin_net: float
    margin_pct: float

class ValidationIssue(BaseModel):
    level: str  # warning/block
    code: str
    message: str
