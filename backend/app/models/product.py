"""SQLAlchemy models – Product and ProductOperation (Routing Template)."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    category = Column(String, nullable=False, default="Precision Machining")
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

    routing_operations = relationship(
        "ProductOperation",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductOperation.sequence_number",
    )


class ProductOperation(Base):
    __tablename__ = "product_operations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), nullable=False)
    operation_name = Column(String, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    processing_time = Column(Float, nullable=False)  # hours
    duration_basis = Column(String, default="fixed")  # fixed | per_unit | per_batch
    eligible_machine_ids = Column(JSON, nullable=False)  # list[str]
    required_material_id = Column(String, nullable=True)
    required_material_qty = Column(Float, nullable=True)
    notes = Column(String, nullable=True)

    product = relationship("Product", back_populates="routing_operations")

