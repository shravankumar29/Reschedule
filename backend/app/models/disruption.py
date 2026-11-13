"""SQLAlchemy model – Disruption supporting Machine Breakdowns, Material Delays, and Rush Orders."""
from sqlalchemy import Column, Float, Integer, JSON, String
from ..database import Base


class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, index=True)
    disruption_id = Column(String, unique=True, index=True, nullable=False)
    disruption_type = Column(String, nullable=False)   # Machine Breakdown | Material Delay | Rush Order
    resource = Column(String, nullable=False)          # machine_id, material_name, or order_id
    reported_at = Column(String, nullable=False)       # ISO datetime string
    severity = Column(String, default="High")          # Critical | High | Medium | Low
    # Statuses: Open | Analyzed | Resolved | Reported | Under Repair | Recovered | Awaiting Material | Received | Cancelled | Scheduled
    status = Column(String, default="Open")
    description = Column(String, nullable=True)
    affected_job_ids = Column(JSON, default=list)      # list[str] job_id values

    # --- Machine Breakdown Fields ---
    machine_id = Column(String, nullable=True)
    breakdown_start = Column(String, nullable=True)    # "HH:MM" or ISO datetime
    estimated_repair_hours = Column(Float, nullable=True)
    recovery_notes = Column(String, nullable=True)
    actual_recovery_at = Column(String, nullable=True)  # ISO datetime when actually recovered

    # --- Material Delay Fields ---
    material_id = Column(String, nullable=True)
    supplier = Column(String, nullable=True)
    required_quantity = Column(Float, nullable=True)
    available_quantity = Column(Float, nullable=True)
    shortage_quantity = Column(Float, nullable=True)
    expected_arrival = Column(String, nullable=True)    # "HH:MM" or ISO datetime
    actual_arrival = Column(String, nullable=True)      # ISO datetime when material received
    affected_operation_ids = Column(JSON, default=list) # list of blocked operation IDs
    affected_machine_ids = Column(JSON, default=list)   # list of affected machines

    # --- Rush Order Fields ---
    rush_job_id = Column(String, nullable=True)         # Reference to newly added rush Job
    deadline = Column(String, nullable=True)            # Delivery deadline
