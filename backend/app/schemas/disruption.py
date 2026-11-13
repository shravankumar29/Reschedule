"""Pydantic schemas for Disruption."""
from typing import List, Optional
from pydantic import BaseModel, Field


class DisruptionCreate(BaseModel):
    disruption_type: str = Field(..., pattern="^(Machine Breakdown|Rush Order|Material Delay)$")
    resource: str
    severity: str = Field("High", pattern="^(Critical|High|Medium|Low)$")
    description: Optional[str] = None
    affected_job_ids: List[str] = Field(default_factory=list)
    breakdown_start: Optional[str] = None      # ISO datetime
    estimated_repair_hours: Optional[float] = None


class DisruptionRead(BaseModel):
    id: int
    disruption_id: str
    disruption_type: str
    resource: str
    reported_at: str
    severity: str
    status: str
    description: Optional[str]
    affected_job_ids: List[str]
    breakdown_start: Optional[str]
    estimated_repair_hours: Optional[float]
    recovery_notes: Optional[str]

    model_config = {"from_attributes": True}

