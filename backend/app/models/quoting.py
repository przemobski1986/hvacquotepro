import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.base import Base

class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    owner_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="new")  # new/estimating/sent/won/lost
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    deal_id: Mapped[str] = mapped_column(String(36), ForeignKey("deals.id", ondelete="CASCADE"), index=True)
    quote_no: Mapped[str] = mapped_column(String(50), index=True)
    scenario: Mapped[str] = mapped_column(String(20))  # split/vrf/vent
    currency: Mapped[str] = mapped_column(String(10), default="PLN")
    vat_rate: Mapped[float] = mapped_column(Numeric(5,4), default=0.23)
    pricing_version: Mapped[int] = mapped_column(Numeric(10,0), default=1)
    notes_internal: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_customer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class QuoteParam(Base):
    __tablename__ = "quote_params"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    value_num: Mapped[float | None] = mapped_column(Numeric(14,4), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

class QuoteLine(Base):
    __tablename__ = "quote_lines"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    line_type: Mapped[str] = mapped_column(String(20))  # equipment/material/labor/service/other
    ref_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(20), default="szt")
    qty: Mapped[float] = mapped_column(Numeric(14,4), default=1)
    purchase_price_net: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    markup_pct: Mapped[float] = mapped_column(Numeric(6,4), default=0.2)
    sell_price_net_unit: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    sell_price_net_total: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual/rule
    sort_order: Mapped[int] = mapped_column(Numeric(10,0), default=0)

class QuoteOverhead(Base):
    __tablename__ = "quote_overheads"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    overhead_type: Mapped[str] = mapped_column(String(20))  # indirect/logistics/risk/other
    pct: Mapped[float] = mapped_column(Numeric(6,4), default=0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

class QuoteTotals(Base):
    __tablename__ = "quote_totals"
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    cost_net: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    sell_net: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    sell_gross: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    margin_net: Mapped[float] = mapped_column(Numeric(14,4), default=0)
    margin_pct: Mapped[float] = mapped_column(Numeric(8,6), default=0)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

