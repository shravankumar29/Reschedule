"""SQLAlchemy models – Job and Operation."""
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    product_id = Column(String, ForeignKey("products.product_id"), nullable=True)
    customer_name = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    priority = Column(String, default="Medium")   # Low | Medium | High | Urgent
    order_date = Column(String, nullable=False)   # ISO date string YYYY-MM-DD
    deadline = Column(String, nullable=False)     # ISO date string YYYY-MM-DD
    status = Column(String, default="Pending")    # Pending | In Production | Completed | Delayed
    is_rush_order = Column(Boolean, default=False)

    operations = relationship("Operation", back_populates="job", cascade="all, delete-orphan", order_by="Operation.sequence_number")


class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(String, unique=True, index=True, nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    operation_name = Column(String, nullable=False)
    processing_time = Column(Float, nullable=False)   # hours
    duration_basis = Column(String, default="fixed")  # fixed | per_unit | per_batch
    routing_operation_id = Column(String, nullable=True)
    eligible_machine_ids = Column(JSON, nullable=False)  # list[str] machine_id values
    sequence_number = Column(Integer, nullable=False)
    status = Column(String, default="Pending")  # Pending | Scheduled | Ongoing | Completed | Delayed

    # Optional material requirement on operation level
    required_material_id = Column(String, nullable=True)
    required_material_qty = Column(Float, nullable=True)

    job = relationship("Job", back_populates="operations")
