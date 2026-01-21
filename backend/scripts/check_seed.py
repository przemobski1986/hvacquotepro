from sqlalchemy import text
from app.db import engine

def count(table: str) -> int:
    with engine.begin() as conn:
        return int(conn.execute(text(f"select count(*) from {table}")).scalar() or 0)

print("employees", count("tk_employees"))
print("vehicles", count("tk_vehicles"))
print("sites", count("tk_sites"))
