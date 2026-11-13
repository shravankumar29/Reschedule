"""SQLAlchemy model – Disruption."""
from sqlalchemy import Column, Integer, String, Float, JSON
from ..database import Base


class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, index=True)
    disruption_id = Column(String, unique=True, index=True, nullable=False)
    disruption_type = Column(String, nullable=False)   # Machine Breakdown | Rush Order | Material Delay
    resource = Column(String, nullable=False)          # machine_id or material name
    reported_at = Column(String, nullable=False)       # ISO datetime string
    severity = Column(String, default="High")          # Critical | High | Medium | Low
    status = Column(String, default="Open")            # Open | Analyzed | Resolved
    description = Column(String, nullable=True)
    affected_job_ids = Column(JSON, default=list)      # list[str] job_id values
    # For machine breakdowns
    breakdown_start = Column(String, nullable=True)    # ISO datetime
    estimated_repair_hours = Column(Float, nullable=True)
    recovery_notes = Column(String, nullable=True)

