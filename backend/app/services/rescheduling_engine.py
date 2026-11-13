"""
Rescheduling engine.

Wraps the core scheduling engine:
  1. Identifies the active disruption (by ID or latest active in DB).
  2. Identifies completed operations:
     - Operations that finished before breakdown start remain frozen.
     - Operations on the disrupted machine that overlap or follow the breakdown are freed for rescheduling.
  3. Ensures active disruptions generate downtime windows in the optimizer.
  4. Calls the CP-SAT scheduling engine with frozen_ops and disruption constraints.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models.disruption import Disruption
from ..models.job import Operation
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from ..utils.time_utils import get_breakdown_interval_minutes, MINS_PER_HOUR
from .scheduling_engine import run_scheduling_engine
from .impact_analyzer import get_impact_analysis
from .explanation_engine import get_explanations

logger = logging.getLogger(__name__)


def run_rescheduling(
    db: Session,
    disruption_id: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Dual-mode schedule optimization engine:
    1. Normal Schedule Optimization: optimizes active baseline without disruptions.
    2. Disruption Recovery Mode: recovers schedule with active breakdown constraints.
    Creates a 'proposed' schedule without prematurely superseding active plans.
    """
    options = options or {}
    requested_mode = options.get("mode", "auto")

    # -----------------------------------------------------------------------
    # 1. Identify target disruption(s) based on mode
    # -----------------------------------------------------------------------
    target_disruption: Optional[Disruption] = None
    broken_machine_id: Optional[str] = None
    breakdown_start_min: Optional[int] = None

    if requested_mode != "optimization":
        if disruption_id:
            target_disruption = (
                db.query(Disruption)
                .filter(Disruption.disruption_id == disruption_id)
                .first()
            )

        # Fall back to any open or analyzed disruption if not specified
        if not target_disruption and requested_mode != "optimization":
            target_disruption = (
                db.query(Disruption)
                .filter(Disruption.status.in_(["Open", "Analyzed"]))
                .order_by(Disruption.id.desc())
                .first()
            )

        if target_disruption:
            target_disruption.status = "Analyzed"
            if target_disruption.disruption_type == "Machine Breakdown" and target_disruption.resource:
                broken_machine_id = target_disruption.resource.split(" · ")[0].strip()
                s_min, _ = get_breakdown_interval_minutes(
                    target_disruption.breakdown_start, target_disruption.estimated_repair_hours
                )
                breakdown_start_min = s_min

                # Ensure machine maintenance_periods includes this breakdown
                machine = (
                    db.query(Machine)
                    .filter((Machine.machine_id == broken_machine_id) | (Machine.machine_id == target_disruption.resource))
                    .first()
                )
                if machine:
                    machine.available = False
                    machine.current_task = f"Breakdown ({target_disruption.breakdown_start or '10:00'})"
                    periods = list(machine.maintenance_periods or [])
                    if not any(p.get("start") == target_disruption.breakdown_start for p in periods):
                        periods.append({
                            "start": target_disruption.breakdown_start or "10:00",
                            "repair_hours": target_disruption.estimated_repair_hours or 3.0,
                            "reason": target_disruption.description or "Breakdown",
                        })
                        machine.maintenance_periods = periods
            db.commit()

    # -----------------------------------------------------------------------
    # 2. Identify frozen operations from the current active schedule
    # -----------------------------------------------------------------------
    active_schedule: Optional[Schedule] = (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )

    frozen_ops: Dict[str, Tuple[int, int, str]] = {}

    if active_schedule:
        for sop in active_schedule.operations:
            start_min = int(sop.start_time * MINS_PER_HOUR)
            end_min = int(sop.end_time * MINS_PER_HOUR)

            # In recovery mode: do not freeze operations on the broken machine
            if broken_machine_id and sop.machine_id == broken_machine_id:
                if breakdown_start_min is not None and end_min >= breakdown_start_min:
                    continue

            if sop.status == "Completed" or sop.frozen:
                frozen_ops[sop.operation_id] = (start_min, end_min, sop.machine_id)
                op_obj: Optional[Operation] = (
                    db.query(Operation)
                    .filter(Operation.operation_id == sop.operation_id)
                    .first()
                )
                if op_obj and op_obj.status not in ("Completed",):
                    op_obj.status = "Completed"

    # -----------------------------------------------------------------------
    # 3. Run scheduling engine with frozen ops & disruption constraints
    # -----------------------------------------------------------------------
    new_schedule_id = f"SCH-{uuid.uuid4().hex[:8].upper()}"
    active_did = target_disruption.disruption_id if target_disruption else disruption_id
    effective_mode = "recovery" if target_disruption else "optimization"

    result = run_scheduling_engine(
        db=db,
        schedule_id=new_schedule_id,
        schedule_type="revised" if active_schedule else "initial",
        status="proposed",
        frozen_ops=frozen_ops,
        disruption_id=active_did,
        options=options,
    )
    result["mode"] = effective_mode
    result["disruption_id"] = active_did
    result["frozen_count"] = len(frozen_ops)
    result["broken_machine"] = broken_machine_id

    # If solver failed or was infeasible, return early
    if result.get("solver_status") not in ("OPTIMAL", "FEASIBLE"):
        result["has_changes"] = False
        result["changes_count"] = 0
        result["changed_operations"] = []
        return result

    # -----------------------------------------------------------------------
    # 4. Compare proposed schedule with active baseline to detect changes
    # -----------------------------------------------------------------------
    active_ops_map = {
        op.operation_id: (op.machine_id, round(op.start_time, 2), round(op.end_time, 2))
        for op in (active_schedule.operations if active_schedule else [])
    }
    changed_ops = []
    reassigned_count = 0
    delayed_count = 0
    unchanged_count = 0

    for pop in result.get("operations", []):
        op_id = pop["operation_id"]
        if op_id in active_ops_map:
            orig_m, orig_s, orig_e = active_ops_map[op_id]
            is_m_changed = pop["machine_id"] != orig_m
            is_t_changed = abs(pop["start_time"] - orig_s) > 0.05
            if is_m_changed or is_t_changed:
                changed_ops.append({
                    "operation_id": op_id,
                    "original_machine": orig_m,
                    "new_machine": pop["machine_id"],
                    "original_start": orig_s,
                    "new_start": pop["start_time"],
                    "original_end": orig_e,
                    "new_end": pop["end_time"],
                    "machine_changed": is_m_changed,
                    "time_shift_hours": round(pop["start_time"] - orig_s, 2),
                })
                if is_m_changed:
                    reassigned_count += 1
                if pop["start_time"] > orig_s + 0.05:
                    delayed_count += 1
            else:
                unchanged_count += 1
        else:
            changed_ops.append({
                "operation_id": op_id,
                "original_machine": "Unassigned",
                "new_machine": pop["machine_id"],
                "original_start": 0.0,
                "new_start": pop["start_time"],
                "original_end": 0.0,
                "new_end": pop["end_time"],
                "machine_changed": True,
                "time_shift_hours": 0.0,
            })
            reassigned_count += 1

    result["has_changes"] = len(changed_ops) > 0
    result["changed_operations"] = changed_ops
    result["changes_count"] = len(changed_ops)
    result["reassigned_count"] = reassigned_count
    result["delayed_count"] = delayed_count
    result["unchanged_count"] = unchanged_count

    # Attach impact analysis and explanations
    try:
        impact_data = get_impact_analysis(db, schedule_id=new_schedule_id)
        result["impact"] = impact_data
        result["explanations"] = get_explanations(db, schedule_id=new_schedule_id)
    except Exception as e:
        logger.warning("Could not compute impact/explanations: %s", e)

    return result
