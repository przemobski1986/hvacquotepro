from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from .schemas import CrewSegmentCreate, CrewSegmentClose, CrewSegmentOut, SegmentStartIn, DailyReportOut, DailyEmployeeTotal, DailySiteTotal, DailyCrewLogTotal, RangeReportOut, RangeDayTotal, RangeVehicleTotal

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
    TkSegmentType,
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

    
    AUTO_TRAVEL_GAP = True
    
    try:
        is_work = (getattr(payload, "segment_type", None) in (None, "work", TkSegmentType.work))
    except Exception:
        is_work = True
    
    if is_work and payload.start_at:
        last = (
            db.query(TkCrewWorkSegment)
            .filter(TkCrewWorkSegment.crew_log_id == log_id)
            .filter(TkCrewWorkSegment.end_at.isnot(None))
            .order_by(TkCrewWorkSegment.end_at.desc())
            .first()
        )
        last_end = last.end_at if last else None
        start_dt = payload.start_at
        try:
            if last_end is not None and getattr(last_end, "tzinfo", None) is not None:
                last_end = last_end.replace(tzinfo=None)
            if start_dt is not None and getattr(start_dt, "tzinfo", None) is not None:
                start_dt = start_dt.replace(tzinfo=None)
        except Exception:
            pass
        if last_end and start_dt and last_end < start_dt:
            gap_min = int((start_dt - last_end).total_seconds() // 60)
            if gap_min > 0:
                travel = TkCrewWorkSegment(
                    crew_log_id=log_id,
                    site_id=payload.site_id,
                    segment_type=TkSegmentType.travel,
                    start_at=last_end,
                    end_at=start_dt,
                    start_lat=site.lat,
                    start_lng=site.lng,
                    end_lat=site.lat,
                    end_lng=site.lng,
                )
                db.add(travel)
    
    seg = TkCrewWorkSegment(
        crew_log_id=log_id,
        site_id=payload.site_id,
        segment_type=getattr(payload, "segment_type", None) or TkSegmentType.work,
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












# -----------------------
# Reports
# -----------------------

@router.get("/reports/daily", response_model=DailyReportOut)
def report_daily(
    work_date: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            TkCrewWorkSegment.crew_log_id,
            TkCrewWorkSegment.site_id,
            TkCrewWorkSegment.start_at,
            TkCrewWorkSegment.end_at,
            TkCrewLog.vehicle_id.label("vehicle_id"),
        )
        .join(TkCrewLog, TkCrewLog.id == TkCrewWorkSegment.crew_log_id)
        .filter(TkCrewLog.work_date == work_date)
        .filter(TkCrewWorkSegment.end_at.isnot(None))
    )

    if vehicle_id is not None:
        q = q.filter(TkCrewLog.vehicle_id == vehicle_id)

    segments = q.all()

    crew_log_ids = sorted({s.crew_log_id for s in segments})
    site_ids = sorted({s.site_id for s in segments})

    sites_by_id = {}
    if site_ids:
        for s in db.query(TkSite).filter(TkSite.id.in_(site_ids)).all():
            sites_by_id[s.id] = s.name

    crewlog_vehicle = {}
    if crew_log_ids:
        for cl in db.query(TkCrewLog).filter(TkCrewLog.id.in_(crew_log_ids)).all():
            crewlog_vehicle[cl.id] = cl.vehicle_id

    members_by_log = defaultdict(list)
    if crew_log_ids:
        members = (
            db.query(TkCrewLogMember)
            .filter(TkCrewLogMember.crew_log_id.in_(crew_log_ids))
            .all()
        )
        for m in members:
            members_by_log[m.crew_log_id].append(m.employee_id)

    employees_by_id = {}
    if crew_log_ids:
        emp_ids = sorted({eid for ids in members_by_log.values() for eid in ids})
        if emp_ids:
            for e in db.query(TkEmployee).filter(TkEmployee.id.in_(emp_ids)).all():
                employees_by_id[e.id] = e.full_name

    site_totals: Dict[int, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})
    crewlog_totals: Dict[int, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})
    employee_totals: Dict[int, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})

    total_minutes = 0

    for s in segments:
        start_at = s.start_at
        end_at = s.end_at
        if not end_at:
            continue

        minutes = int(max(0, (end_at - start_at).total_seconds() // 60))
        total_minutes += minutes

        site_totals[s.site_id]["minutes"] += minutes
        site_totals[s.site_id]["segments"] += 1

        crewlog_totals[s.crew_log_id]["minutes"] += minutes
        crewlog_totals[s.crew_log_id]["segments"] += 1

        emp_ids = members_by_log.get(s.crew_log_id, [])
        if employee_id is not None:
            emp_ids = [x for x in emp_ids if x == employee_id]

        if emp_ids:
            per_emp = minutes // len(emp_ids) if len(emp_ids) > 0 else 0
            for eid in emp_ids:
                employee_totals[eid]["minutes"] += per_emp
                employee_totals[eid]["segments"] += 1

    employees_out = [
        DailyEmployeeTotal(
            employee_id=eid,
            full_name=employees_by_id.get(eid, f"Employee {eid}"),
            minutes=vals["minutes"],
            segments=vals["segments"],
        )
        for eid, vals in sorted(employee_totals.items(), key=lambda kv: (-(kv[1]["minutes"]), kv[0]))
    ]

    sites_out = [
        DailySiteTotal(
            site_id=sid,
            name=sites_by_id.get(sid, f"Site {sid}"),
            minutes=vals["minutes"],
            segments=vals["segments"],
        )
        for sid, vals in sorted(site_totals.items(), key=lambda kv: (-(kv[1]["minutes"]), kv[0]))
    ]

    crew_logs_out = [
        DailyCrewLogTotal(
            crew_log_id=clid,
            vehicle_id=crewlog_vehicle.get(clid, 0),
            minutes=vals["minutes"],
            segments=vals["segments"],
        )
        for clid, vals in sorted(crewlog_totals.items(), key=lambda kv: (-(kv[1]["minutes"]), kv[0]))
    ]

    return DailyReportOut(
        work_date=work_date,
        total_minutes=total_minutes,
        employees=employees_out,
        sites=sites_out,
        crew_logs=crew_logs_out,
    )


# -----------------------
# Range Reports
# -----------------------

from calendar import monthrange

def _aggregate_range(
    db: Session,
    date_from: date,
    date_to: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
) -> RangeReportOut:
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to must be >= date_from")

    q = (
        db.query(
            TkCrewWorkSegment.crew_log_id,
            TkCrewWorkSegment.site_id,
            TkCrewWorkSegment.start_at,
            TkCrewWorkSegment.end_at,
            TkCrewLog.work_date.label("work_date"),
            TkCrewLog.vehicle_id.label("vehicle_id"),
        )
        .join(TkCrewLog, TkCrewLog.id == TkCrewWorkSegment.crew_log_id)
        .filter(TkCrewLog.work_date >= date_from)
        .filter(TkCrewLog.work_date <= date_to)
        .filter(TkCrewWorkSegment.end_at.isnot(None))
    )

    if vehicle_id is not None:
        q = q.filter(TkCrewLog.vehicle_id == vehicle_id)

    segments = q.all()

    crew_log_ids = sorted({s.crew_log_id for s in segments})
    site_ids = sorted({s.site_id for s in segments})
    vehicle_ids = sorted({s.vehicle_id for s in segments})

    sites_by_id = {}
    if site_ids:
        for s in db.query(TkSite).filter(TkSite.id.in_(site_ids)).all():
            sites_by_id[s.id] = s.name

    vehicles_by_id = {}
    if vehicle_ids:
        for v in db.query(TkVehicle).filter(TkVehicle.id.in_(vehicle_ids)).all():
            vehicles_by_id[v.id] = v.plate

    members_by_log = defaultdict(list)
    if crew_log_ids:
        members = (
            db.query(TkCrewLogMember)
            .filter(TkCrewLogMember.crew_log_id.in_(crew_log_ids))
            .all()
        )
        for m in members:
            members_by_log[m.crew_log_id].append(m.employee_id)

    employees_by_id = {}
    if crew_log_ids:
        emp_ids = sorted({eid for ids in members_by_log.values() for eid in ids})
        if emp_ids:
            for e in db.query(TkEmployee).filter(TkEmployee.id.in_(emp_ids)).all():
                employees_by_id[e.id] = e.full_name

    day_totals: Dict[date, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})
    site_totals: Dict[int, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})
    vehicle_totals: Dict[int, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})
    employee_totals: Dict[int, Dict[str, int]] = defaultdict(lambda: {"minutes": 0, "segments": 0})

    total_minutes = 0

    for s in segments:
        if not s.end_at:
            continue

        minutes = int(max(0, (s.end_at - s.start_at).total_seconds() // 60))
        total_minutes += minutes

        day_totals[s.work_date]["minutes"] += minutes
        day_totals[s.work_date]["segments"] += 1

        site_totals[s.site_id]["minutes"] += minutes
        site_totals[s.site_id]["segments"] += 1

        vehicle_totals[s.vehicle_id]["minutes"] += minutes
        vehicle_totals[s.vehicle_id]["segments"] += 1

        emp_ids = members_by_log.get(s.crew_log_id, [])
        if employee_id is not None:
            emp_ids = [x for x in emp_ids if x == employee_id]

        if emp_ids:
            per_emp = minutes // len(emp_ids) if len(emp_ids) > 0 else 0
            for eid in emp_ids:
                employee_totals[eid]["minutes"] += per_emp
                employee_totals[eid]["segments"] += 1

    days_out = [
        RangeDayTotal(work_date=d, minutes=v["minutes"], segments=v["segments"])
        for d, v in sorted(day_totals.items(), key=lambda kv: kv[0])
    ]

    employees_out = [
        DailyEmployeeTotal(
            employee_id=eid,
            full_name=employees_by_id.get(eid, f"Employee {eid}"),
            minutes=vals["minutes"],
            segments=vals["segments"],
        )
        for eid, vals in sorted(employee_totals.items(), key=lambda kv: (-(kv[1]["minutes"]), kv[0]))
    ]

    sites_out = [
        DailySiteTotal(
            site_id=sid,
            name=sites_by_id.get(sid, f"Site {sid}"),
            minutes=vals["minutes"],
            segments=vals["segments"],
        )
        for sid, vals in sorted(site_totals.items(), key=lambda kv: (-(kv[1]["minutes"]), kv[0]))
    ]

    vehicles_out = [
        RangeVehicleTotal(
            vehicle_id=vid,
            plate=vehicles_by_id.get(vid, f"Vehicle {vid}"),
            minutes=vals["minutes"],
            segments=vals["segments"],
        )
        for vid, vals in sorted(vehicle_totals.items(), key=lambda kv: (-(kv[1]["minutes"]), kv[0]))
    ]

    return RangeReportOut(
        date_from=date_from,
        date_to=date_to,
        total_minutes=total_minutes,
        days=days_out,
        employees=employees_out,
        sites=sites_out,
        vehicles=vehicles_out,
    )


@router.get("/reports/range", response_model=RangeReportOut)
def report_range(
    date_from: date,
    date_to: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return _aggregate_range(db, date_from, date_to, vehicle_id=vehicle_id, employee_id=employee_id)


@router.get("/reports/weekly", response_model=RangeReportOut)
def report_weekly(
    week_start: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    date_from = week_start
    date_to = date(week_start.year, week_start.month, week_start.day)  # defensive
    date_to = date_from.fromordinal(date_from.toordinal() + 6)
    return _aggregate_range(db, date_from, date_to, vehicle_id=vehicle_id, employee_id=employee_id)


@router.get("/reports/monthly", response_model=RangeReportOut)
def report_monthly(
    year: int,
    month: int,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be 1..12")
    last_day = monthrange(year, month)[1]
    date_from = date(year, month, 1)
    date_to = date(year, month, last_day)
    return _aggregate_range(db, date_from, date_to, vehicle_id=vehicle_id, employee_id=employee_id)

# -----------------------
# CSV Exports
# -----------------------

from io import StringIO
import csv
from fastapi.responses import Response

def _csv_response(filename: str, header: list[str], rows: list[list[object]]) -> Response:
    buf = StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(header)
    for r in rows:
        w.writerow(r)

    content = "\ufeff" + buf.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

def _date_add_days(d: date, days: int) -> date:
    return date.fromordinal(d.toordinal() + days)

def _range_report(db: Session, date_from: date, date_to: date, vehicle_id: Optional[int], employee_id: Optional[int]) -> RangeReportOut:
    return _aggregate_range(db, date_from, date_to, vehicle_id=vehicle_id, employee_id=employee_id)

def _weekly_report(db: Session, week_start: date, vehicle_id: Optional[int], employee_id: Optional[int]) -> RangeReportOut:
    return _aggregate_range(db, week_start, _date_add_days(week_start, 6), vehicle_id=vehicle_id, employee_id=employee_id)

def _monthly_report(db: Session, year: int, month: int, vehicle_id: Optional[int], employee_id: Optional[int]) -> RangeReportOut:
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be 1..12")
    last_day = monthrange(year, month)[1]
    return _aggregate_range(db, date(year, month, 1), date(year, month, last_day), vehicle_id=vehicle_id, employee_id=employee_id)

@router.get("/reports/range/employees.csv")
def report_range_employees_csv(
    date_from: date,
    date_to: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _range_report(db, date_from, date_to, vehicle_id, employee_id)
    rows = [[e.employee_id, e.full_name, e.minutes, e.segments] for e in rep.employees]
    return _csv_response("range_employees.csv", ["employee_id", "full_name", "minutes", "segments"], rows)

@router.get("/reports/range/vehicles.csv")
def report_range_vehicles_csv(
    date_from: date,
    date_to: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _range_report(db, date_from, date_to, vehicle_id, employee_id)
    rows = [[v.vehicle_id, v.plate, v.minutes, v.segments] for v in rep.vehicles]
    return _csv_response("range_vehicles.csv", ["vehicle_id", "plate", "minutes", "segments"], rows)

@router.get("/reports/range/sites.csv")
def report_range_sites_csv(
    date_from: date,
    date_to: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _range_report(db, date_from, date_to, vehicle_id, employee_id)
    rows = [[s.site_id, s.name, s.minutes, s.segments] for s in rep.sites]
    return _csv_response("range_sites.csv", ["site_id", "name", "minutes", "segments"], rows)

@router.get("/reports/weekly/employees.csv")
def report_weekly_employees_csv(
    week_start: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _weekly_report(db, week_start, vehicle_id, employee_id)
    rows = [[e.employee_id, e.full_name, e.minutes, e.segments] for e in rep.employees]
    return _csv_response("weekly_employees.csv", ["employee_id", "full_name", "minutes", "segments"], rows)

@router.get("/reports/weekly/vehicles.csv")
def report_weekly_vehicles_csv(
    week_start: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _weekly_report(db, week_start, vehicle_id, employee_id)
    rows = [[v.vehicle_id, v.plate, v.minutes, v.segments] for v in rep.vehicles]
    return _csv_response("weekly_vehicles.csv", ["vehicle_id", "plate", "minutes", "segments"], rows)

@router.get("/reports/weekly/sites.csv")
def report_weekly_sites_csv(
    week_start: date,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _weekly_report(db, week_start, vehicle_id, employee_id)
    rows = [[s.site_id, s.name, s.minutes, s.segments] for s in rep.sites]
    return _csv_response("weekly_sites.csv", ["site_id", "name", "minutes", "segments"], rows)

@router.get("/reports/monthly/employees.csv")
def report_monthly_employees_csv(
    year: int,
    month: int,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _monthly_report(db, year, month, vehicle_id, employee_id)
    rows = [[e.employee_id, e.full_name, e.minutes, e.segments] for e in rep.employees]
    return _csv_response("monthly_employees.csv", ["employee_id", "full_name", "minutes", "segments"], rows)

@router.get("/reports/monthly/vehicles.csv")
def report_monthly_vehicles_csv(
    year: int,
    month: int,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _monthly_report(db, year, month, vehicle_id, employee_id)
    rows = [[v.vehicle_id, v.plate, v.minutes, v.segments] for v in rep.vehicles]
    return _csv_response("monthly_vehicles.csv", ["vehicle_id", "plate", "minutes", "segments"], rows)

@router.get("/reports/monthly/sites.csv")
def report_monthly_sites_csv(
    year: int,
    month: int,
    vehicle_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rep = _monthly_report(db, year, month, vehicle_id, employee_id)
    rows = [[s.site_id, s.name, s.minutes, s.segments] for s in rep.sites]
    return _csv_response("monthly_sites.csv", ["site_id", "name", "minutes", "segments"], rows)

