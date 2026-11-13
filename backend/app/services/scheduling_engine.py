"""
OR-Tools CP-SAT scheduling engine.

Time is represented in integer minutes from shift start (06:00 = 0 minutes).
The horizon is 7 days × 24 h × 60 min = 10080 minutes.

Features:
  - Supports alternative eligible machines per operation via NewOptionalIntervalVar + AddExactlyOne.
  - Precedence constraints between consecutive operations of the same job.
  - No-overlap constraint on each machine (AddNoOverlap).
  - Breakdown / maintenance downtime windows participate directly in AddNoOverlap.
  - Frozen completed operations are preserved.
  - Multi-objective optimization: minimizes tardiness, makespan, and schedule change.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from ..models.disruption import Disruption
from ..models.job import Job, Operation
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from ..utils.time_utils import (
    get_breakdown_interval_minutes,
    parse_time_to_shift_minutes,
    MINS_PER_HOUR,
    SHIFT_START_HOUR,
)

logger = logging.getLogger(__name__)

HORIZON_DAYS = 14
HORIZON = HORIZON_DAYS * 24 * MINS_PER_HOUR          # 20 160 minutes
SOLVER_TIME_LIMIT = 30.0                               # seconds
PRIORITY_WEIGHT = {"Urgent": 5, "High": 3, "Medium": 2, "Low": 1}

# Weights for the objective function
W_TARDINESS = 10
W_MAKESPAN = 1
W_CHANGE = 2   # used in rescheduling to penalise deviation from original plan


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge overlapping or duplicate (start, end) intervals."""
    if not intervals:
        return []
    sorted_ivs = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_ivs[0]]
    for cur_s, cur_e in sorted_ivs[1:]:
        last_s, last_e = merged[-1]
        if cur_s <= last_e:
            merged[-1] = (last_s, max(last_e, cur_e))
        else:
            merged.append((cur_s, cur_e))
    return merged


