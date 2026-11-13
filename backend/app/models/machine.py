"""SQLAlchemy model – Machine."""
from sqlalchemy import Boolean, Column, Integer, JSON, String, Time
from ..database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
    supported_operations = Column(JSON, nullable=False, default=list)  # list[str]
    available = Column(Boolean, default=True)
    working_start_hour = Column(Integer, default=6)   # hour of day (0-23)
    working_end_hour = Column(Integer, default=22)    # hour of day (0-23)
    # list of {"start": "YYYY-MM-DDTHH:MM", "end": "YYYY-MM-DDTHH:MM", "reason": str}
    maintenance_periods = Column(JSON, nullable=True, default=list)
    # utilization 0-100 (updated after scheduling)
    utilization = Column(Integer, default=0)
    current_task = Column(String, nullable=True)

