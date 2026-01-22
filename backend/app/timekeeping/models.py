from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Float, Text,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum


)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.base import Base


class TkCrewLogStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    locked = "locked"


class TkAbsenceType(str, Enum):
    urlop = "urlop"
    l4 = "l4"
    inne = "inne"


class TkDailyStatus(str, Enum):
    praca = "praca"
    urlop = "urlop"
    l4 = "l4"
    inne = "inne"
    nieobecny_do_klasyfikacji = "nieobecny_do_klasyfikacji"


class TkSegmentType(str, Enum):
    work = "work"
    travel = "travel"


class TkEmployee(Base):
    __tablename__ = "tk_employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", lazy="joined", foreign_keys=[user_id])


class TkVehicle(Base):
    __tablename__ = "tk_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(32), nullable=False, unique=True, index=True)
    make_model = Column(String(128), nullable=True)
    navisoft_device_id = Column(String(64), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TkSite(Base):
    __tablename__ = "tk_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    radius_m = Column(Integer, nullable=True)
    is_ad_hoc = Column(Boolean, nullable=False, default=False)
    created_by_employee_id = Column(Integer, ForeignKey("tk_employees.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    created_by = relationship("TkEmployee", lazy="joined", foreign_keys=[created_by_employee_id])


class TkCrewLog(Base):
    __tablename__ = "tk_crew_logs"
    __table_args__ = (
        UniqueConstraint("work_date", "vehicle_id", name="uq_tk_crew_logs_work_date_vehicle"),
    )

    id = Column(Integer, primary_key=True, index=True)
    work_date = Column(Date, nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("tk_vehicles.id"), nullable=False, index=True)
    created_by_employee_id = Column(Integer, ForeignKey("tk_employees.id"), nullable=False, index=True)
    status = Column(SAEnum(TkCrewLogStatus, name="tk_crew_log_status"), nullable=False, default=TkCrewLogStatus.draft)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    vehicle = relationship("TkVehicle", lazy="joined", foreign_keys=[vehicle_id])
    created_by = relationship("TkEmployee", lazy="joined", foreign_keys=[created_by_employee_id])
    members = relationship("TkCrewLogMember", cascade="all, delete-orphan", lazy="selectin")
    segments = relationship("TkCrewWorkSegment", cascade="all, delete-orphan", lazy="selectin")


class TkCrewLogMember(Base):
    __tablename__ = "tk_crew_log_members"
    __table_args__ = (
        UniqueConstraint("crew_log_id", "employee_id", name="uq_tk_crew_log_members_log_employee"),
    )

    id = Column(Integer, primary_key=True, index=True)
    crew_log_id = Column(Integer, ForeignKey("tk_crew_logs.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("tk_employees.id"), nullable=False, index=True)
    override_start_at = Column(DateTime(timezone=True), nullable=True)
    override_end_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    employee = relationship("TkEmployee", lazy="joined", foreign_keys=[employee_id])


class TkCrewWorkSegment(Base):
    __tablename__ = "tk_crew_work_segments"

    id = Column(Integer, primary_key=True, index=True)
    crew_log_id = Column(Integer, ForeignKey("tk_crew_logs.id"), nullable=False, index=True)
    site_id = Column(Integer, ForeignKey("tk_sites.id"), nullable=False, index=True)

    segment_type = Column(SAEnum(TkSegmentType, name="tk_segment_type"), nullable=False, default=TkSegmentType.work)

    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=True, index=True)

    start_lat = Column(Float, nullable=False)
    start_lng = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=True)
    end_lng = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    site = relationship("TkSite", lazy="joined", foreign_keys=[site_id])


class TkAbsence(Base):
    __tablename__ = "tk_absences"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("tk_employees.id"), nullable=False, index=True)
    date_from = Column(Date, nullable=False, index=True)
    date_to = Column(Date, nullable=False, index=True)
    type = Column(SAEnum(TkAbsenceType, name="tk_absence_type"), nullable=False)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    employee = relationship("TkEmployee", lazy="joined", foreign_keys=[employee_id])


class TkDailyStatusOverride(Base):
    __tablename__ = "tk_daily_status_overrides"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_tk_daily_status_overrides_employee_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("tk_employees.id"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    status = Column(SAEnum(TkDailyStatus, name="tk_daily_status"), nullable=False)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    employee = relationship("TkEmployee", lazy="joined", foreign_keys=[employee_id])




