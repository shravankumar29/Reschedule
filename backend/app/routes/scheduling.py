"""FastAPI router – Schedule generation and retrieval."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.disruption import Disruption
from ..models.machine import Machine
from ..models.schedule import Schedule
from ..schemas.schedule import RescheduleRequest, ScheduleApproveRequest, ScheduleRead
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

