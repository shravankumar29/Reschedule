"""SQLAlchemy models – Schedule and ScheduleOperation."""
from sqlalchemy import Column, Float, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(String, nullable=False)   # ISO datetime
    schedule_type = Column(String, default="initial")  # initial | revised
    status = Column(String, default="active")           # active | superseded
    # summary metrics
    makespan_hours = Column(Float, nullable=True)
    total_jobs = Column(Integer, default=0)
    on_time_count = Column(Integer, default=0)
    delayed_count = Column(Integer, default=0)
    # link to disruption that caused rescheduling (nullable for initial)
    disruption_id = Column(String, nullable=True)
    solver_status = Column(String, nullable=True)       # OPTIMAL | FEASIBLE | INFEASIBLE

    operations = relationship("ScheduleOperation", back_populates="schedule", cascade="all, delete-orphan")


class ScheduleOperation(Base):
    __tablename__ = "schedule_operations"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String, ForeignKey("schedules.schedule_id"), nullable=False)
    job_id = Column(String, nullable=False)
    operation_id = Column(String, nullable=False)
    machine_id = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)   # hours from epoch reference (day start)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    date = Column(String, nullable=True)         # YYYY-MM-DD
    end_date = Column(String, nullable=True)     # YYYY-MM-DD
    status = Column(String, default="Scheduled")  # Scheduled | Ongoing | Completed | Delayed | Rescheduled
    frozen = Column(Boolean, default=False)       # completed ops are frozen during rescheduling

    schedule = relationship("Schedule", back_populates="operations")

