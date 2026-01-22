from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel


class CrewSegmentCreate(BaseModel):
    site_id: int
    segment_type: Literal["work","travel"] = "work"
    start_at: datetime
    end_at: Optional[datetime] = None


class CrewSegmentClose(BaseModel):
    end_at: Optional[datetime] = None


class CrewSegmentOut(BaseModel):
    id: int
    crew_log_id: int
    site_id: int
    segment_type: str
    start_at: datetime
    end_at: Optional[datetime]
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float

    class Config:
        from_attributes = True


class SegmentStartIn(BaseModel):
    site_id: int

from datetime import date
from pydantic import BaseModel
from typing import List

class DailyEmployeeTotal(BaseModel):
    employee_id: int
    full_name: str
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int

class DailySiteTotal(BaseModel):
    site_id: int
    name: str
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int

class DailyCrewLogTotal(BaseModel):
    crew_log_id: int
    vehicle_id: int
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int

class DailyReportOut(BaseModel):
    work_date: date
    total_minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    employees: list[DailyEmployeeTotal]
    sites: list[DailySiteTotal]
    crew_logs: list[DailyCrewLogTotal]

from datetime import date
from pydantic import BaseModel
from typing import List

class RangeDayTotal(BaseModel):
    work_date: date
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int

class RangeVehicleTotal(BaseModel):
    vehicle_id: int
    plate: str
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int

class RangeReportOut(BaseModel):
    date_from: date
    date_to: date
    total_minutes: int
    days: List[RangeDayTotal]
    employees: List[RangeEmployeeTotal]
    sites: List[RangeSiteTotal]
    vehicles: List[RangeVehicleTotal]

class RangeEmployeeTotal(BaseModel):
    employee_id: int
    full_name: str
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int


class RangeSiteTotal(BaseModel):
    site_id: int
    name: str
    minutes: int
    work_minutes: int = 0
    travel_minutes: int = 0
    segments: int


