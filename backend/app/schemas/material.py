"""Pydantic schemas for Material Inventory and Requirements."""
from typing import List, Optional
from pydantic import BaseModel


class MaterialBase(BaseModel):
    material_id: str
    name: str
    category: str = "Raw Material"
    unit: str = "kg"
    available_quantity: float = 0.0
    reserved_quantity: float = 0.0
    min_stock_level: float = 10.0
    supplier: Optional[str] = None
    lead_time_days: int = 2


class MaterialCreate(BaseModel):
    material_id: str
    name: str
    category: str = "Raw Material"
    unit: str = "kg"
    available_quantity: float = 0.0
    min_stock_level: float = 10.0
    supplier: Optional[str] = None
    lead_time_days: int = 2


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    available_quantity: Optional[float] = None
    reserved_quantity: Optional[float] = None
    min_stock_level: Optional[float] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = None


class MaterialRequirementRead(BaseModel):
    id: int
    job_id: str
    operation_id: Optional[str] = None
    material_id: str
    required_quantity: float
    allocated_quantity: float

    model_config = {"from_attributes": True}


class MaterialRead(MaterialBase):
    id: int
    requirements: List[MaterialRequirementRead] = []

    model_config = {"from_attributes": True}

