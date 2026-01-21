"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("nip", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("email", sa.String(length=255), index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "tenant_settings",
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("min_margin_pct", sa.Numeric(6,4), server_default=sa.text("0.15")),
        sa.Column("block_below_min_margin", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("default_vat_rate", sa.Numeric(5,4), server_default=sa.text("0.23")),
        sa.Column("quote_prefix", sa.String(length=20), server_default=sa.text("'Q'")),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("company_name", sa.Text(), nullable=True),
        sa.Column("company_address", sa.Text(), nullable=True),
        sa.Column("company_nip", sa.Text(), nullable=True),
    )
    op.create_table(
        "clients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("nip", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "sites",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("client_id", sa.String(length=36), sa.ForeignKey("clients.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "deals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("site_id", sa.String(length=36), sa.ForeignKey("sites.id", ondelete="CASCADE"), index=True),
        sa.Column("owner_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), server_default=sa.text("'new'")),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "quotes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("deal_id", sa.String(length=36), sa.ForeignKey("deals.id", ondelete="CASCADE"), index=True),
        sa.Column("quote_no", sa.String(length=50), index=True),
        sa.Column("scenario", sa.String(length=20), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default=sa.text("'PLN'")),
        sa.Column("vat_rate", sa.Numeric(5,4), server_default=sa.text("0.23")),
        sa.Column("pricing_version", sa.Numeric(10,0), server_default=sa.text("1")),
        sa.Column("notes_internal", sa.Text(), nullable=True),
        sa.Column("notes_customer", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "quote_params",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("quote_id", sa.String(length=36), sa.ForeignKey("quotes.id", ondelete="CASCADE"), index=True),
        sa.Column("key", sa.String(length=100), index=True),
        sa.Column("value_num", sa.Numeric(14,4), nullable=True),
        sa.Column("value_text", sa.String(length=255), nullable=True),
    )
    op.create_table(
        "quote_lines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("quote_id", sa.String(length=36), sa.ForeignKey("quotes.id", ondelete="CASCADE"), index=True),
        sa.Column("line_type", sa.String(length=20), nullable=False),
        sa.Column("ref_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit", sa.String(length=20), server_default=sa.text("'szt'")),
        sa.Column("qty", sa.Numeric(14,4), server_default=sa.text("1")),
        sa.Column("purchase_price_net", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("markup_pct", sa.Numeric(6,4), server_default=sa.text("0.2")),
        sa.Column("sell_price_net_unit", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("sell_price_net_total", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("source", sa.String(length=20), server_default=sa.text("'manual'")),
        sa.Column("sort_order", sa.Numeric(10,0), server_default=sa.text("0")),
    )
    op.create_table(
        "quote_overheads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("quote_id", sa.String(length=36), sa.ForeignKey("quotes.id", ondelete="CASCADE"), index=True),
        sa.Column("overhead_type", sa.String(length=20), nullable=False),
        sa.Column("pct", sa.Numeric(6,4), server_default=sa.text("0")),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_table(
        "quote_totals",
        sa.Column("quote_id", sa.String(length=36), sa.ForeignKey("quotes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), index=True),
        sa.Column("cost_net", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("sell_net", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("vat_amount", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("sell_gross", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("margin_net", sa.Numeric(14,4), server_default=sa.text("0")),
        sa.Column("margin_pct", sa.Numeric(8,6), server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("quote_totals")
    op.drop_table("quote_overheads")
    op.drop_table("quote_lines")
    op.drop_table("quote_params")
    op.drop_table("quotes")
    op.drop_table("deals")
    op.drop_table("sites")
    op.drop_table("clients")
    op.drop_table("tenant_settings")
    op.drop_table("users")
    op.drop_table("tenants")