def run_scheduling_engine(
    db: Session,
    schedule_id: str,
    schedule_type: str = "initial",
    status: str = "active",
    frozen_ops: Optional[Dict[str, Tuple[int, int, str]]] = None,
    disruption_id: Optional[str] = None,
    unavailable_machine_ids: Optional[List[str]] = None,
    custom_breakdowns: Optional[List[Dict[str, Any]]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run CP-SAT scheduling.

    Parameters
    ----------
    db               : active SQLAlchemy session
    schedule_id      : unique id for the new Schedule record
    schedule_type    : 'initial' or 'revised'
    status           : 'active', 'proposed', or 'superseded'
    frozen_ops       : {operation_id: (start_min, end_min, machine_id)}
    disruption_id    : linked disruption (rescheduling only)
    unavailable_machine_ids : machines permanently blocked for the entire horizon
    custom_breakdowns: list of dicts with {"machine_id", "start", "repair_hours"}
    options          : user optimization weights and toggles
    """
    frozen_ops = frozen_ops or {}
    unavailable_machine_ids = unavailable_machine_ids or []
    custom_breakdowns = custom_breakdowns or []
    options = options or {}

    prioritize_urgent = bool(options.get("prioritize_urgent", True))
    minimize_delay = bool(options.get("minimize_delay", True))
    minimize_idle = bool(options.get("minimize_idle", False))
    minimize_overtime = bool(options.get("minimize_overtime", False))

    w_tardiness = 200 if minimize_delay else 40
    w_makespan = 30 if minimize_overtime else 5
    w_change = 40      # Stability penalty against baseline schedule
    w_reassign = 300   # Penalty for swapping machine unless forced
    priority_weights = {
        "Urgent": 10 if prioritize_urgent else 2,
        "High": 5 if prioritize_urgent else 2,
        "Medium": 2,
        "Low": 1,
    }

    # -----------------------------------------------------------------------
    # Load data from database
    # -----------------------------------------------------------------------
    machines: List[Machine] = db.query(Machine).all()
    jobs: List[Job] = db.query(Job).filter(Job.status != "Completed").all()
    machine_map: Dict[str, Machine] = {m.machine_id: m for m in machines}

    if not jobs:
        return {
            "schedule_id": schedule_id,
            "solver_status": "NO_JOBS",
            "operations": [],
        }

    # Baseline schedule map for stability/change penalties
    baseline_ops: Dict[str, Tuple[int, str]] = {}
    if schedule_type == "revised":
        baseline_sched = (
            db.query(Schedule)
            .filter(Schedule.status == "active")
            .order_by(Schedule.id.desc())
            .first()
        )
        if baseline_sched:
            for b_op in baseline_sched.operations:
                baseline_ops[b_op.operation_id] = (
                    int(b_op.start_time * MINS_PER_HOUR),
                    b_op.machine_id,
                )

    # -----------------------------------------------------------------------
    # Build CP-SAT model
    # -----------------------------------------------------------------------
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT
    solver.parameters.num_search_workers = 4

    machine_intervals: Dict[str, List] = {m.machine_id: [] for m in machines}

    # -----------------------------------------------------------------------
    # Collect and add breakdown & maintenance downtime windows
    # -----------------------------------------------------------------------
    # 1. From Disruption table (all active breakdowns)
    active_disruptions = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Machine Breakdown",
            Disruption.status.in_(["Open", "Analyzed", "Reported", "Under Repair"]),
        )
        .all()
    )

    machine_downtime_windows: Dict[str, List[Tuple[int, int]]] = {m.machine_id: [] for m in machines}

    for d in active_disruptions:
        d_mid = d.machine_id or (d.resource.split(" · ")[0].strip() if d.resource else "")
        if d_mid in machine_downtime_windows:
            s_min, e_min = get_breakdown_interval_minutes(d.breakdown_start, d.estimated_repair_hours)
            machine_downtime_windows[d_mid].append((s_min, e_min))

    # 1b. From Disruption table (all active material delays)
    active_mat_delays = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Material Delay",
            Disruption.status.in_(["Open", "Analyzed", "Reported", "Awaiting Material"]),
        )
        .all()
    )
    material_delay_constraints: Dict[str, int] = {}
    for md in active_mat_delays:
        arr_min = parse_time_to_shift_minutes(md.expected_arrival or "15:00")
        for op_id in (md.affected_operation_ids or []):
            material_delay_constraints[op_id] = max(material_delay_constraints.get(op_id, 0), arr_min)
        for jid in (md.affected_job_ids or []):
            for job_obj in jobs:
                if job_obj.job_id == jid and job_obj.operations:
                    first_op = sorted(job_obj.operations, key=lambda x: x.sequence_number)[0]
                    material_delay_constraints[first_op.operation_id] = max(
                        material_delay_constraints.get(first_op.operation_id, 0), arr_min
                    )
        if md.material_id:
            for job_obj in jobs:
                for op_obj in job_obj.operations:
                    if getattr(op_obj, "required_material_id", None) == md.material_id:
                        material_delay_constraints[op_obj.operation_id] = max(
                            material_delay_constraints.get(op_obj.operation_id, 0), arr_min
                        )

    # 2. From machine maintenance_periods
    for machine in machines:
        for period in (machine.maintenance_periods or []):
            p_start = period.get("start")
            p_dur = period.get("repair_hours") or period.get("duration_hours")
            s_min, e_min = get_breakdown_interval_minutes(p_start, p_dur)
            machine_downtime_windows[machine.machine_id].append((s_min, e_min))

    # 3. From custom_breakdowns argument
    for cb in custom_breakdowns:
        mid = cb.get("machine_id")
        if mid in machine_downtime_windows:
            s_min, e_min = get_breakdown_interval_minutes(cb.get("start"), cb.get("repair_hours"))
            machine_downtime_windows[mid].append((s_min, e_min))

    # Add downtime intervals as fixed intervals that participate in AddNoOverlap
    for mid, windows in machine_downtime_windows.items():
        merged_windows = merge_intervals(windows)
        for idx, (s_min, e_min) in enumerate(merged_windows):
            dur = e_min - s_min
            if dur > 0 and mid in machine_intervals:
                clamped_s = max(0, min(HORIZON - 1, s_min))
                clamped_e = max(clamped_s + 1, min(HORIZON, e_min))
                clamped_dur = clamped_e - clamped_s
                downtime_iv = model.NewIntervalVar(
                    clamped_s, clamped_dur, clamped_e, f"downtime_{mid}_{idx}_{clamped_s}"
                )
                machine_intervals[mid].append(downtime_iv)
                logger.info(
                    "Added downtime window on %s: [%d min, %d min] (%.1fh - %.1fh)",
                    mid, clamped_s, clamped_e, clamped_s / MINS_PER_HOUR, clamped_e / MINS_PER_HOUR,
                )

    # 4. Permanently decommissioned machines (if any)
    for mid in unavailable_machine_ids:
        if mid in machine_intervals:
            block_iv = model.NewIntervalVar(0, HORIZON, HORIZON, f"block_full_{mid}")
            machine_intervals[mid].append(block_iv)

    # -----------------------------------------------------------------------
    # Decision variables
    # -----------------------------------------------------------------------
    op_vars: Dict[str, Dict] = {}
    tardiness_terms: List = []
    makespan_terms: List = []
    change_terms: List = []
    all_ends: List = []

    # Determine base anchor date from earliest order_date
    valid_dates = []
    for j in jobs:
        try:
            valid_dates.append(datetime.fromisoformat(str(j.order_date).split("T")[0]).date())
        except Exception:
            pass
    base_d = min(valid_dates) if valid_dates else datetime(2026, 11, 7).date()

    for job in jobs:
        # Calculate release time (order_date) in minutes from base anchor
        try:
            order_d = datetime.fromisoformat(str(job.order_date).split("T")[0]).date()
            diff_days = (order_d - base_d).days
            release_min = max(0, diff_days * 24 * MINS_PER_HOUR)
        except Exception:
            release_min = 0

        # Calculate deadline in minutes from shift start
        try:
            d_d = datetime.fromisoformat(str(job.deadline).split("T")[0]).date()
            diff_days = (d_d - base_d).days
            deadline_min = max(release_min + 60, diff_days * 24 * MINS_PER_HOUR + 16 * MINS_PER_HOUR)
        except Exception:
            deadline_min = HORIZON

        priority_w = PRIORITY_WEIGHT.get(job.priority, 2)
        prev_end_var = None

        for op in sorted(job.operations, key=lambda x: x.sequence_number):
            dur_min = max(1, int(op.processing_time * MINS_PER_HOUR))
            op_id = op.operation_id

            # --- Frozen (completed) operation ---
            if op_id in frozen_ops:
                f_start, f_end, f_mid = frozen_ops[op_id]
                f_iv = model.NewIntervalVar(f_start, f_end - f_start, f_end, f"frozen_{op_id}")
                machine_intervals.setdefault(f_mid, []).append(f_iv)
                op_vars[op_id] = {
                    "start": f_start,
                    "end": f_end,
                    "duration": f_end - f_start,
                    "machine_id": f_mid,
                    "frozen": True,
                    "interval": f_iv,
                }
                prev_end_var = f_end
                all_ends.append(f_end)
                continue

            # --- Eligible machines ---
            # All machines in eligible_machine_ids that exist in the factory
            # Downtime windows already block the machine during breakdown periods!
            eligible = [
                mid for mid in op.eligible_machine_ids
                if mid in machine_map and mid not in unavailable_machine_ids
            ]

            if not eligible:
                logger.warning("No eligible machine found for operation %s", op_id)
                continue

            start_var = model.NewIntVar(0, HORIZON - dur_min, f"s_{op_id}")
            end_var = model.NewIntVar(dur_min, HORIZON, f"e_{op_id}")
            model.Add(end_var == start_var + dur_min)

            # Precedence constraint: start >= previous operation end
            if isinstance(prev_end_var, int):
                model.Add(start_var >= prev_end_var)
            elif prev_end_var is not None:
                model.Add(start_var >= prev_end_var)
            elif release_min > 0:
                model.Add(start_var >= release_min)

            # Material availability constraint: cannot start before delayed material arrives
            if op_id in material_delay_constraints:
                mat_arrival_min = material_delay_constraints[op_id]
                model.Add(start_var >= mat_arrival_min)
                logger.info(
                    "Enforced material delay on %s: start >= %d min",
                    op_id,
                    mat_arrival_min,
                )

            machine_bools: Dict[str, Any] = {}
            for mid in eligible:
                b = model.NewBoolVar(f"assign_{op_id}_{mid}")
                opt_iv = model.NewOptionalIntervalVar(
                    start_var, dur_min, end_var, b, f"iv_{op_id}_{mid}"
                )
                machine_intervals[mid].append(opt_iv)
                machine_bools[mid] = b

            # Exactly one machine must be selected
            model.AddExactlyOne(machine_bools.values())

            op_vars[op_id] = {
                "start": start_var,
                "end": end_var,
                "duration": dur_min,
                "machine_id": None,
                "frozen": False,
                "bools": machine_bools,
                "job_id": job.job_id,
                "operation_id": op_id,
            }
            all_ends.append(end_var)

            # Tardiness objective
            tardiness = model.NewIntVar(0, HORIZON, f"tard_{op_id}")
            model.AddMaxEquality(tardiness, [0, end_var - deadline_min])
            is_rush = getattr(job, "is_rush_order", False) or job.priority == "Urgent"
            p_weight = 100 if is_rush else priority_weights.get(job.priority, 2)
            tardiness_terms.append(p_weight * w_tardiness * tardiness)

            # Stability / Change penalty compared to baseline schedule
            if op_id in baseline_ops:
                b_start, b_mid = baseline_ops[op_id]
                diff_var = model.NewIntVar(0, HORIZON, f"diff_{op_id}")
                model.AddAbsEquality(diff_var, start_var - b_start)
                change_terms.append(w_change * diff_var)
                # Penalize swapping to a different machine unless required
                if b_mid in machine_bools:
                    change_terms.append(w_reassign * (1 - machine_bools[b_mid]))

            prev_end_var = end_var

    # Enforce non-overlapping execution on every machine
    for mid, ivs in machine_intervals.items():
        if ivs:
            model.AddNoOverlap(ivs)

    # Makespan objective
    if all_ends:
        makespan_var = model.NewIntVar(0, HORIZON, "makespan")
        model.AddMaxEquality(makespan_var, all_ends)
        makespan_terms.append(w_makespan * makespan_var)

    # Multi-objective minimization
    objective_terms = tardiness_terms + makespan_terms + change_terms
    if objective_terms:
        model.Minimize(sum(objective_terms))

    # -----------------------------------------------------------------------
    # Solve model
    # -----------------------------------------------------------------------
    status_code = solver.Solve(model)
    wall_time_seconds = round(solver.WallTime(), 3)
    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "UNKNOWN",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
    }
    solver_status = status_map.get(status_code, "UNKNOWN")

    if solver_status not in ("OPTIMAL", "FEASIBLE"):
        logger.error("CP-SAT solver returned %s for schedule %s (wall time: %.3fs)", solver_status, schedule_id, wall_time_seconds)
        return {
            "schedule_id": schedule_id,
            "solver_status": solver_status,
            "status": "infeasible" if solver_status == "INFEASIBLE" else "failed",
            "operations": [],
            "wall_time_seconds": wall_time_seconds,
            "objective_value": None,
            "best_bound": None,
            "error": f"No feasible schedule found (solver status: {solver_status}). "
                     "Conflicting constraints: check machine eligibility, deadlines, and downtime windows.",
        }

    # -----------------------------------------------------------------------
    # Extract solution
    # -----------------------------------------------------------------------
    result_ops: List[Dict] = []
    max_end = 0

    for op_id, info in op_vars.items():
        if info.get("frozen"):
            f_s = info["start"]
            f_e = info["end"]
            day_offset = int(f_s / (24 * MINS_PER_HOUR))
            end_day_offset = int(f_e / (24 * MINS_PER_HOUR))
            op_date = (base_d + timedelta(days=day_offset)).isoformat()
            op_end_date = (base_d + timedelta(days=end_day_offset)).isoformat()
            result_ops.append({
                "operation_id": op_id,
                "job_id": _find_job_id(op_id, jobs),
                "machine_id": info["machine_id"],
                "start_time": f_s / MINS_PER_HOUR,
                "end_time": f_e / MINS_PER_HOUR,
                "duration": (f_e - f_s) / MINS_PER_HOUR,
                "date": op_date,
                "end_date": op_end_date,
                "status": "Completed",
                "frozen": True,
            })
            max_end = max(max_end, info["end"])
            continue

        if "bools" not in info:
            continue

        s = solver.Value(info["start"])
        e = solver.Value(info["end"])
        selected_mid = None
        for mid, bv in info["bools"].items():
            if solver.Value(bv):
                selected_mid = mid
                break

        max_end = max(max_end, e)
        day_offset = int(s / (24 * MINS_PER_HOUR))
        end_day_offset = int(e / (24 * MINS_PER_HOUR))
        op_date = (base_d + timedelta(days=day_offset)).isoformat()
        op_end_date = (base_d + timedelta(days=end_day_offset)).isoformat()
        result_ops.append({
            "operation_id": op_id,
            "job_id": info.get("job_id", _find_job_id(op_id, jobs)),
            "machine_id": selected_mid,
            "start_time": round(s / MINS_PER_HOUR, 2),
            "end_time": round(e / MINS_PER_HOUR, 2),
            "duration": round((e - s) / MINS_PER_HOUR, 2),
            "date": op_date,
            "end_date": op_end_date,
            "status": "Rescheduled" if schedule_type == "revised" else "Scheduled",
            "frozen": False,
        })

    makespan_hours = round(max_end / MINS_PER_HOUR, 2)

    # -----------------------------------------------------------------------
    # Persist Schedule to Database
    # -----------------------------------------------------------------------
    now_str = datetime.now(timezone.utc).isoformat()

    # Calculate on-time / delayed counts
    delayed_count = 0
    on_time_count = 0
    job_ids = list({op["job_id"] for op in result_ops})
    for jid in job_ids:
        job_ops = [op for op in result_ops if op["job_id"] == jid]
        if job_ops:
            max_job_end = max(op["end_time"] for op in job_ops)
            # 16-hour day threshold or 2 days (32 hours)
            if max_job_end <= 32.0:
                on_time_count += 1
            else:
                delayed_count += 1

    db_schedule = Schedule(
        schedule_id=schedule_id,
        created_at=now_str,
        schedule_type=schedule_type,
        status=status,
        makespan_hours=makespan_hours,
        total_jobs=len(jobs),
        on_time_count=on_time_count,
        delayed_count=delayed_count,
        disruption_id=disruption_id,
        solver_status=solver_status,
    )
    db.add(db_schedule)
    db.flush()

    for op in result_ops:
        if op["machine_id"] is None:
            continue
        db_op = ScheduleOperation(
            schedule_id=schedule_id,
            job_id=op["job_id"],
            operation_id=op["operation_id"],
            machine_id=op["machine_id"],
            start_time=op["start_time"],
            end_time=op["end_time"],
            duration=op["duration"],
            date=op.get("date"),
            end_date=op.get("end_date"),
            status=op["status"],
            frozen=op["frozen"],
        )
        db.add(db_op)

    # Only supersede existing active schedules and update machine utilization if this schedule is being activated
    if status == "active":
        db.query(Schedule).filter(
            Schedule.schedule_id != schedule_id,
            Schedule.status == "active",
        ).update({"status": "superseded"})

        machine_scheduled_hours: Dict[str, float] = {}
        for op in result_ops:
            mid = op["machine_id"]
            machine_scheduled_hours[mid] = machine_scheduled_hours.get(mid, 0.0) + op["duration"]

        for m in machines:
            total_h = machine_scheduled_hours.get(m.machine_id, 0.0)
            m.utilization = int(min(100, round((total_h / 16.0) * 100)))

    db.commit()

    logger.info(
        "[CP-SAT Run] schedule_id=%s, type=%s, status=%s, solver=%s, makespan=%.1fh, obj=%s, time=%.3fs",
        schedule_id, schedule_type, status, solver_status, makespan_hours,
        int(solver.ObjectiveValue()) if solver_status in ("OPTIMAL", "FEASIBLE") else "N/A",
        wall_time_seconds
    )

    best_bound = None
    if solver_status in ("OPTIMAL", "FEASIBLE"):
        try:
            best_bound = round(solver.BestObjectiveBound(), 2)
        except Exception:
            pass

    return {
        "schedule_id": schedule_id,
        "solver_status": solver_status,
        "status": status,
        "operations": result_ops,
        "makespan_hours": makespan_hours,
        "on_time_count": on_time_count,
        "delayed_count": delayed_count,
        "objective_value": int(solver.ObjectiveValue()) if solver_status in ("OPTIMAL", "FEASIBLE") else None,
        "best_bound": best_bound,
        "wall_time_seconds": wall_time_seconds,
        "weights_used": {
            "w_tardiness": w_tardiness,
            "w_makespan": w_makespan,
            "w_change": w_change,
            "prioritize_urgent": prioritize_urgent,
            "minimize_delay": minimize_delay,
            "minimize_idle": minimize_idle,
            "minimize_overtime": minimize_overtime,
        },
    }


def _find_job_id(op_id: str, jobs: List[Job]) -> str:
    for job in jobs:
        for op in job.operations:
            if op.operation_id == op_id:
                return job.job_id
    parts = op_id.rsplit("-OP", 1)
    return parts[0] if parts else op_id
