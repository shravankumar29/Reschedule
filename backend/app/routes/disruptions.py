"""FastAPI router – Disruption management."""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.disruption import Disruption
from ..models.machine import Machine
from ..models.job import Job
from ..schemas.disruption import DisruptionCreate, DisruptionRead

router = APIRouter(prefix="/api/disruptions", tags=["disruptions"])


def _next_id(db: Session) -> str:
    count = db.query(Disruption).count()
    return f"D-{count + 1:04d}"


@router.get("/", response_model=List[DisruptionRead])
def list_disruptions(db: Session = Depends(get_db)):
    return db.query(Disruption).order_by(Disruption.id.desc()).all()


@router.post("/", response_model=DisruptionRead, status_code=201)
def create_disruption(payload: DisruptionCreate, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).isoformat()
    breakdown_start = payload.breakdown_start or "10:00"
    repair_hours = payload.estimated_repair_hours or 3.0

    target_machine = None
    canonical_resource = payload.resource

    # Strict validation of machine for Machine Breakdown disruptions
    if payload.disruption_type == "Machine Breakdown":
        resource_raw = (payload.resource or "").strip()
        mid = resource_raw.split(" · ")[0].strip()
        target_machine = (
            db.query(Machine)
            .filter((Machine.machine_id == mid) | (Machine.machine_id == resource_raw) | (Machine.name == resource_raw))
            .first()
        )
        if not target_machine:
            valid_ids = [m.machine_id for m in db.query(Machine).all()]
            raise HTTPException(
                status_code=400,
                detail=f"Machine '{resource_raw}' does not exist in production database. Valid machines: {valid_ids}",
            )
        canonical_resource = f"{target_machine.machine_id} · {target_machine.name}"

    # Validate affected jobs if provided
    if payload.affected_job_ids:
        for jid in payload.affected_job_ids:
            if not db.query(Job).filter(Job.job_id == jid).first():
                raise HTTPException(
                    status_code=400,
                    detail=f"Job '{jid}' does not exist in production database.",
                )

    d = Disruption(
        disruption_id=_next_id(db),
        reported_at=now,
        disruption_type=payload.disruption_type,
        resource=canonical_resource,
        severity=payload.severity,
        status="Open",
        description=payload.description or f"Breakdown on {canonical_resource}",
        affected_job_ids=payload.affected_job_ids or [],
        breakdown_start=breakdown_start,
        estimated_repair_hours=repair_hours,
        recovery_notes=f"Repair estimated {repair_hours}h from {breakdown_start}",
    )
    db.add(d)

    # Attach maintenance period to the validated machine
    if target_machine:
        target_machine.available = False
        target_machine.current_task = f"Breakdown ({breakdown_start}, {repair_hours}h)"
        period = {
            "start": breakdown_start,
            "repair_hours": repair_hours,
            "reason": payload.description or f"Breakdown from {breakdown_start}",
        }
        periods = list(target_machine.maintenance_periods or [])
        periods.append(period)
        target_machine.maintenance_periods = periods

    db.commit()
    db.refresh(d)
    return d


@router.get("/{disruption_id}", response_model=DisruptionRead)
def get_disruption(disruption_id: str, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d:
        raise HTTPException(404, "Disruption not found")
    return d


@router.patch("/{disruption_id}/resolve", response_model=DisruptionRead)
def resolve_disruption(disruption_id: str, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d:
        raise HTTPException(404, "Disruption not found")
    d.status = "Resolved"
    if d.disruption_type == "Machine Breakdown" and d.resource:
        mid = d.resource.split(" · ")[0].strip()
        machine = db.query(Machine).filter((Machine.machine_id == mid) | (Machine.machine_id == d.resource)).first()
        if machine:
            # Check if any other open/analyzed disruptions remain for this machine
            other_active = (
                db.query(Disruption)
                .filter(
                    Disruption.id != d.id,
                    Disruption.disruption_type == "Machine Breakdown",
                    Disruption.status.in_(["Open", "Analyzed"]),
                )
                .all()
            )
            has_other = any(od.resource.split(" · ")[0].strip() == mid for od in other_active)
            if not has_other:
                machine.available = True
                machine.current_task = None
    db.commit()
    db.refresh(d)
    return d
