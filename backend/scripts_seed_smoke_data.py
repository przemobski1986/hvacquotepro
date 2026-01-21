from sqlalchemy.orm import Session
from app.db import SessionLocal

from app.models.core import User, Tenant  # ważne: rejestruje modele dla relacji stringowych
from app.timekeeping.models import TkSite, TkEmployee, TkVehicle

SITE_ID = 1
SITE_NAME = "SMOKE_SITE"
SITE_LAT = 50.2649
SITE_LNG = 19.0238

EMPLOYEE_NAME = "TEST_SMOKE"
VEHICLE_PLATE = "TEST-SMOKE-000"
VEHICLE_MAKE_MODEL = "SMOKE"

def main():
    db: Session = SessionLocal()
    try:
        site = db.query(TkSite).filter(TkSite.id == SITE_ID).first()
        if not site:
            site = TkSite(id=SITE_ID, name=SITE_NAME, lat=SITE_LAT, lng=SITE_LNG)
            db.add(site)

        emp = db.query(TkEmployee).filter(TkEmployee.full_name == EMPLOYEE_NAME).first()
        if not emp:
            emp = TkEmployee(full_name=EMPLOYEE_NAME, user_id=None, is_active=True)
            db.add(emp)

        veh = db.query(TkVehicle).filter(TkVehicle.plate == VEHICLE_PLATE).first()
        if not veh:
            veh = TkVehicle(plate=VEHICLE_PLATE, make_model=VEHICLE_MAKE_MODEL, navisoft_device_id=None, is_active=True)
            db.add(veh)

        db.commit()

        print(f"OK site_id={site.id} emp_id={emp.id} veh_id={veh.id}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
