"""
Schedule validator – verifies a schedule is internally consistent.

Checks performed:
  1. No machine processes overlapping operations.
  2. No operation starts before its predecessor ends (same job).
  3. No operation assigned to an incompatible machine.
  4. No operation overlaps a machine downtime window.
  5. No completed operation is modified vs. frozen set.
  6. Every required operation is scheduled.
  7. All processing durations match the declared values (within tolerance).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models.job import Job, Operation
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from ..models.disruption import Disruption
from ..utils.time_utils import get_breakdown_interval_minutes, MINS_PER_HOUR

logger = logging.getLogger(__name__)
TOLERANCE = 0.01  # hours


def validate_schedule(db: Session, schedule_id: str) -> Dict[str, Any]:
    schedule: Optional[Schedule] = (
        db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    )
    if not schedule:
        return {"valid": False, "errors": [f"Schedule {schedule_id} not found"]}

    errors: List[str] = []
    warnings: List[str] = []

    ops: List[ScheduleOperation] = schedule.operations
    jobs: List[Job] = db.query(Job).all()
    machines: List[Machine] = db.query(Machine).all()

    machine_map: Dict[str, Machine] = {m.machine_id: m for m in machines}
    job_map: Dict[str, Job] = {j.job_id: j for j in jobs}

    # Index ops by operation_id
    op_map: Dict[str, ScheduleOperation] = {op.operation_id: op for op in ops}

    # --- Check 1: No machine overlap ---
    machine_timelines: Dict[str, List[Tuple[float, float, str]]] = {}
    for op in ops:
        mid = op.machine_id
        if mid not in machine_timelines:
            machine_timelines[mid] = []
        machine_timelines[mid].append((op.start_time, op.end_time, op.operation_id))

    for mid, timeline in machine_timelines.items():
        sorted_tl = sorted(timeline, key=lambda x: x[0])
        for i in range(len(sorted_tl) - 1):
            if sorted_tl[i][1] > sorted_tl[i + 1][0] + TOLERANCE:
                errors.append(
                    f"OVERLAP: Machine {mid} has overlapping operations "
                    f"{sorted_tl[i][2]} (ends {sorted_tl[i][1]:.2f}h) and "
                    f"{sorted_tl[i+1][2]} (starts {sorted_tl[i+1][0]:.2f}h)"
                )

    # --- Check 2: Operation precedence within jobs ---
    for job in jobs:
        sorted_ops = sorted(job.operations, key=lambda x: x.sequence_number)
        for i in range(len(sorted_ops) - 1):
            prev_op = sorted_ops[i]
            next_op = sorted_ops[i + 1]
            prev_sched = op_map.get(prev_op.operation_id)
            next_sched = op_map.get(next_op.operation_id)
            if prev_sched and next_sched:
                if next_sched.start_time < prev_sched.end_time - TOLERANCE:
                    errors.append(
                        f"PRECEDENCE VIOLATION: Job {job.job_id}: "
                        f"op {next_op.operation_id} starts at {next_sched.start_time:.2f}h "
                        f"before op {prev_op.operation_id} ends at {prev_sched.end_time:.2f}h"
                    )

    # --- Check 3: Machine eligibility ---
    op_obj_map: Dict[str, Operation] = {}
    for job in jobs:
        for op in job.operations:
            op_obj_map[op.operation_id] = op

    for sop in ops:
        op_def = op_obj_map.get(sop.operation_id)
        if op_def and sop.machine_id not in op_def.eligible_machine_ids:
            errors.append(
                f"INELIGIBLE MACHINE: Operation {sop.operation_id} assigned to "
                f"{sop.machine_id} but eligible machines are: {op_def.eligible_machine_ids}"
            )

    # --- Check 4: Maintenance / Breakdown downtime overlap ---
    active_disruptions = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Machine Breakdown",
            Disruption.status.in_(["Open", "Analyzed"]),
        )
        .all()
    )
    machine_downtime: Dict[str, List[Tuple[float, float, str]]] = {m.machine_id: [] for m in machines}
    for d in active_disruptions:
        s_min, e_min = get_breakdown_interval_minutes(d.breakdown_start, d.estimated_repair_hours)
        s_h = s_min / MINS_PER_HOUR
        e_h = e_min / MINS_PER_HOUR
        machine_downtime.setdefault(d.resource, []).append((s_h, e_h, f"Disruption {d.disruption_id}"))

    for m in machines:
        for p in (m.maintenance_periods or []):
            s_min, e_min = get_breakdown_interval_minutes(p.get("start"), p.get("repair_hours"))
            s_h = s_min / MINS_PER_HOUR
            e_h = e_min / MINS_PER_HOUR
            machine_downtime.setdefault(m.machine_id, []).append((s_h, e_h, p.get("reason", "Maintenance")))

    for sop in ops:
        for s_h, e_h, reason in machine_downtime.get(sop.machine_id, []):
            if sop.start_time < e_h - TOLERANCE and sop.end_time > s_h + TOLERANCE:
                errors.append(
                    f"DOWNTIME OVERLAP: Operation {sop.operation_id} on {sop.machine_id} "
                    f"({sop.start_time:.2f}h–{sop.end_time:.2f}h) overlaps downtime "
                    f"({s_h:.2f}h–{e_h:.2f}h: {reason})"
                )

    # --- Check 5: Completed operations not modified ---
    for sop in ops:
        if sop.frozen and sop.status != "Completed":
            errors.append(
                f"FROZEN VIOLATION: Operation {sop.operation_id} is frozen but status is {sop.status}"
            )

    # --- Check 6: All required operations scheduled ---
    for job in jobs:
        if job.status == "Completed":
            continue
        for op in job.operations:
            if op.status not in ("Completed",) and op.operation_id not in op_map:
                warnings.append(
                    f"UNSCHEDULED: Operation {op.operation_id} (job {job.job_id}) "
                    "has no entry in the schedule"
                )

    # --- Check 7: Duration tolerance ---
    for sop in ops:
        op_def = op_obj_map.get(sop.operation_id)
        if op_def:
            expected = op_def.processing_time
            actual = sop.duration
            if abs(actual - expected) > TOLERANCE + 0.05:
                warnings.append(
                    f"DURATION MISMATCH: Op {sop.operation_id} expected {expected:.2f}h, "
                    f"got {actual:.2f}h"
                )

    return {
        "valid": len(errors) == 0,
        "schedule_id": schedule_id,
        "errors": errors,
        "warnings": warnings,
        "checks_passed": 7 - len(set([e.split(":")[0] for e in errors])),
        "total_checks": 7,
    }

