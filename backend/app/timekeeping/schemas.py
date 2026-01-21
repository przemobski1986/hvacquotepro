from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CrewSegmentCreate(BaseModel):
    site_id: int
    start_at: datetime
    end_at: Optional[datetime] = None


class CrewSegmentClose(BaseModel):
    end_at: Optional[datetime] = None


class CrewSegmentOut(BaseModel):
    id: int
    crew_log_id: int
    site_id: int
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
    segments: int

class DailySiteTotal(BaseModel):
    site_id: int
    name: str
    minutes: int
    segments: int

class DailyCrewLogTotal(BaseModel):
    crew_log_id: int
    vehicle_id: int
    minutes: int
    segments: int

class DailyReportOut(BaseModel):
    work_date: date
    total_minutes: int
    employees: List[DailyEmployeeTotal]
    sites: List[DailySiteTotal]
    crew_logs: List[DailyCrewLogTotal]

from datetime import date
from pydantic import BaseModel
from typing import List

class RangeDayTotal(BaseModel):
    work_date: date
    minutes: int
    segments: int

class RangeVehicleTotal(BaseModel):
    vehicle_id: int
    plate: str
    minutes: int
    segments: int

class RangeReportOut(BaseModel):
    date_from: date
    date_to: date
    total_minutes: int
    days: List[RangeDayTotal]
    employees: List[DailyEmployeeTotal]
    sites: List[DailySiteTotal]
    vehicles: List[RangeVehicleTotal]
