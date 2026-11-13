"""Pydantic schemas for Disruption module across Machine Breakdowns, Material Delays, and Rush Orders."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DisruptionCreate(BaseModel):
    disruption_type: str = Field(..., pattern="^(Machine Breakdown|Rush Order|Material Delay)$")
    resource: str
    severity: str = Field("High", pattern="^(Critical|High|Medium|Low)$")
    description: Optional[str] = None
    affected_job_ids: List[str] = Field(default_factory=list)
    breakdown_start: Optional[str] = None
    estimated_repair_hours: Optional[float] = None
    # Material delay fields
    material_id: Optional[str] = None
    supplier: Optional[str] = None
    required_quantity: Optional[float] = None
    available_quantity: Optional[float] = None
    expected_arrival: Optional[str] = None
    # Rush order fields
    rush_job_id: Optional[str] = None
    deadline: Optional[str] = None


class BreakdownReportRequest(BaseModel):
    machine_id: str
    description: Optional[str] = None
    breakdown_start: str = "10:00"
    estimated_repair_hours: float = 3.0
    severity: str = "Critical"
    notes: Optional[str] = None


class BreakdownRecoverRequest(BaseModel):
    actual_recovery_time: Optional[str] = None  # e.g. "12:30" or ISO datetime
    notes: Optional[str] = None


class BreakdownUpdateRequest(BaseModel):
    estimated_repair_hours: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None
    recovery_notes: Optional[str] = None


class MaterialDelayReportRequest(BaseModel):
    material_id: str
    delay_reason: Optional[str] = None
    required_quantity: Optional[float] = None
    available_quantity: Optional[float] = None
    expected_arrival_date: Optional[str] = None
    expected_arrival_time: str = "15:00"
    supplier: Optional[str] = None
    severity: str = "High"
    notes: Optional[str] = None


class MaterialDelayReceiveRequest(BaseModel):
    actual_arrival_time: Optional[str] = None
    received_quantity: Optional[float] = None  # if partial or full
    notes: Optional[str] = None


class MaterialDelayUpdateRequest(BaseModel):
    expected_arrival: Optional[str] = None
    shortage_quantity: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


class RushOrderOperationInput(BaseModel):
    operation_name: str
    processing_time: float
    eligible_machine_ids: List[str]
    sequence_number: int
    required_material_id: Optional[str] = None
    required_material_qty: Optional[float] = None


class RushOrderCreateRequest(BaseModel):
    customer_name: str
    product_name: str
    quantity: int
    order_date: Optional[str] = None
    deadline: str
    priority: str = "Urgent"
    operations: List[RushOrderOperationInput]
    required_materials: Optional[List[Dict[str, Any]]] = None  # [{"material_id": str, "quantity": float}]


class DisruptionWorkspaceSummary(BaseModel):
    active_machine_breakdowns: int
    active_material_delays: int
    open_rush_orders: int
    total_affected_orders: int


class DisruptionRead(BaseModel):
    id: int
    disruption_id: str
    disruption_type: str
    resource: str
    reported_at: str
    severity: str
    status: str
    description: Optional[str] = None
    affected_job_ids: List[str] = []

    # Machine Breakdown Fields
    machine_id: Optional[str] = None
    breakdown_start: Optional[str] = None
    estimated_repair_hours: Optional[float] = None
    recovery_notes: Optional[str] = None
    actual_recovery_at: Optional[str] = None

    # Material Delay Fields
    material_id: Optional[str] = None
    supplier: Optional[str] = None
    required_quantity: Optional[float] = None
    available_quantity: Optional[float] = None
    shortage_quantity: Optional[float] = None
    expected_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    affected_operation_ids: List[str] = []
    affected_machine_ids: List[str] = []

    # Rush Order Fields
    rush_job_id: Optional[str] = None
    deadline: Optional[str] = None

    model_config = {"from_attributes": True}
