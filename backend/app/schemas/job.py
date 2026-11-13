"""Pydantic schemas for Job and Operation."""
from typing import List, Optional
from pydantic import BaseModel, Field


class OperationCreate(BaseModel):
    operation_name: str
    processing_time: float = Field(..., gt=0, description="Processing time in hours")
    duration_basis: str = Field("fixed", pattern="^(fixed|per_unit|per_batch)$")
    eligible_machine_ids: List[str]
    sequence_number: int = Field(..., ge=1)
    routing_operation_id: Optional[str] = None
    required_material_id: Optional[str] = None
    required_material_qty: Optional[float] = None


class OperationRead(OperationCreate):
    id: int
    operation_id: str
    job_id: str
    status: str

    model_config = {"from_attributes": True}


class JobCreate(BaseModel):
    job_id: str = Field(..., json_schema_extra={"example": "J-101"})
    product_id: Optional[str] = None
    customer_name: str
    product_name: str
    quantity: int = Field(..., gt=0)
    priority: str = Field("Medium", pattern="^(Low|Medium|High|Urgent)$")
    order_date: str  # YYYY-MM-DD
    deadline: str    # YYYY-MM-DD
    operations: List[OperationCreate] = Field(default_factory=list)


class JobUpdate(BaseModel):
    product_id: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    priority: Optional[str] = None
    order_date: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[str] = None


class JobRead(BaseModel):
    id: int
    job_id: str
    product_id: Optional[str] = None
    customer_name: str
    product_name: str
    quantity: int
    priority: str
    order_date: str
    deadline: str
    status: str
    operations: List[OperationRead] = []

    model_config = {"from_attributes": True}

