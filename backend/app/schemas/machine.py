"""Pydantic schemas for Machine."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MachineBase(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "CNC-1"})
    name: str = Field(..., json_schema_extra={"example": "CNC Milling Machine 1"})
    machine_type: str = Field(..., json_schema_extra={"example": "CNC"})
    supported_operations: List[str] = Field(..., json_schema_extra={"example": ["Milling", "Drilling"]})
    working_start_hour: int = Field(6, ge=0, le=23)
    working_end_hour: int = Field(22, ge=1, le=24)
    maintenance_periods: Optional[List[Dict[str, Any]]] = None


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    machine_type: Optional[str] = None
    supported_operations: Optional[List[str]] = None
    available: Optional[bool] = None
    working_start_hour: Optional[int] = None
    working_end_hour: Optional[int] = None
    maintenance_periods: Optional[List[Dict[str, Any]]] = None
    utilization: Optional[int] = None
    current_task: Optional[str] = None


class MachineRead(MachineBase):
    id: int
    available: bool
    utilization: int
    current_task: Optional[str]

    model_config = {"from_attributes": True}

