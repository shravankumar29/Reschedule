"""FastAPI router for Rush Order Disruption Management."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.disruption import Disruption
from ..models.job import Job, Operation
from ..models.machine import Machine
from ..models.material import Material, MaterialRequirement
from ..models.schedule import Schedule
from ..schemas.disruption import RushOrderCreateRequest, DisruptionRead
from ..schemas.job import JobRead
from ..services.rescheduling_engine import run_rescheduling

router = APIRouter(prefix="/api/rush-orders", tags=["rush-orders"])


@router.get("/")
def list_rush_orders(db: Session = Depends(get_db)):
    """List all rush orders along with their operational routes and disruption status."""
    rush_jobs = (
        db.query(Job)
        .filter((Job.is_rush_order == True) | (Job.priority == "Urgent"))
        .order_by(Job.id.desc())
        .all()
    )
    result = []
    for rj in rush_jobs:
        # Check linked disruption
        disr = db.query(Disruption).filter(Disruption.rush_job_id == rj.job_id).first()
        status_label = disr.status if disr else ("Completed" if rj.status == "Completed" else "Awaiting Scheduling")
        ops = [
            {
                "operation_id": o.operation_id,
                "operation_name": o.operation_name,
                "processing_time": o.processing_time,
                "eligible_machine_ids": o.eligible_machine_ids,
                "sequence_number": o.sequence_number,
                "status": o.status,
            }
            for o in rj.operations
        ]
        mat_reqs = [
            {
                "material_id": mr.material_id,
                "required_quantity": mr.required_quantity,
                "allocated_quantity": mr.allocated_quantity,
            }
            for mr in db.query(MaterialRequirement).filter(MaterialRequirement.job_id == rj.job_id).all()
        ]
        result.append({
            "rush_order_id": rj.job_id,
            "disruption_id": disr.disruption_id if disr else None,
            "customer_name": rj.customer_name,
            "product_name": rj.product_name,
            "quantity": rj.quantity,
            "order_date": rj.order_date,
            "deadline": rj.deadline,
            "priority": rj.priority,
            "status": status_label,
            "production_status": rj.status,
            "operations": ops,
            "required_materials": mat_reqs,
        })
    return result


@router.post("/", status_code=201)
def create_rush_order(payload: RushOrderCreateRequest, db: Session = Depends(get_db)):
    """
    Add a new Rush Order.
    Validates:
      1. Operation sequence and processing times (> 0).
      2. Valid eligible machine IDs that exist in factory.
      3. Valid material IDs if materials are required.
    Persists normal Job with priority='Urgent' and linked Disruption record.
    """
    if not payload.operations or len(payload.operations) == 0:
        raise HTTPException(400, "A rush order must contain at least one production operation.")

    machines = {m.machine_id: m for m in db.query(Machine).all()}
    for op in payload.operations:
        if op.processing_time <= 0:
            raise HTTPException(400, f"Operation '{op.operation_name}' must have processing time > 0.")
        if not op.eligible_machine_ids:
            raise HTTPException(400, f"Operation '{op.operation_name}' must specify at least one eligible machine.")
        for mid in op.eligible_machine_ids:
            if mid not in machines:
                raise HTTPException(400, f"Machine '{mid}' does not exist in production database.")

    # Validate materials if specified
    if payload.required_materials:
        for mr in payload.required_materials:
            mat_id = mr.get("material_id")
            if not db.query(Material).filter(Material.material_id == mat_id).first():
                raise HTTPException(400, f"Material '{mat_id}' does not exist in inventory.")

    now_iso = datetime.now(timezone.utc).isoformat()
    order_date = payload.order_date or now_iso[:10]

    # Generate rush order Job ID
    count = db.query(Job).count()
    job_id = f"RUSH-{count + 101}"

    job = Job(
        job_id=job_id,
        customer_name=payload.customer_name,
        product_name=payload.product_name,
        quantity=payload.quantity,
        priority="Urgent",
        order_date=order_date,
        deadline=payload.deadline,
        status="Pending",
        is_rush_order=True,
    )
    db.add(job)
    db.flush()

    for op_in in payload.operations:
        op = Operation(
            operation_id=f"{job_id}-OP{op_in.sequence_number}",
            job_id=job_id,
            operation_name=op_in.operation_name,
            processing_time=op_in.processing_time,
            eligible_machine_ids=op_in.eligible_machine_ids,
            sequence_number=op_in.sequence_number,
            status="Pending",
            required_material_id=op_in.required_material_id,
            required_material_qty=op_in.required_material_qty,
        )
        db.add(op)

    # Persist MaterialRequirements
    if payload.required_materials:
        for mr in payload.required_materials:
            req = MaterialRequirement(
                job_id=job_id,
                material_id=mr["material_id"],
                required_quantity=float(mr.get("quantity", 10.0)),
                allocated_quantity=0.0,
            )
            db.add(req)

    # Create Disruption tracking entry
    d_count = db.query(Disruption).count()
    disruption_id = f"D-RUSH-{d_count + 1:03d}"
    disruption = Disruption(
        disruption_id=disruption_id,
        disruption_type="Rush Order",
        resource=f"{job_id} · {payload.product_name}",
        reported_at=now_iso,
        severity="Critical",
        status="Awaiting Scheduling",
        description=f"Urgent customer order {job_id} for {payload.customer_name} ({payload.quantity} units, deadline: {payload.deadline})",
        affected_job_ids=[job_id],
        rush_job_id=job_id,
        deadline=payload.deadline,
    )
    db.add(disruption)

    db.commit()
    db.refresh(job)

    return {
        "success": True,
        "rush_order_id": job_id,
        "disruption_id": disruption_id,
        "customer_name": job.customer_name,
        "product_name": job.product_name,
        "deadline": job.deadline,
        "priority": job.priority,
        "operations_count": len(job.operations),
        "status": "Awaiting Scheduling",
    }


@router.post("/{rush_order_id}/schedule")
def schedule_rush_order(rush_order_id: str, db: Session = Depends(get_db)):
    """Initiate CP-SAT recovery to integrate this rush order into the active schedule."""
    job = db.query(Job).filter(Job.job_id == rush_order_id).first()
    if not job:
        raise HTTPException(404, f"Rush order '{rush_order_id}' not found.")

    disr = db.query(Disruption).filter(Disruption.rush_job_id == rush_order_id).first()
    resched_result = run_rescheduling(
        db=db,
        disruption_id=disr.disruption_id if disr else None,
        options={"mode": "recovery", "prioritize_urgent": True, "minimize_delay": True},
    )

    if disr and resched_result.get("solver_status") in ("OPTIMAL", "FEASIBLE"):
        disr.status = "Scheduled"
        db.commit()

    return resched_result

