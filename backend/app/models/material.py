"""SQLAlchemy models for Material Inventory and Material Requirements."""
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, default="Raw Material")
    unit = Column(String, default="kg")
    available_quantity = Column(Float, default=0.0)
    reserved_quantity = Column(Float, default=0.0)
    min_stock_level = Column(Float, default=10.0)
    supplier = Column(String, nullable=True)
    lead_time_days = Column(Integer, default=2)

    requirements = relationship(
        "MaterialRequirement",
        back_populates="material",
        cascade="all, delete-orphan",
    )


class MaterialRequirement(Base):
    __tablename__ = "material_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    operation_id = Column(String, nullable=True)
    material_id = Column(String, ForeignKey("materials.material_id"), nullable=False)
    required_quantity = Column(Float, nullable=False)
    allocated_quantity = Column(Float, default=0.0)

    material = relationship("Material", back_populates="requirements")

