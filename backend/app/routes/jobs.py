"""FastAPI router – Job and Operation CRUD with Product Routing & Details."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.job import Job, Operation
from ..models.product import Product, ProductOperation
from ..models.schedule import Schedule, ScheduleOperation
from ..models.machine import Machine
from ..schemas.job import JobCreate, JobRead, JobUpdate, OperationCreate, OperationRead

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _gen_op_id(job_id: str, seq: int) -> str:
    return f"{job_id}-OP{seq}"


@router.get("/", response_model=List[JobRead])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()


@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    if db.query(Job).filter(Job.job_id == payload.job_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job ID '{payload.job_id}' already exists.",
        )

    # 1. Product lookup & validation
    product_obj: Optional[Product] = None
    if payload.product_id:
        product_obj = db.query(Product).filter(Product.product_id == payload.product_id).first()
        if not product_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{payload.product_id}' not found in catalog.",
            )
        if not product_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{payload.product_id}' ({product_obj.name}) is inactive/decommissioned.",
            )
    elif payload.product_name:
        product_obj = db.query(Product).filter(Product.name == payload.product_name).first()

    # 2. Prepare operations
    ops_data = list(payload.operations)

    # If no operations specified, instantiate directly from Product Routing Template
    if not ops_data and product_obj and product_obj.routing_operations:
        for r_op in sorted(product_obj.routing_operations, key=lambda x: x.sequence_number):
            p_time = r_op.processing_time
            if r_op.duration_basis == "per_unit":
                p_time = round(r_op.processing_time * payload.quantity, 2)
            ops_data.append(
                OperationCreate(
                    operation_name=r_op.operation_name,
                    sequence_number=r_op.sequence_number,
                    processing_time=max(0.1, p_time),
                    duration_basis=r_op.duration_basis,
                    eligible_machine_ids=list(r_op.eligible_machine_ids),
                    routing_operation_id=f"{product_obj.product_id}-OP{r_op.sequence_number}",
                    required_material_id=r_op.required_material_id,
                    required_material_qty=r_op.required_material_qty,
                )
            )

    # Validate machines if operations exist
    all_machines = {m.machine_id for m in db.query(Machine).all()}
    for op in ops_data:
        if not op.eligible_machine_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operation '{op.operation_name}' must have at least one eligible machine.",
            )
        if all_machines:
            invalid = [mid for mid in op.eligible_machine_ids if mid not in all_machines]
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid machines for operation '{op.operation_name}': {invalid}.",
                )

    job_data = payload.model_dump(exclude={"operations"})
    if product_obj:
        if not job_data.get("product_id"):
            job_data["product_id"] = product_obj.product_id
        if not job_data.get("product_name"):
            job_data["product_name"] = product_obj.name

    job = Job(**job_data)
    db.add(job)
    db.flush()

    for op in ops_data:
        op_obj = Operation(
            operation_id=_gen_op_id(payload.job_id, op.sequence_number),
            job_id=payload.job_id,
            **op.model_dump(),
        )
        db.add(op_obj)

    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    return j


@router.get("/{job_id}/details")
def get_job_full_details(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns rich order details, production routing status, live schedule mapping,
    progress %, and reassignment history.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")

    # Get product if linked
    product = None
    if job.product_id:
        product = db.query(Product).filter(Product.product_id == job.product_id).first()
    elif job.product_name:
        product = db.query(Product).filter(Product.name == job.product_name).first()

    # Active & baseline schedule operations
    active_sched = (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )
    superseded_sched = (
        db.query(Schedule)
        .filter(Schedule.status == "superseded")
        .order_by(Schedule.id.desc())
        .first()
    )

    active_ops_map = {}
    if active_sched:
        for sop in active_sched.operations:
            if sop.job_id == job_id:
                active_ops_map[sop.operation_id] = sop

    superseded_ops_map = {}
    if superseded_sched:
        for sop in superseded_sched.operations:
            if sop.job_id == job_id:
                superseded_ops_map[sop.operation_id] = sop

    # Machine metadata lookup
    machines = {m.machine_id: m for m in db.query(Machine).all()}

    # Compute operations timeline
    sorted_ops = sorted(job.operations, key=lambda x: x.sequence_number)
    total_ops = len(sorted_ops)
    completed_count = 0
    running_count = 0
    pending_count = 0

    route_timeline = []
    latest_end_hours = 0.0

    for op in sorted_ops:
        sop = active_ops_map.get(op.operation_id)
        prev_sop = superseded_ops_map.get(op.operation_id)

        # Status
        actual_status = op.status
        assigned_machine = sop.machine_id if sop else (op.eligible_machine_ids[0] if op.eligible_machine_ids else "None")
        planned_start = sop.start_time if sop else None
        planned_end = sop.end_time if sop else None

        if planned_end and planned_end > latest_end_hours:
            latest_end_hours = planned_end

        is_reassigned = bool(prev_sop and sop and prev_sop.machine_id != sop.machine_id)
        previous_machine = prev_sop.machine_id if is_reassigned else None

        if actual_status == "Completed":
            completed_count += 1
            display_status = "Completed"
        elif actual_status in ["Ongoing", "Running"] or (sop and sop.status in ["Ongoing", "Running"]):
            running_count += 1
            display_status = "Running"
        elif is_reassigned:
            pending_count += 1
            display_status = "Reassigned"
        elif sop:
            pending_count += 1
            display_status = sop.status
        else:
            pending_count += 1
            display_status = "Waiting"

        machine_name = machines.get(assigned_machine).name if assigned_machine in machines else assigned_machine

        route_timeline.append({
            "operation_id": op.operation_id,
            "operation_name": op.operation_name,
            "sequence_number": op.sequence_number,
            "processing_time": op.processing_time,
            "duration_basis": getattr(op, "duration_basis", "fixed") or "fixed",
            "eligible_machine_ids": op.eligible_machine_ids,
            "assigned_machine": assigned_machine,
            "assigned_machine_name": machine_name,
            "previous_machine": previous_machine,
            "is_reassigned": is_reassigned,
            "planned_start": planned_start,
            "planned_end": planned_end,
            "status": display_status,
            "required_material_id": op.required_material_id,
            "required_material_qty": op.required_material_qty,
        })

    # Overall progress calculation
    progress_pct = 0
    if total_ops > 0:
        progress_pct = round(((completed_count + 0.5 * running_count) / total_ops) * 100)

    # Next scheduled machine
    next_machine = None
    for item in route_timeline:
        if item["status"] in ["Running", "Scheduled", "Waiting", "Reassigned"]:
            next_machine = item["assigned_machine"]
            break

    # Risk evaluation
    risk_status = "On Track"
    if job.status == "Delayed":
        risk_status = "Delayed"
    elif route_timeline and any(item["is_reassigned"] for item in route_timeline):
        risk_status = "Recovered / Reassigned"

    return {
        "job_id": job.job_id,
        "customer_name": job.customer_name,
        "product_id": job.product_id,
        "product_name": job.product_name,
        "product_category": product.category if product else "General",
        "product_description": product.description if product else None,
        "quantity": job.quantity,
        "priority": job.priority,
        "order_date": job.order_date,
        "deadline": job.deadline,
        "status": job.status,
        "is_rush_order": job.is_rush_order,
        "risk_status": risk_status,
        "progress_pct": progress_pct,
        "total_operations": total_ops,
        "completed_operations": completed_count,
        "running_operations": running_count,
        "pending_operations": pending_count,
        "next_machine": next_machine,
        "expected_completion_hours": latest_end_hours if latest_end_hours > 0 else None,
        "routing_operations": route_timeline,
    }


@router.put("/{job_id}", response_model=JobRead)
def update_job(job_id: str, payload: JobUpdate, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(j, field, value)
    db.commit()
    db.refresh(j)
    return j


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    # Clean up associated schedule operations across all schedules
    db.query(ScheduleOperation).filter(ScheduleOperation.job_id == job_id).delete()
    db.delete(j)
    db.commit()


@router.get("/{job_id}/operations", response_model=List[OperationRead])
def list_operations(job_id: str, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    return j.operations
