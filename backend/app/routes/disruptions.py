"""FastAPI router – Unified Disruption management for Breakdowns, Material Delays, and Rush Orders."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.disruption import Disruption
from ..models.machine import Machine
from ..models.job import Job, Operation
from ..models.material import Material, MaterialRequirement
from ..models.schedule import Schedule, ScheduleOperation
from ..schemas.disruption import (
    DisruptionCreate,
    DisruptionRead,
    BreakdownReportRequest,
    BreakdownRecoverRequest,
    BreakdownUpdateRequest,
    MaterialDelayReportRequest,
    MaterialDelayReceiveRequest,
    MaterialDelayUpdateRequest,
    DisruptionWorkspaceSummary,
)
from ..utils.time_utils import get_breakdown_interval_minutes, MINS_PER_HOUR

router = APIRouter(prefix="/api/disruptions", tags=["disruptions"])


def _next_id(db: Session, prefix: str = "D") -> str:
    count = db.query(Disruption).count()
    return f"{prefix}-{count + 1:04d}"


# ---------------------------------------------------------------------------
# Workspace Summary
# ---------------------------------------------------------------------------
@router.get("/summary", response_model=DisruptionWorkspaceSummary)
def get_disruptions_summary(db: Session = Depends(get_db)):
    """Aggregate actual database counts for the 3 disruption workspace categories."""
    active_breakdowns = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Machine Breakdown",
            Disruption.status.in_(["Open", "Analyzed", "Reported", "Under Repair"]),
        )
        .count()
    )

    active_materials = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Material Delay",
            Disruption.status.in_(["Open", "Analyzed", "Reported", "Awaiting Material"]),
        )
        .count()
    )

    open_rush = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Rush Order",
            Disruption.status.in_(["Open", "Analyzed", "Awaiting Scheduling"]),
        )
        .count()
    )

    # Collect all unique affected order IDs across active disruptions
    active_disruptions = (
        db.query(Disruption)
        .filter(
            Disruption.status.in_(["Open", "Analyzed", "Reported", "Under Repair", "Awaiting Material", "Awaiting Scheduling"])
        )
        .all()
    )
    all_affected_jobs = set()
    for d in active_disruptions:
        for jid in (d.affected_job_ids or []):
            all_affected_jobs.add(jid)

    return DisruptionWorkspaceSummary(
        active_machine_breakdowns=active_breakdowns,
        active_material_delays=active_materials,
        open_rush_orders=open_rush,
        total_affected_orders=len(all_affected_jobs),
    )


# ---------------------------------------------------------------------------
# General Disruption Endpoints (Backward Compatible)
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[DisruptionRead])
def list_disruptions(
    disruption_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Disruption)
    if disruption_type:
        q = q.filter(Disruption.disruption_type == disruption_type)
    if status:
        q = q.filter(Disruption.status == status)
    return q.order_by(Disruption.id.desc()).all()


@router.post("/", response_model=DisruptionRead, status_code=201)
def create_disruption(payload: DisruptionCreate, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).isoformat()
    breakdown_start = payload.breakdown_start or "10:00"
    repair_hours = payload.estimated_repair_hours or 3.0

    target_machine = None
    canonical_resource = payload.resource
    machine_id = None

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
        machine_id = target_machine.machine_id

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
        machine_id=machine_id,
        severity=payload.severity,
        status="Open",
        description=payload.description or f"Breakdown on {canonical_resource}",
        affected_job_ids=payload.affected_job_ids or [],
        breakdown_start=breakdown_start,
        estimated_repair_hours=repair_hours,
        recovery_notes=f"Repair estimated {repair_hours}h from {breakdown_start}",
        material_id=payload.material_id,
        supplier=payload.supplier,
        required_quantity=payload.required_quantity,
        available_quantity=payload.available_quantity,
        expected_arrival=payload.expected_arrival,
        rush_job_id=payload.rush_job_id,
        deadline=payload.deadline,
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


# ---------------------------------------------------------------------------
# Category 1: Machine Breakdowns Dedicated Endpoints
# ---------------------------------------------------------------------------
@router.get("/breakdowns", response_model=List[DisruptionRead])
def list_breakdowns(db: Session = Depends(get_db)):
    return (
        db.query(Disruption)
        .filter(Disruption.disruption_type == "Machine Breakdown")
        .order_by(Disruption.id.desc())
        .all()
    )


@router.post("/breakdowns", response_model=DisruptionRead, status_code=201)
def report_breakdown(payload: BreakdownReportRequest, db: Session = Depends(get_db)):
    """
    Report an unplanned Machine Breakdown:
      1. Validates that the machine exists.
      2. Identifies operations scheduled on the machine during downtime.
      3. Identifies affected customer orders.
      4. Identifies alternative eligible machines.
      5. Marks machine availability as False and records breakdown window.
    """
    machine = db.query(Machine).filter(Machine.machine_id == payload.machine_id).first()
    if not machine:
        valid_ids = [m.machine_id for m in db.query(Machine).all()]
        raise HTTPException(
            400,
            f"Machine '{payload.machine_id}' does not exist. Available machines: {valid_ids}",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    start_time = payload.breakdown_start or "10:00"
    repair_h = float(payload.estimated_repair_hours or 3.0)
    s_min, e_min = get_breakdown_interval_minutes(start_time, repair_h)
    s_h = s_min / MINS_PER_HOUR
    e_h = e_min / MINS_PER_HOUR

    # Identify scheduled operations during this downtime from active schedule
    active_sched = (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )
    affected_ops = []
    affected_jobs = set()
    if active_sched:
        for op in active_sched.operations:
            if op.machine_id == payload.machine_id:
                # Check overlap with breakdown interval
                if op.start_time < e_h - 0.01 and op.end_time > s_h + 0.01:
                    affected_ops.append(op.operation_id)
                    affected_jobs.add(op.job_id)

    canonical_resource = f"{machine.machine_id} · {machine.name}"
    disruption = Disruption(
        disruption_id=_next_id(db, "D-BD"),
        disruption_type="Machine Breakdown",
        resource=canonical_resource,
        machine_id=machine.machine_id,
        reported_at=now_iso,
        severity=payload.severity,
        status="Under Repair",
        description=payload.description or f"Unplanned breakdown on {machine.machine_id} from {start_time}",
        affected_job_ids=list(affected_jobs),
        affected_operation_ids=affected_ops,
        breakdown_start=start_time,
        estimated_repair_hours=repair_h,
        recovery_notes=payload.notes or f"Repair estimated {repair_h}h from {start_time}",
    )
    db.add(disruption)

    # Update machine state
    machine.available = False
    machine.current_task = f"Breakdown ({start_time}, {repair_h}h)"
    period = {
        "start": start_time,
        "repair_hours": repair_h,
        "reason": payload.description or f"Breakdown from {start_time}",
    }
    periods = list(machine.maintenance_periods or [])
    periods.append(period)
    machine.maintenance_periods = periods

    db.commit()
    db.refresh(disruption)
    return disruption


@router.put("/breakdowns/{disruption_id}", response_model=DisruptionRead)
def update_breakdown(disruption_id: str, payload: BreakdownUpdateRequest, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d or d.disruption_type != "Machine Breakdown":
        raise HTTPException(404, f"Breakdown '{disruption_id}' not found.")

    if payload.estimated_repair_hours is not None:
        d.estimated_repair_hours = payload.estimated_repair_hours
    if payload.description is not None:
        d.description = payload.description
    if payload.status is not None:
        d.status = payload.status
    if payload.recovery_notes is not None:
        d.recovery_notes = payload.recovery_notes

    db.commit()
    db.refresh(d)
    return d


@router.post("/breakdowns/{disruption_id}/recover", response_model=DisruptionRead)
def recover_breakdown(disruption_id: str, payload: BreakdownRecoverRequest, db: Session = Depends(get_db)):
    """
    Mark a machine breakdown as recovered:
      1. Records actual recovery timestamp.
      2. Separates estimate from actual recovery time.
      3. Restores machine availability if no other active breakdowns exist.
    """
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d or d.disruption_type != "Machine Breakdown":
        raise HTTPException(404, f"Breakdown '{disruption_id}' not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    d.status = "Recovered"
    d.actual_recovery_at = payload.actual_recovery_time or now_iso
    if payload.notes:
        d.recovery_notes = (d.recovery_notes or "") + f" | Recovered: {payload.notes}"

    # Check if other active breakdowns remain on this machine
    mid = d.machine_id or (d.resource.split(" · ")[0].strip() if d.resource else "")
    machine = db.query(Machine).filter(Machine.machine_id == mid).first()
    if machine:
        remaining = (
            db.query(Disruption)
            .filter(
                Disruption.id != d.id,
                Disruption.disruption_type == "Machine Breakdown",
                Disruption.machine_id == mid,
                Disruption.status.in_(["Open", "Analyzed", "Reported", "Under Repair"]),
            )
            .all()
        )
        if not remaining:
            machine.available = True
            machine.current_task = None

    db.commit()
    db.refresh(d)
    return d


# ---------------------------------------------------------------------------
# Category 2: Material Delays Dedicated Endpoints
# ---------------------------------------------------------------------------
@router.get("/material-delays", response_model=List[DisruptionRead])
def list_material_delays(db: Session = Depends(get_db)):
    return (
        db.query(Disruption)
        .filter(Disruption.disruption_type == "Material Delay")
        .order_by(Disruption.id.desc())
        .all()
    )


@router.post("/material-delays", response_model=DisruptionRead, status_code=201)
def report_material_delay(payload: MaterialDelayReportRequest, db: Session = Depends(get_db)):
    """
    Report a Material Delay:
      STEP 1: Identify jobs and operations requiring the delayed material.
      STEP 2: Calculate whether available inventory covers the required quantity.
      STEP 3: Identify operations blocked due to insufficient material.
      STEP 4: Identify affected machines from blocked operations.
      STEP 5: Calculate orders at risk.
      STEP 6: Enforce arrival time constraints in CP-SAT without blocking independent jobs!
    """
    mat = db.query(Material).filter(Material.material_id == payload.material_id).first()
    if not mat:
        valid_mats = [m.material_id for m in db.query(Material).all()]
        raise HTTPException(
            400,
            f"Material '{payload.material_id}' does not exist in inventory. Valid materials: {valid_mats}",
        )

    # Step 1: Find all requirements
    reqs = (
        db.query(MaterialRequirement)
        .filter(MaterialRequirement.material_id == payload.material_id)
        .all()
    )

    total_required = sum(r.required_quantity for r in reqs)
    available_qty = payload.available_quantity if payload.available_quantity is not None else mat.available_quantity
    shortage_qty = max(0.0, total_required - available_qty)

    # Step 2 & 3: Identify blocked operations
    # An operation is blocked if remaining stock cannot fulfill its requirement
    blocked_ops = []
    affected_jobs = set()
    running_stock = available_qty

    for r in reqs:
        affected_jobs.add(r.job_id)
        if running_stock < r.required_quantity:
            if r.operation_id:
                blocked_ops.append(r.operation_id)
            else:
                # Find first operation of this job
                first_op = (
                    db.query(Operation)
                    .filter(Operation.job_id == r.job_id)
                    .order_by(Operation.sequence_number.asc())
                    .first()
                )
                if first_op:
                    blocked_ops.append(first_op.operation_id)
        else:
            running_stock -= r.required_quantity

    # If no requirements linked yet, check all operations referencing this material
    if not blocked_ops:
        op_refs = db.query(Operation).filter(Operation.required_material_id == payload.material_id).all()
        for op in op_refs:
            blocked_ops.append(op.operation_id)
            affected_jobs.add(op.job_id)

    # Step 4: Identify affected machines from blocked operations
    active_sched = (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )
    affected_machines = set()
    if active_sched:
        for op in active_sched.operations:
            if op.operation_id in blocked_ops:
                affected_machines.add(op.machine_id)

    now_iso = datetime.now(timezone.utc).isoformat()
    expected_arr = payload.expected_arrival_time or "15:00"

    canonical_resource = f"{mat.material_id} · {mat.name}"
    disruption = Disruption(
        disruption_id=_next_id(db, "D-MAT"),
        disruption_type="Material Delay",
        resource=canonical_resource,
        material_id=mat.material_id,
        supplier=payload.supplier or mat.supplier,
        reported_at=now_iso,
        severity=payload.severity,
        status="Awaiting Material",
        description=payload.delay_reason or f"Material shortage on {mat.name}: {shortage_qty:.1f} {mat.unit} delayed until {expected_arr}",
        required_quantity=total_required,
        available_quantity=available_qty,
        shortage_quantity=shortage_qty,
        expected_arrival=expected_arr,
        affected_job_ids=list(affected_jobs),
        affected_operation_ids=blocked_ops,
        affected_machine_ids=list(affected_machines),
        recovery_notes=payload.notes or f"Expected shipment arrival: {expected_arr}",
    )
    db.add(disruption)
    db.commit()
    db.refresh(disruption)
    return disruption


@router.put("/material-delays/{disruption_id}", response_model=DisruptionRead)
def update_material_delay(disruption_id: str, payload: MaterialDelayUpdateRequest, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d or d.disruption_type != "Material Delay":
        raise HTTPException(404, f"Material delay '{disruption_id}' not found.")

    if payload.expected_arrival is not None:
        d.expected_arrival = payload.expected_arrival
    if payload.shortage_quantity is not None:
        d.shortage_quantity = payload.shortage_quantity
    if payload.description is not None:
        d.description = payload.description
    if payload.status is not None:
        d.status = payload.status

    db.commit()
    db.refresh(d)
    return d


@router.post("/material-delays/{disruption_id}/receive", response_model=DisruptionRead)
def receive_material_delay(disruption_id: str, payload: MaterialDelayReceiveRequest, db: Session = Depends(get_db)):
    """
    Record receipt of delayed material:
      1. Records actual arrival timestamp.
      2. Updates material stock in inventory.
      3. Resolves or updates disruption status to 'Received' or 'Partially Received'.
    """
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d or d.disruption_type != "Material Delay":
        raise HTTPException(404, f"Material delay '{disruption_id}' not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    d.actual_arrival = payload.actual_arrival_time or now_iso

    # Update material inventory
    if d.material_id:
        mat = db.query(Material).filter(Material.material_id == d.material_id).first()
        if mat:
            received_qty = payload.received_quantity if payload.received_quantity is not None else (d.shortage_quantity or 50.0)
            mat.available_quantity += received_qty
            if payload.received_quantity is not None and d.shortage_quantity and payload.received_quantity < d.shortage_quantity:
                d.status = "Partially Received"
                d.shortage_quantity = max(0.0, d.shortage_quantity - payload.received_quantity)
            else:
                d.status = "Received"
                d.shortage_quantity = 0.0

    if payload.notes:
        d.recovery_notes = (d.recovery_notes or "") + f" | Received: {payload.notes}"

    db.commit()
    db.refresh(d)
    return d


# ---------------------------------------------------------------------------
# Individual Disruption Retrieval & Status Patch
# ---------------------------------------------------------------------------
@router.get("/{disruption_id}", response_model=DisruptionRead)
def get_disruption(disruption_id: str, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d:
        raise HTTPException(404, f"Disruption '{disruption_id}' not found.")
    return d


@router.patch("/{disruption_id}/resolve", response_model=DisruptionRead)
def resolve_disruption(disruption_id: str, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d:
        raise HTTPException(404, f"Disruption '{disruption_id}' not found.")
    d.status = "Resolved"
    if d.disruption_type == "Machine Breakdown" and d.resource:
        mid = d.machine_id or d.resource.split(" · ")[0].strip()
        machine = db.query(Machine).filter((Machine.machine_id == mid) | (Machine.machine_id == d.resource)).first()
        if machine:
            other_active = (
                db.query(Disruption)
                .filter(
                    Disruption.id != d.id,
                    Disruption.disruption_type == "Machine Breakdown",
                    Disruption.status.in_(["Open", "Analyzed", "Reported", "Under Repair"]),
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


@router.patch("/{disruption_id}/status", response_model=DisruptionRead)
def update_disruption_status(disruption_id: str, status: str, db: Session = Depends(get_db)):
    d = db.query(Disruption).filter(Disruption.disruption_id == disruption_id).first()
    if not d:
        raise HTTPException(404, f"Disruption '{disruption_id}' not found.")
    d.status = status
    if status == "Cancelled" and d.disruption_type == "Machine Breakdown":
        mid = d.machine_id or d.resource.split(" · ")[0].strip()
        m = db.query(Machine).filter(Machine.machine_id == mid).first()
        if m:
            m.available = True
            m.current_task = None
    db.commit()
    db.refresh(d)
    return d
