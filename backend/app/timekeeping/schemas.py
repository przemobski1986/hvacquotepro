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
