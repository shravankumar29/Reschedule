"""FastAPI router – Schedule generation and retrieval."""
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.disruption import Disruption
from ..models.job import Job, Operation
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from ..schemas.schedule import (
    RescheduleRequest,
    ScheduleApproveRequest,
    ScheduleRead,
    DraftProposalRequest,
    OperationUpdateRequest,
    EligibleMachineRead,
    ProposalOperationEditResult,
)
from ..utils.time_utils import get_breakdown_interval_minutes, MINS_PER_HOUR
from ..services.scheduling_engine import run_scheduling_engine
from ..services.rescheduling_engine import run_rescheduling
from ..services.impact_analyzer import get_impact_analysis
from ..services.explanation_engine import get_explanations
from ..services.schedule_validator import validate_schedule

router = APIRouter(prefix="/api", tags=["scheduling"])


# ---------------------------------------------------------------------------
# Schedule generation
# ---------------------------------------------------------------------------
@router.post("/schedule/generate")
def generate_schedule(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run initial CP-SAT scheduling and persist the result."""
    schedule_id = f"SCH-{uuid.uuid4().hex[:8].upper()}"
    result = run_scheduling_engine(
        db=db,
        schedule_id=schedule_id,
        schedule_type="initial",
    )
    if result.get("solver_status") not in ("OPTIMAL", "FEASIBLE"):
        raise HTTPException(422, detail=result.get("error", "Solver failed"))
    # Validate
    validation = validate_schedule(db, schedule_id)
    result["validation"] = validation
    return result


@router.post("/reschedule")
def reschedule(payload: Optional[RescheduleRequest] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run dual-mode scheduling: normal optimization or disruption recovery using CP-SAT."""
    if payload is None:
        payload = RescheduleRequest()

    options = {
        "mode": payload.mode or "auto",
        "prioritize_urgent": payload.prioritize_urgent,
        "minimize_delay": payload.minimize_delay,
        "minimize_idle": payload.minimize_idle,
        "minimize_overtime": payload.minimize_overtime,
    }

    result = run_rescheduling(db=db, disruption_id=payload.disruption_id, options=options)
    if result.get("solver_status") == "INFEASIBLE":
        result["validation"] = {"valid": False, "errors": [result.get("error", "No feasible schedule found")]}
        return result

    if result.get("solver_status") not in ("OPTIMAL", "FEASIBLE"):
        raise HTTPException(422, detail=result.get("error", "Solver failed during scheduling"))

    # Validate
    if "schedule_id" in result and "validation" not in result:
        validation = validate_schedule(db, result["schedule_id"])
        result["validation"] = validation
    return result


# ---------------------------------------------------------------------------
# Schedule approval – marks proposed schedule as active
# ---------------------------------------------------------------------------
@router.post("/schedule/approve")
def approve_schedule(payload: ScheduleApproveRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Approve a proposed schedule: makes it active, supersedes prior active schedule,
    and resolves any linked disruption."""
    schedule = db.query(Schedule).filter(Schedule.schedule_id == payload.schedule_id).first()
    if not schedule:
        raise HTTPException(404, f"Schedule '{payload.schedule_id}' not found.")
    if schedule.status not in ("proposed", "active"):
        raise HTTPException(
            400,
            f"Schedule '{payload.schedule_id}' has status '{schedule.status}' and cannot be approved."
        )

    now_str = datetime.now(timezone.utc).isoformat()

    # Supersede prior active schedules
    db.query(Schedule).filter(
        Schedule.schedule_id != payload.schedule_id,
        Schedule.status == "active",
    ).update({"status": "superseded"})

    # Activate the proposed schedule
    schedule.status = "active"

    # Resolve the linked disruption if present
    resolved_disruption_id = None
    if schedule.disruption_id:
        disruption = (
            db.query(Disruption)
            .filter(Disruption.disruption_id == schedule.disruption_id)
            .first()
        )
        if disruption and disruption.status in ("Open", "Analyzed"):
            disruption.status = "Resolved"
            resolved_disruption_id = disruption.disruption_id

            # Restore machine availability once disruption is resolved
            if disruption.disruption_type == "Machine Breakdown" and disruption.resource:
                mid = disruption.resource.split(" · ")[0].strip()
                machine = (
                    db.query(Machine)
                    .filter((Machine.machine_id == mid) | (Machine.machine_id == disruption.resource))
                    .first()
                )
                if machine:
                    # Only restore if no other active disruptions remain on this machine
                    other_active = (
                        db.query(Disruption)
                        .filter(
                            Disruption.disruption_id != disruption.disruption_id,
                            Disruption.disruption_type == "Machine Breakdown",
                            Disruption.status.in_(["Open", "Analyzed"]),
                        )
                        .all()
                    )
                    has_other = any(
                        od.resource.split(" · ")[0].strip() == mid for od in other_active
                    )
                    if not has_other:
                        machine.available = True
                        machine.current_task = None

    # Update machine utilization for the now-active schedule
    machine_scheduled_hours: Dict[str, float] = {}
    for op in schedule.operations:
        machine_scheduled_hours[op.machine_id] = (
            machine_scheduled_hours.get(op.machine_id, 0.0) + op.duration
        )
    for m in db.query(Machine).all():
        total_h = machine_scheduled_hours.get(m.machine_id, 0.0)
        m.utilization = int(min(100, round((total_h / 16.0) * 100)))

    db.commit()

    return {
        "schedule_id": schedule.schedule_id,
        "status": "active",
        "resolved_disruption_id": resolved_disruption_id,
        "approved_at": now_str,
        "total_operations": len(schedule.operations),
        "makespan_hours": schedule.makespan_hours,
        "solver_status": schedule.solver_status,
    }


# ---------------------------------------------------------------------------
# Manual Schedule Editor – Proposals & Operation Modifications
# ---------------------------------------------------------------------------
@router.post("/schedule/proposals/draft")
def create_draft_proposal(
    payload: Optional[DraftProposalRequest] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create or load an editable proposal cloned from the active schedule without modifying baseline."""
    base_id = payload.base_schedule_id if payload else None
    base_schedule = None
    if base_id:
        base_schedule = db.query(Schedule).filter(Schedule.schedule_id == base_id).first()
    if not base_schedule:
        base_schedule = (
            db.query(Schedule)
            .filter(Schedule.status == "active")
            .order_by(Schedule.id.desc())
            .first()
        )
    if not base_schedule:
        raise HTTPException(
            404, "No baseline schedule available to create a draft from. Generate an initial schedule first."
        )

    now_str = datetime.now(timezone.utc).isoformat()
    new_schedule_id = f"SCH-MANUAL-{uuid.uuid4().hex[:6].upper()}"

    draft = Schedule(
        schedule_id=new_schedule_id,
        created_at=now_str,
        schedule_type="revised",
        status="proposed",
        makespan_hours=base_schedule.makespan_hours,
        total_jobs=base_schedule.total_jobs,
        on_time_count=base_schedule.on_time_count,
        delayed_count=base_schedule.delayed_count,
        disruption_id=base_schedule.disruption_id,
        solver_status=base_schedule.solver_status or "OPTIMAL",
    )
    db.add(draft)
    db.flush()

    for op in base_schedule.operations:
        cloned_op = ScheduleOperation(
            schedule_id=new_schedule_id,
            job_id=op.job_id,
            operation_id=op.operation_id,
            machine_id=op.machine_id,
            start_time=op.start_time,
            end_time=op.end_time,
            duration=op.duration,
            date=op.date,
            end_date=op.end_date,
            status=op.status,
            frozen=op.frozen,
        )
        db.add(cloned_op)

    db.commit()
    db.refresh(draft)

    validation = validate_schedule(db, new_schedule_id)
    impact = get_impact_analysis(db, schedule_id=new_schedule_id)

    return {
        "schedule_id": new_schedule_id,
        "solver_status": draft.solver_status,
        "mode": "optimization",
        "has_changes": False,
        "changes_count": 0,
        "reassigned_count": 0,
        "delayed_count": 0,
        "unchanged_count": len(draft.operations),
        "changed_operations": [],
        "operations": [
            {
                "id": o.id,
                "schedule_id": o.schedule_id,
                "job_id": o.job_id,
                "operation_id": o.operation_id,
                "machine_id": o.machine_id,
                "start_time": o.start_time,
                "end_time": o.end_time,
                "duration": o.duration,
                "date": o.date,
                "end_date": o.end_date,
                "status": o.status,
                "frozen": o.frozen,
            }
            for o in draft.operations
        ],
        "validation": validation,
        "impact": impact,
    }


@router.get("/schedule/proposals/{proposal_id}/eligible-machines/{operation_id}")
def get_eligible_machines_for_op(
    proposal_id: str,
    operation_id: str,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all machines in the shop with compatibility information for this operation."""
    op_def = db.query(Operation).filter(Operation.operation_id == operation_id).first()
    if not op_def:
        raise HTTPException(404, f"Operation '{operation_id}' not found.")

    machines = db.query(Machine).all()
    result = []
    for m in machines:
        is_comp = m.machine_id in (op_def.eligible_machine_ids or [])
        reason = None if is_comp else f"Machine {m.machine_id} does not support {op_def.operation_name}"
        result.append({
            "machine_id": m.machine_id,
            "name": m.name,
            "machine_type": m.machine_type,
            "available": m.available,
            "utilization": m.utilization,
            "current_task": m.current_task,
            "is_compatible": is_comp,
            "incompatibility_reason": reason,
        })
    return result


@router.put("/schedule/proposals/{proposal_id}/operations/{operation_id}")
def update_proposal_operation(
    proposal_id: str,
    operation_id: str,
    payload: OperationUpdateRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Validate and update a single scheduled operation within a draft proposal.
    Rejects conflicts with clear user-facing messages:
      - Scenario A: Machine conflict (overlapping operation on same machine)
      - Scenario B: Precedence violation (starts before predecessor or ends after successor)
      - Scenario C: Machine unavailable (overlaps breakdown or maintenance downtime)
      - Scenario D: Machine incompatibility (machine does not support operation)
    """
    # 1. Proposal check
    proposal = db.query(Schedule).filter(Schedule.schedule_id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, f"Proposal schedule '{proposal_id}' not found.")
    if proposal.status != "proposed":
        raise HTTPException(
            400,
            f"Schedule '{proposal_id}' has status '{proposal.status}'. Only proposed drafts can be manually modified.",
        )

    # 2. Operation check
    sop = (
        db.query(ScheduleOperation)
        .filter(
            ScheduleOperation.schedule_id == proposal_id,
            ScheduleOperation.operation_id == operation_id,
        )
        .first()
    )
    if not sop:
        raise HTTPException(404, f"Operation '{operation_id}' not found in proposal '{proposal_id}'.")
    if sop.frozen or sop.status == "Completed":
        raise HTTPException(400, f"Cannot modify completed or frozen operation '{operation_id}'.")

    # 3. Machine check & Eligibility (Scenario D)
    target_machine = db.query(Machine).filter(Machine.machine_id == payload.machine_id).first()
    if not target_machine:
        raise HTTPException(400, f"Target machine '{payload.machine_id}' does not exist.")

    op_def = db.query(Operation).filter(Operation.operation_id == operation_id).first()
    if op_def and payload.machine_id not in (op_def.eligible_machine_ids or []):
        eligible_str = ", ".join(op_def.eligible_machine_ids or [])
        raise HTTPException(
            400,
            f"Machine incompatibility: This machine ({payload.machine_id}) does not support the required operation ({op_def.operation_name}). Eligible machines: {eligible_str}",
        )

    # 4. Duration and time sanity checks
    if payload.start_time < 0:
        raise HTTPException(400, "Invalid start time: Start time cannot be negative.")

    if payload.end_time is not None:
        duration = round(payload.end_time - payload.start_time, 2)
        if duration <= 0:
            raise HTTPException(400, "Invalid duration: End time must be strictly after start time.")
    else:
        duration = op_def.processing_time if op_def else sop.duration
        payload.end_time = round(payload.start_time + duration, 2)

    TOLERANCE = 0.01

    # 5. Breakdown & Maintenance Downtime Check (Scenario C)
    active_breakdowns = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Machine Breakdown",
            Disruption.status.in_(["Open", "Analyzed"]),
        )
        .all()
    )
    for d in active_breakdowns:
        d_mid = d.resource.split(" · ")[0].strip() if d.resource else ""
        if d_mid == payload.machine_id:
            s_min, e_min = get_breakdown_interval_minutes(d.breakdown_start, d.estimated_repair_hours)
            bd_s = s_min / MINS_PER_HOUR
            bd_e = e_min / MINS_PER_HOUR
            if payload.start_time < bd_e - TOLERANCE and payload.end_time > bd_s + TOLERANCE:
                raise HTTPException(
                    400,
                    f"Machine unavailable: This time ({payload.start_time:.1f}h–{payload.end_time:.1f}h) overlaps with an active breakdown on {payload.machine_id} ({bd_s:.1f}h–{bd_e:.1f}h: {d.description or 'Unplanned Breakdown'}).",
                )

    for p in (target_machine.maintenance_periods or []):
        s_min, e_min = get_breakdown_interval_minutes(p.get("start"), p.get("repair_hours"))
        m_s = s_min / MINS_PER_HOUR
        m_e = e_min / MINS_PER_HOUR
        if payload.start_time < m_e - TOLERANCE and payload.end_time > m_s + TOLERANCE:
            raise HTTPException(
                400,
                f"Machine unavailable: This time ({payload.start_time:.1f}h–{payload.end_time:.1f}h) overlaps with scheduled maintenance on {payload.machine_id} ({m_s:.1f}h–{m_e:.1f}h: {p.get('reason', 'Maintenance')}).",
            )

    # 6. Machine conflict / overlap with other operations on this machine (Scenario A)
    other_ops = (
        db.query(ScheduleOperation)
        .filter(
            ScheduleOperation.schedule_id == proposal_id,
            ScheduleOperation.machine_id == payload.machine_id,
            ScheduleOperation.operation_id != operation_id,
        )
        .all()
    )
    for other in other_ops:
        if payload.start_time < other.end_time - TOLERANCE and payload.end_time > other.start_time + TOLERANCE:
            raise HTTPException(
                400,
                f"Machine conflict: {payload.machine_id} is already scheduled for another operation ({other.operation_id} from {other.start_time:.1f}h to {other.end_time:.1f}h) during this period.",
            )

    # 7. Precedence violation within Job (Scenario B)
    job = db.query(Job).filter(Job.job_id == sop.job_id).first()
    if job:
        job_sops = {
            o.operation_id: o
            for o in db.query(ScheduleOperation)
            .filter(
                ScheduleOperation.schedule_id == proposal_id,
                ScheduleOperation.job_id == sop.job_id,
            )
            .all()
        }
        sorted_job_ops = sorted(job.operations, key=lambda x: x.sequence_number)
        current_idx = next((i for i, x in enumerate(sorted_job_ops) if x.operation_id == operation_id), None)
        if current_idx is not None:
            if current_idx > 0:
                pred_op_def = sorted_job_ops[current_idx - 1]
                pred_sop = job_sops.get(pred_op_def.operation_id)
                if pred_sop and payload.start_time < pred_sop.end_time - TOLERANCE:
                    raise HTTPException(
                        400,
                        f"Precedence violation: The previous operation ({pred_sop.operation_id}) must finish (at {pred_sop.end_time:.1f}h) before this operation starts ({payload.start_time:.1f}h).",
                    )
            if current_idx < len(sorted_job_ops) - 1:
                succ_op_def = sorted_job_ops[current_idx + 1]
                succ_sop = job_sops.get(succ_op_def.operation_id)
                if succ_sop and payload.end_time > succ_sop.start_time + TOLERANCE:
                    raise HTTPException(
                        400,
                        f"Precedence violation: This operation ends at {payload.end_time:.1f}h, but the subsequent operation ({succ_sop.operation_id}) is scheduled to start at {succ_sop.start_time:.1f}h.",
                    )

    # 8. Apply modification
    base_d = date(2026, 11, 7)
    sop.machine_id = payload.machine_id
    sop.start_time = round(payload.start_time, 2)
    sop.end_time = round(payload.end_time, 2)
    sop.duration = round(duration, 2)
    sop.status = "Rescheduled"
    day_offset = int(payload.start_time / 24)
    end_day_offset = int(payload.end_time / 24)
    sop.date = (base_d + timedelta(days=day_offset)).isoformat()
    sop.end_date = (base_d + timedelta(days=end_day_offset)).isoformat()

    # Recalculate makespan of proposal
    all_proposal_ops = (
        db.query(ScheduleOperation)
        .filter(ScheduleOperation.schedule_id == proposal_id)
        .all()
    )
    if all_proposal_ops:
        proposal.makespan_hours = round(max(o.end_time for o in all_proposal_ops), 2)

    db.commit()
    db.refresh(sop)
    db.refresh(proposal)

    # 9. Compute changed operations and comparison against active baseline
    active_sched = (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )
    active_ops_map = {
        op.operation_id: (op.machine_id, round(op.start_time, 2), round(op.end_time, 2))
        for op in (active_sched.operations if active_sched else [])
    }
    changed_ops = []
    reassigned_count = 0
    delayed_count = 0
    unchanged_count = 0

    for pop in all_proposal_ops:
        op_id = pop.operation_id
        if op_id in active_ops_map:
            orig_m, orig_s, orig_e = active_ops_map[op_id]
            is_m_changed = pop.machine_id != orig_m
            is_t_changed = abs(pop.start_time - orig_s) > 0.05
            if is_m_changed or is_t_changed:
                changed_ops.append({
                    "operation_id": op_id,
                    "original_machine": orig_m,
                    "new_machine": pop.machine_id,
                    "original_start": orig_s,
                    "new_start": pop.start_time,
                    "original_end": orig_e,
                    "new_end": pop.end_time,
                    "machine_changed": is_m_changed,
                    "time_shift_hours": round(pop.start_time - orig_s, 2),
                })
                if is_m_changed:
                    reassigned_count += 1
                if pop.start_time > orig_s + 0.05:
                    delayed_count += 1
            else:
                unchanged_count += 1
        else:
            changed_ops.append({
                "operation_id": op_id,
                "original_machine": "Unassigned",
                "new_machine": pop.machine_id,
                "original_start": 0.0,
                "new_start": pop.start_time,
                "original_end": 0.0,
                "new_end": pop.end_time,
                "machine_changed": True,
                "time_shift_hours": 0.0,
            })
            reassigned_count += 1

    validation = validate_schedule(db, proposal_id)
    impact = get_impact_analysis(db, schedule_id=proposal_id)

    return {
        "success": True,
        "message": f"Operation '{operation_id}' successfully updated to {payload.machine_id} ({payload.start_time:.1f}h–{payload.end_time:.1f}h).",
        "schedule_id": proposal_id,
        "has_changes": len(changed_ops) > 0,
        "changes_count": len(changed_ops),
        "reassigned_count": reassigned_count,
        "delayed_count": delayed_count,
        "unchanged_count": unchanged_count,
        "changed_operations": changed_ops,
        "operation": {
            "id": sop.id,
            "schedule_id": sop.schedule_id,
            "job_id": sop.job_id,
            "operation_id": sop.operation_id,
            "machine_id": sop.machine_id,
            "start_time": sop.start_time,
            "end_time": sop.end_time,
            "duration": sop.duration,
            "date": sop.date,
            "end_date": sop.end_date,
            "status": sop.status,
            "frozen": sop.frozen,
        },
        "operations": [
            {
                "id": o.id,
                "schedule_id": o.schedule_id,
                "job_id": o.job_id,
                "operation_id": o.operation_id,
                "machine_id": o.machine_id,
                "start_time": o.start_time,
                "end_time": o.end_time,
                "duration": o.duration,
                "date": o.date,
                "end_date": o.end_date,
                "status": o.status,
                "frozen": o.frozen,
            }
            for o in all_proposal_ops
        ],
        "validation": validation,
        "impact": impact,
    }


@router.delete("/schedule/proposals/{proposal_id}/discard")
def discard_proposal(proposal_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Discard a draft proposal without affecting the active baseline schedule."""
    proposal = db.query(Schedule).filter(Schedule.schedule_id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, f"Proposal '{proposal_id}' not found.")
    if proposal.status != "proposed":
        raise HTTPException(
            400,
            f"Cannot discard schedule with status '{proposal.status}'. Only proposed drafts can be discarded.",
        )

    db.delete(proposal)
    db.commit()
    return {"success": True, "message": f"Proposal '{proposal_id}' discarded successfully."}


@router.post("/schedule/proposals/{proposal_id}/validate")
def validate_proposal(proposal_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Validate all hard constraints on a proposal schedule."""
    return validate_schedule(db, proposal_id)


# ---------------------------------------------------------------------------
# Schedule retrieval
# ---------------------------------------------------------------------------
@router.get("/schedule/current", response_model=ScheduleRead)
def get_current_schedule(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    s = (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )
    if not s:
        raise HTTPException(404, "No active schedule. Run /api/schedule/generate first.")

    if start_date and end_date:
        filtered_ops = [
            op for op in s.operations
            if (op.date or "2026-11-07") <= end_date and (op.end_date or op.date or "2026-11-07") >= start_date
        ]
        return ScheduleRead(
            id=s.id,
            schedule_id=s.schedule_id,
            created_at=s.created_at,
            schedule_type=s.schedule_type,
            status=s.status,
            makespan_hours=s.makespan_hours,
            total_jobs=s.total_jobs,
            on_time_count=s.on_time_count,
            delayed_count=s.delayed_count,
            disruption_id=s.disruption_id,
            solver_status=s.solver_status,
            operations=filtered_ops,
        )
    return s


@router.get("/schedule/history", response_model=List[ScheduleRead])
def get_schedule_history(db: Session = Depends(get_db)):
    return db.query(Schedule).order_by(Schedule.id.desc()).all()


@router.get("/schedule/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    s = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if not s:
        raise HTTPException(404, "Schedule not found")
    return s


# ---------------------------------------------------------------------------
# Impact analysis and explanations
# ---------------------------------------------------------------------------
@router.get("/reschedule/impact")
def impact(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return get_impact_analysis(db)


@router.get("/reschedule/explanations")
def explanations(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return get_explanations(db)


@router.get("/schedule/{schedule_id}/validate")
def validate(schedule_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return validate_schedule(db, schedule_id)

