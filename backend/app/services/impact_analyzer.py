"""
Impact analyser – compares original vs revised schedule.

All calculations are derived from actual schedule data stored in the DB.
No values are fabricated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.schedule import Schedule, ScheduleOperation
from ..models.job import Job


def _load_schedule(db: Session, schedule_id: str) -> Optional[Schedule]:
    return db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()


def _job_map(db: Session) -> Dict[str, Job]:
    return {j.job_id: j for j in db.query(Job).all()}


def get_impact_analysis(db: Session, schedule_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Compare the revised/proposed schedule against the baseline schedule.
    Returns a structured impact and optimization comparison report.
    """
    # Target revised schedule: by schedule_id if supplied, else latest proposed or active
    revised: Optional[Schedule] = None
    if schedule_id:
        revised = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if not revised:
        revised = (
            db.query(Schedule)
            .filter(Schedule.status.in_(["proposed", "active"]))
            .order_by(Schedule.id.desc())
            .first()
        )

    if not revised:
        return {"error": "No schedule found. Generate a schedule first."}

    # Baseline schedule: prior active or superseded schedule that preceded this revision
    original: Optional[Schedule] = (
        db.query(Schedule)
        .filter(
            Schedule.id < revised.id,
            Schedule.status.in_(["active", "superseded"]),
        )
        .order_by(Schedule.id.desc())
        .first()
    )

    if not original:
        # Fall back to initial schedule or self
        original = (
            db.query(Schedule)
            .filter(Schedule.schedule_type == "initial")
            .order_by(Schedule.id.desc())
            .first()
        )
    if not original:
        original = revised

    jobs = _job_map(db)
    orig_ops: Dict[str, ScheduleOperation] = {}
    if original and original.id != revised.id:
        for op in original.operations:
            orig_ops[op.operation_id] = op
    elif original and original.id == revised.id and revised.schedule_type == "revised":
        # If revised is compared to itself, no diff
        for op in original.operations:
            orig_ops[op.operation_id] = op

    rev_ops: List[ScheduleOperation] = revised.operations if revised else []

    # -----------------------------------------------------------------------
    # Compute metrics
    # -----------------------------------------------------------------------
    rescheduled_ops: List[Dict] = []
    affected_jobs: set = set()
    machine_changes: List[Dict] = []
    delayed_operations: List[Dict] = []
    unchanged_operations: List[Dict] = []

    for op in rev_ops:
        orig = orig_ops.get(op.operation_id)
        if orig and not op.frozen and original.id != revised.id:
            machine_changed = orig.machine_id != op.machine_id
            time_changed = abs(orig.start_time - op.start_time) > 0.05

            if machine_changed or time_changed:
                change_item = {
                    "operation_id": op.operation_id,
                    "job_id": op.job_id,
                    "original_machine": orig.machine_id,
                    "new_machine": op.machine_id,
                    "original_start": round(orig.start_time, 2),
                    "new_start": round(op.start_time, 2),
                    "original_end": round(orig.end_time, 2),
                    "new_end": round(op.end_time, 2),
                    "time_shift_hours": round(op.start_time - orig.start_time, 2),
                    "machine_changed": machine_changed,
                }
                rescheduled_ops.append(change_item)
                affected_jobs.add(op.job_id)

                if machine_changed:
                    machine_changes.append({
                        "operation_id": op.operation_id,
                        "job_id": op.job_id,
                        "from_machine": orig.machine_id,
                        "to_machine": op.machine_id,
                    })
                if op.start_time > orig.start_time + 0.05:
                    delayed_operations.append(change_item)
            else:
                unchanged_operations.append({
                    "operation_id": op.operation_id,
                    "job_id": op.job_id,
                    "machine_id": op.machine_id,
                    "start_time": round(op.start_time, 2),
                    "end_time": round(op.end_time, 2),
                })
        else:
            unchanged_operations.append({
                "operation_id": op.operation_id,
                "job_id": op.job_id,
                "machine_id": op.machine_id,
                "start_time": round(op.start_time, 2),
                "end_time": round(op.end_time, 2),
            })

    # Machine utilisation per machine (16-hour working shift)
    working_hours = 16.0
    machine_usage: Dict[str, float] = {}
    for op in rev_ops:
        mid = op.machine_id
        machine_usage[mid] = machine_usage.get(mid, 0.0) + (op.duration or (op.end_time - op.start_time))
    machine_utilization = {
        mid: round(min(100.0, hrs / working_hours * 100), 1)
        for mid, hrs in machine_usage.items()
    }

    orig_machine_usage: Dict[str, float] = {}
    if original:
        for op in original.operations:
            mid = op.machine_id
            orig_machine_usage[mid] = orig_machine_usage.get(mid, 0.0) + (op.duration or (op.end_time - op.start_time))
    original_machine_utilization = {
        mid: round(min(100.0, hrs / working_hours * 100), 1)
        for mid, hrs in orig_machine_usage.items()
    }

    # On-time vs delayed jobs
    delayed_jobs: List[Dict] = []
    for op in rev_ops:
        job = jobs.get(op.job_id)
        if not job:
            continue
        try:
            from datetime import datetime, timezone
            deadline_dt = datetime.fromisoformat(f"{job.deadline}T23:59:00+00:00")
            today_midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            deadline_hours = (deadline_dt - today_midnight).total_seconds() / 3600
            if op.end_time > deadline_hours:
                delay_hours = op.end_time - deadline_hours
                delayed_jobs.append({
                    "job_id": op.job_id,
                    "product_name": job.product_name,
                    "deadline": job.deadline,
                    "expected_end_hours": round(op.end_time, 2),
                    "delay_hours": round(delay_hours, 2),
                })
        except Exception:
            pass

    # Total tardiness calculation
    def calc_tardiness(ops_list: List[ScheduleOperation]) -> float:
        tot = 0.0
        from datetime import datetime, timezone
        for o in ops_list:
            job = jobs.get(o.job_id)
            if not job:
                continue
            try:
                deadline_dt = datetime.fromisoformat(f"{job.deadline}T23:59:00+00:00")
                today_midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                deadline_hours = (deadline_dt - today_midnight).total_seconds() / 3600
                if o.end_time > deadline_hours:
                    tot += (o.end_time - deadline_hours)
            except Exception:
                pass
        return round(tot, 2)

    original_tardiness = calc_tardiness(list(orig_ops.values())) if orig_ops else 0.0
    revised_tardiness = calc_tardiness(rev_ops)
    reassigned_ops_count = len(machine_changes)
    delayed_ops_count = len(delayed_operations)
    unaffected_ops_count = len(unchanged_operations)

    orig_makespan = original.makespan_hours if (original and original.id != revised.id) else revised.makespan_hours
    new_makespan = revised.makespan_hours

    return {
        "original_schedule_id": original.schedule_id if original else None,
        "revised_schedule_id": revised.schedule_id,
        "original_makespan_hours": orig_makespan,
        "revised_makespan_hours": new_makespan,
        "new_makespan_hours": new_makespan,
        "makespan_change_hours": (
            round(new_makespan - orig_makespan, 2)
            if orig_makespan and new_makespan
            else 0.0
        ),
        "original_total_tardiness_hours": original_tardiness,
        "revised_total_tardiness_hours": revised_tardiness,
        "new_total_tardiness_hours": revised_tardiness,
        "original_delayed_count": original.delayed_count if original else 0,
        "revised_delayed_count": revised.delayed_count,
        "new_delayed_count": revised.delayed_count,
        "reassigned_operations_count": reassigned_ops_count,
        "delayed_operations_count": delayed_ops_count,
        "unaffected_operations_count": unaffected_ops_count,
        "unchanged_operations_count": unaffected_ops_count,
        "total_operations": len(rev_ops),
        "rescheduled_operations_count": len(rescheduled_ops),
        "rescheduled_operations": rescheduled_ops,
        "delayed_operations": delayed_operations,
        "unchanged_operations": unchanged_operations,
        "affected_jobs": list(affected_jobs),
        "affected_jobs_count": len(affected_jobs),
        "machine_changes": machine_changes,
        "machine_utilization": machine_utilization,
        "new_scheduled_utilization": machine_utilization,
        "original_scheduled_utilization": original_machine_utilization,
        "delayed_jobs": list({d["job_id"]: d for d in delayed_jobs}.values()),
        "on_time_count": revised.on_time_count,
        "delayed_count": revised.delayed_count,
        "on_time_delivery_pct": (
            round(revised.on_time_count / revised.total_jobs * 100, 1)
            if revised.total_jobs > 0 else 0.0
        ),
        "solver_status": revised.solver_status,
    }

