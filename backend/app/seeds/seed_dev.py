from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import MetaData, Table, select, and_
from sqlalchemy.exc import NoSuchTableError

from app.config import settings
from app.db import engine

def _now():
    return datetime.now(timezone.utc)

def _hash_password(pw: str) -> str:
    try:
        from app.security import pwd_context
        return pwd_context.hash(pw)
    except Exception:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        return ctx.hash(pw)

def _autoload(md: MetaData, name: str) -> Table | None:
    try:
        return Table(name, md, autoload_with=engine)
    except NoSuchTableError:
        return None
    except Exception:
        return None

def _ensure_row(conn, table: Table, where_cols: dict, values: dict) -> int:
    conds = []
    for k, v in where_cols.items():
        col = table.c.get(k)
        if col is None:
            continue
        conds.append(col == v)

    if conds:
        row = conn.execute(select(table.c.id).where(and_(*conds))).first()
        if row:
            return int(row[0])

    r = conn.execute(table.insert().values(**values))
    try:
        pk = r.inserted_primary_key[0]
        if pk is not None:
            return int(pk)
    except Exception:
        pass

    if conds:
        row2 = conn.execute(select(table.c.id).where(and_(*conds))).first()
        if row2:
            return int(row2[0])

    raise RuntimeError(f"Nie udalo sie ustalic ID dla {table.name}")

def seed(email: str = "admin@hvacquotepro.pl", password: str = "Admin123!") -> None:
    md = MetaData()

    users = _autoload(md, "users")
    employees = _autoload(md, "tk_employees")
    vehicles = _autoload(md, "tk_vehicles")
    sites = _autoload(md, "tk_sites")

    with engine.begin() as conn:
        if users is not None and "email" in users.c:
            row = conn.execute(select(users.c.id).where(users.c.email == email)).first()
            if not row:
                hpw = _hash_password(password)
                values = {}

                if "email" in users.c:
                    values["email"] = email
                if "hashed_password" in users.c:
                    values["hashed_password"] = hpw
                elif "password_hash" in users.c:
                    values["password_hash"] = hpw

                if "is_active" in users.c:
                    values["is_active"] = True
                if "is_superuser" in users.c:
                    values["is_superuser"] = True
                if "is_admin" in users.c:
                    values["is_admin"] = True

                if "full_name" in users.c:
                    values["full_name"] = "Admin"
                if "name" in users.c and "full_name" not in values:
                    values["name"] = "Admin"

                if "created_at" in users.c:
                    values["created_at"] = _now()
                if "updated_at" in users.c:
                    values["updated_at"] = _now()

                for col in users.columns:
                    if col.name in values:
                        continue
                    if col.primary_key:
                        continue
                    if col.nullable:
                        continue
                    if col.server_default is not None or col.default is not None:
                        continue
                    try:
                        py = col.type.python_type
                    except Exception:
                        py = str
                    if py is bool:
                        values[col.name] = False
                    elif py is int:
                        values[col.name] = 0
                    elif py is float:
                        values[col.name] = 0.0
                    else:
                        values[col.name] = ""

                conn.execute(users.insert().values(**values))

        if employees is not None:
            e1_id = _ensure_row(
                conn,
                employees,
                {"full_name": "Jan Kowalski"},
                {"full_name": "Jan Kowalski", "user_id": None, "is_active": True, "created_at": _now()},
            )
            e2_id = _ensure_row(
                conn,
                employees,
                {"full_name": "Piotr Nowak"},
                {"full_name": "Piotr Nowak", "user_id": None, "is_active": True, "created_at": _now()},
            )
        else:
            e1_id = None
            e2_id = None

        if vehicles is not None:
            _ensure_row(
                conn,
                vehicles,
                {"plate": "SBI-DEV-001"},
                {"plate": "SBI-DEV-001", "make_model": "Dev Van 1", "navisoft_device_id": None, "is_active": True, "created_at": _now()},
            )
            _ensure_row(
                conn,
                vehicles,
                {"plate": "SBI-DEV-002"},
                {"plate": "SBI-DEV-002", "make_model": "Dev Van 2", "navisoft_device_id": None, "is_active": True, "created_at": _now()},
            )

        if sites is not None:
            values = {
                "name": "DEV Site",
                "lat": 50.2600,
                "lng": 19.0200,
                "radius_m": 200,
                "is_ad_hoc": True,
                "created_at": _now(),
            }
            if "created_by_employee_id" in sites.c:
                values["created_by_employee_id"] = e1_id
            _ensure_row(conn, sites, {"name": "DEV Site"}, values)

if __name__ == "__main__":
    seed()
