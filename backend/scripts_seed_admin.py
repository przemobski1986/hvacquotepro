from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.core import User
from app.security import hash_password

EMAIL = "admin@hvacquotepro.pl"
PASSWORD = "Admin123!"

def main():
    db: Session = SessionLocal()
    try:
        u = db.query(User).filter(User.email == EMAIL).first()
        if u:
            print("ADMIN_EXISTS")
            return
        u = User(
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            role="admin",
            is_active=True,
            tenant_id=None,
        )
        db.add(u)
        db.commit()
        print("ADMIN_CREATED")
    finally:
        db.close()

if __name__ == "__main__":
    main()
