"""Pydantic schemas for Schedule and ScheduleOperation."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RescheduleRequest(BaseModel):
    disruption_id: Optional[str] = None
    mode: Optional[str] = "auto"  # "optimization" | "recovery" | "auto"
    prioritize_urgent: bool = True
    minimize_delay: bool = True
    minimize_idle: bool = False
    minimize_overtime: bool = False


class ScheduleApproveRequest(BaseModel):
    schedule_id: str


class ScheduleOperationRead(BaseModel):
    id: int
    schedule_id: str
    job_id: str
    operation_id: str
    machine_id: str
    start_time: float
    end_time: float
    duration: float
    date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    frozen: bool

    model_config = {"from_attributes": True}


class ScheduleRead(BaseModel):
    id: int
    schedule_id: str
    created_at: str
    schedule_type: str
    status: str
    makespan_hours: Optional[float]
    total_jobs: int
    on_time_count: int
    delayed_count: int
    disruption_id: Optional[str]
    solver_status: Optional[str]
    operations: List[ScheduleOperationRead] = []

    model_config = {"from_attributes": True}

