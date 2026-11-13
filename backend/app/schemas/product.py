"""Pydantic schemas for Product and Product Routing Templates."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOperationBase(BaseModel):
    operation_name: str
    sequence_number: int = Field(..., ge=1)
    processing_time: float = Field(..., gt=0, description="Processing time in hours")
    duration_basis: str = Field("fixed", pattern="^(fixed|per_unit|per_batch)$")
    eligible_machine_ids: List[str] = Field(..., min_length=1)
    required_material_id: Optional[str] = None
    required_material_qty: Optional[float] = None
    notes: Optional[str] = None


class ProductOperationCreate(ProductOperationBase):
    pass


class ProductOperationRead(ProductOperationBase):
    id: int
    product_id: str

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: str = "Precision Machining"
    is_active: bool = True


class ProductCreate(ProductBase):
    product_id: str = Field(..., json_schema_extra={"example": "PROD-001"})
    routing_operations: List[ProductOperationCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    routing_operations: Optional[List[ProductOperationCreate]] = None


class ProductRead(ProductBase):
    id: int
    product_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    routing_operations: List[ProductOperationRead] = []

    model_config = {"from_attributes": True}

