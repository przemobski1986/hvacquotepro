"""Creates first tenant + admin user for fresh deployments."""

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.core import Tenant, User, TenantSettings
from app.security import hash_password
import uuid

def main():
    db: Session = SessionLocal()
    try:
        tenant = Tenant(name="Demo Tenant", nip=None)
        db.add(tenant); db.commit(); db.refresh(tenant)

        settings = TenantSettings(
            tenant_id=tenant.id,
            min_margin_pct=0.15,
            block_below_min_margin=False,
            default_vat_rate=0.23,
            quote_prefix="Q",
            company_name="HVACQuotePro sp. z o.o.",
            company_nip="",
            company_address="",
        )
        db.add(settings)

        password = "Admin123!"
        admin = User(
            tenant_id=tenant.id,
            email="admin@demo.local",
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit(); db.refresh(admin)

        print("=== BOOTSTRAP DONE ===")
        print("tenant_id:", tenant.id)
        print("admin_email:", admin.email)
        print("admin_password:", password)
    finally:
        db.close()

if __name__ == "__main__":
    main()
