"""FastAPI router – Machine CRUD."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from ..schemas.machine import MachineCreate, MachineRead, MachineUpdate

router = APIRouter(prefix="/api/machines", tags=["machines"])


@router.get("/", response_model=List[MachineRead])
def list_machines(db: Session = Depends(get_db)):
    return db.query(Machine).all()


@router.post("/", response_model=MachineRead, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreate, db: Session = Depends(get_db)):
    if db.query(Machine).filter(Machine.machine_id == payload.machine_id).first():
        raise HTTPException(400, "machine_id already exists")
    m = Machine(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/{machine_id}", response_model=MachineRead)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    m = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not m:
        raise HTTPException(404, "Machine not found")
    return m


@router.put("/{machine_id}", response_model=MachineRead)
def update_machine(machine_id: str, payload: MachineUpdate, db: Session = Depends(get_db)):
    m = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not m:
        raise HTTPException(404, "Machine not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    m = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not m:
        raise HTTPException(404, "Machine not found")
    # Block deletion if there are active (non-completed) operations assigned to this machine in an active schedule
    active_ops = (
        db.query(ScheduleOperation)
        .join(Schedule, ScheduleOperation.schedule_id == Schedule.schedule_id)
        .filter(
            ScheduleOperation.machine_id == machine_id,
            Schedule.status == "active",
            ScheduleOperation.status.notin_(["Completed", "Cancelled"]),
        )
        .count()
    )
    if active_ops > 0:
        raise HTTPException(
            409,
            f"Cannot remove machine {machine_id}: it has {active_ops} active scheduled "
            "operation(s). Complete or reassign them first.",
        )
    db.delete(m)
    db.commit()


@router.patch("/{machine_id}/availability", response_model=MachineRead)
def set_availability(machine_id: str, available: bool, db: Session = Depends(get_db)):
    m = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not m:
        raise HTTPException(404, "Machine not found")
    m.available = available
    if available:
        m.current_task = None
    db.commit()
    db.refresh(m)
    return m

