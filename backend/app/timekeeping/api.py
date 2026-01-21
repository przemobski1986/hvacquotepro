from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from .schemas import CrewSegmentCreate, CrewSegmentClose, CrewSegmentOut, SegmentStartIn

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.timekeeping.models import (
    TkCrewLog,
    TkCrewLogMember,
    TkCrewWorkSegment,
    TkEmployee,
    TkVehicle,
    TkSite,
)

router = APIRouter(prefix="/timekeeping", tags=["timekeeping"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# Employees
# -----------------------

class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    user_id: Optional[int] = None


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    user_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/employees", response_model=EmployeeOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    emp = TkEmployee(full_name=payload.full_name, user_id=payload.user_id, is_active=True)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.get("/employees", response_model=List[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return (
        db.query(TkEmployee)
        .filter(TkEmployee.is_active == True)  # noqa: E712
        .order_by(TkEmployee.full_name.asc())
        .all()
    )


# -----------------------
# Vehicles
# -----------------------

class VehicleCreate(BaseModel):
    plate: str = Field(min_length=2, max_length=32)
    make_model: Optional[str] = None
    navisoft_device_id: Optional[str] = None


class VehicleOut(BaseModel):
    id: int
    plate: str
    make_model: Optional[str]
    navisoft_device_id: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/vehicles", response_model=VehicleOut)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    v = TkVehicle(
        plate=payload.plate,
        make_model=payload.make_model,
        navisoft_device_id=payload.navisoft_device_id,
        is_active=True,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.get("/vehicles", response_model=List[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return (
        db.query(TkVehicle)
        .filter(TkVehicle.is_active == True)  # noqa: E712
        .order_by(TkVehicle.plate.asc())
        .all()
    )


# -----------------------
# Sites
# -----------------------

class SiteAdHocCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    lat: float
    lng: float
    radius_m: int = 500


class SiteOut(BaseModel):
    id: int
    name: str
    lat: Optional[float]
    lng: Optional[float]
    radius_m: Optional[int]
    is_ad_hoc: bool

    class Config:
        from_attributes = True


@router.post("/sites/ad-hoc", response_model=SiteOut)
def create_site_ad_hoc(payload: SiteAdHocCreate, db: Session = Depends(get_db)):
    s = TkSite(
        name=payload.name,
        lat=payload.lat,
        lng=payload.lng,
        radius_m=payload.radius_m,
        is_ad_hoc=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/sites", response_model=List[SiteOut])
def list_sites(db: Session = Depends(get_db)):
    return db.query(TkSite).order_by(TkSite.name.asc()).all()


# -----------------------
# Crew Logs
# -----------------------

class CrewLogCreate(BaseModel):
    work_date: date
    vehicle_id: int
    created_by_employee_id: Optional[int] = None


class CrewLogOut(BaseModel):
    id: int
    work_date: date
    vehicle_id: int
    created_by_employee_id: Optional[int] = None

    class Config:
        from_attributes = True


@router.post("/crew-logs", response_model=CrewLogOut)
def create_crew_log(payload: CrewLogCreate, db: Session = Depends(get_db)):
    # ochrona przed duplikatem (cz?sty pow?d 500, je?li jest UNIQUE)
    existing = (
        db.query(TkCrewLog)
        .filter(TkCrewLog.work_date == payload.work_date)
        .filter(TkCrewLog.vehicle_id == payload.vehicle_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Crew log already exists (id={existing.id}).")

    log = TkCrewLog(
        work_date=payload.work_date,
        vehicle_id=payload.vehicle_id,
        created_by_employee_id=payload.created_by_employee_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/crew-logs", response_model=List[CrewLogOut])
def list_crew_logs(
    work_date: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(TkCrewLog)
    if work_date is not None:
        q = q.filter(TkCrewLog.work_date == work_date)
    if vehicle_id is not None:
        q = q.filter(TkCrewLog.vehicle_id == vehicle_id)
    return q.order_by(TkCrewLog.id.desc()).all()


class CrewMemberCreate(BaseModel):
    employee_id: int


class CrewMemberOut(BaseModel):
    id: int
    crew_log_id: int
    employee_id: int

    class Config:
        from_attributes = True


@router.get("/crew-logs/{log_id}/members", response_model=List[CrewMemberOut])
def list_members(log_id: int, db: Session = Depends(get_db)):
    return (
        db.query(TkCrewLogMember)
        .filter(TkCrewLogMember.crew_log_id == log_id)
        .order_by(TkCrewLogMember.id.asc())
        .all()
    )


@router.post("/crew-logs/{log_id}/members", response_model=CrewMemberOut)
def add_member(log_id: int, payload: CrewMemberCreate, db: Session = Depends(get_db)):
    log = db.query(TkCrewLog).filter(TkCrewLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Crew log not found")

    emp = db.query(TkEmployee).filter(TkEmployee.id == payload.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # blokada duplikatu cz?onka
    exists = (
        db.query(TkCrewLogMember)
        .filter(TkCrewLogMember.crew_log_id == log_id)
        .filter(TkCrewLogMember.employee_id == payload.employee_id)
        .first()
    )
    if exists:
        return exists

    m = TkCrewLogMember(crew_log_id=log_id, employee_id=payload.employee_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


# -----------------------
# Segments
# -----------------------
@router.get("/crew-logs/{log_id}/segments", response_model=List[CrewSegmentOut])
def list_segments(log_id: int, db: Session = Depends(get_db)):
    return (
        db.query(TkCrewWorkSegment)
        .filter(TkCrewWorkSegment.crew_log_id == log_id)
        .order_by(TkCrewWorkSegment.id.asc())
        .all()
    )


@router.post("/crew-logs/{log_id}/segments", response_model=CrewSegmentOut)
def add_segment(log_id: int, payload: CrewSegmentCreate, db: Session = Depends(get_db)):
    log = db.query(TkCrewLog).filter(TkCrewLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Crew log not found")

    open_seg = (
        db.query(TkCrewWorkSegment)
        .filter(TkCrewWorkSegment.crew_log_id == log_id)
        .filter(TkCrewWorkSegment.end_at.is_(None))
        .first()
    )
    if open_seg:
        raise HTTPException(
            status_code=409,
            detail=f"Open segment already exists (segment_id={open_seg.id}). Close it first.",
        )

    site = db.query(TkSite).filter(TkSite.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if site.lat is None or site.lng is None:
        raise HTTPException(status_code=422, detail="Site is missing lat/lng")

    seg = TkCrewWorkSegment(
        crew_log_id=log_id,
        site_id=payload.site_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        start_lat=site.lat,
        start_lng=site.lng,
        end_lat=site.lat,
        end_lng=site.lng,
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)
    return seg

@router.post("/crew-logs/{log_id}/segments/start", response_model=CrewSegmentOut)
def start_segment(log_id: int, payload: SegmentStartIn, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    return add_segment(
        log_id=log_id,
        payload=CrewSegmentCreate(site_id=payload.site_id, start_at=now, end_at=None),
        db=db,
    )


@router.patch("/crew-logs/{log_id}/segments/{segment_id}/close", response_model=CrewSegmentOut)
def close_segment(log_id: int, segment_id: int, payload: CrewSegmentClose, db: Session = Depends(get_db)):
    seg = (
        db.query(TkCrewWorkSegment)
        .filter(TkCrewWorkSegment.id == segment_id)
        .filter(TkCrewWorkSegment.crew_log_id == log_id)
        .first()
    )
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    if seg.end_at is not None:
        raise HTTPException(status_code=409, detail="Segment already closed")

    if seg.site_id is None:
        raise HTTPException(status_code=422, detail="Segment is missing site_id")

    site = db.query(TkSite).filter(TkSite.id == seg.site_id).first()
    if not site or site.lat is None or site.lng is None:
        raise HTTPException(status_code=422, detail="Site is missing lat/lng")

    if seg.start_lat is None or seg.start_lng is None:
        seg.start_lat = site.lat
        seg.start_lng = site.lng

    seg.end_at = payload.end_at or datetime.now(timezone.utc)
    seg.end_lat = site.lat
    seg.end_lng = site.lng

    db.add(seg)
    db.commit()
    db.refresh(seg)
    return seg

@router.patch("/crew-logs/{log_id}/segments/stop", response_model=CrewSegmentOut)
def stop_segment(log_id: int, db: Session = Depends(get_db)):
    seg = (
        db.query(TkCrewWorkSegment)
        .filter(TkCrewWorkSegment.crew_log_id == log_id)
        .filter(TkCrewWorkSegment.end_at.is_(None))
        .order_by(TkCrewWorkSegment.id.desc())
        .first()
    )
    if not seg:
        raise HTTPException(status_code=404, detail="No open segment found")

    return close_segment(
        log_id=log_id,
        segment_id=seg.id,
        payload=CrewSegmentClose(end_at=datetime.now(timezone.utc)),
        db=db,
    )


# -----------------------
# Summary
# -----------------------

class CrewLogSummaryOut(BaseModel):
    crew_log_id: int
    work_date: date
    vehicle_id: int
    total_minutes: int
    by_site_minutes: Dict[int, int]
    by_employee_minutes: Dict[int, int]


@router.get("/crew-logs/{log_id}/summary", response_model=CrewLogSummaryOut)
def crew_log_summary(log_id: int, db: Session = Depends(get_db)):
    log = db.query(TkCrewLog).filter(TkCrewLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Crew log not found")

    segs = (
        db.query(TkCrewWorkSegment)
        .filter(TkCrewWorkSegment.crew_log_id == log_id)
        .filter(TkCrewWorkSegment.end_at.isnot(None))
        .order_by(TkCrewWorkSegment.start_at.asc())
        .all()
    )

    by_site = defaultdict(int)
    total = 0

    for seg in segs:
        minutes = int((seg.end_at - seg.start_at).total_seconds() // 60)
        if minutes < 0:
            minutes = 0
        total += minutes
        by_site[int(seg.site_id)] += minutes

    members = (
        db.query(TkCrewLogMember)
        .filter(TkCrewLogMember.crew_log_id == log_id)
        .all()
    )

    # MVP: ka?demu cz?onkowi przypisujemy total (to p??niej rozbijemy proporcjonalnie)
    by_emp = {int(m.employee_id): int(total) for m in members}

    return CrewLogSummaryOut(
        crew_log_id=log.id,
        work_date=log.work_date,
        vehicle_id=log.vehicle_id,
        total_minutes=int(total),
        by_site_minutes=dict(by_site),
        by_employee_minutes=by_emp,
    )










