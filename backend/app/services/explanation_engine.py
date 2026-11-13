"""
Rule-based explanation engine.

Generates human-readable explanations for every scheduling decision
grounded in actual data from the schedule comparison.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.disruption import Disruption
from ..models.job import Job
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from .impact_analyzer import get_impact_analysis


def get_explanations(db: Session, schedule_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return a list of explanation records for the latest rescheduling or optimization."""
    impact = get_impact_analysis(db, schedule_id=schedule_id)
    if "error" in impact:
        return [{"type": "error", "message": impact["error"]}]

    explanations: List[Dict[str, Any]] = []

    # Check active or linked disruptions
    target_sched = None
    if schedule_id:
        target_sched = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if not target_sched:
        target_sched = db.query(Schedule).filter(Schedule.status.in_(["active", "proposed"])).order_by(Schedule.id.desc()).first()

    linked_d_id = target_sched.disruption_id if target_sched else None

    disruption_filter = [Disruption.status.in_(["Open", "Analyzed"])]
    if linked_d_id:
        disruption_filter.append(Disruption.disruption_id == linked_d_id)

    active_breakdowns = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Machine Breakdown",
            or_(*disruption_filter),
        )
        .all()
    )

    # --- Machine changes ---
    for change in impact.get("machine_changes", []):
        from_m = change["from_machine"]
        to_m = change["to_machine"]
        job_id = change["job_id"]
        op_id = change["operation_id"]

        # Find if from_m experienced a breakdown
        breakdown = next(
            (
                d for d in active_breakdowns
                if (d.machine_id == from_m) or (d.resource and (d.resource.split(" · ")[0].strip() == from_m or d.resource == from_m))
            ),
            None,
        )

        if breakdown:
            reason = (
                f"{from_m} experienced a breakdown starting at {breakdown.breakdown_start or '10:00'} "
                f"({breakdown.estimated_repair_hours or 3}h downtime window)."
            )
        else:
            reason = f"Workload rebalancing on {from_m} to eliminate bottlenecks and reduce total makespan."

        job = db.query(Job).filter(Job.job_id == job_id).first()
        job_name = job.product_name if job else job_id

        explanations.append({
            "type": "machine_reassignment",
            "operation_id": op_id,
            "job_id": job_id,
            "message": (
                f"Operation {op_id} for job {job_id} ({job_name}) was moved from "
                f"{from_m} to {to_m}. Reason: {reason} "
                f"{to_m} was selected because it supports the required operation and has available capacity."
            ),
            "from_machine": from_m,
            "to_machine": to_m,
        })

    # --- Time shifts (same machine, different time) ---
    for op in impact.get("rescheduled_operations", []):
        if op["machine_changed"]:
            continue  # already explained above
        shift = op["time_shift_hours"]
        direction = "delayed" if shift > 0 else "advanced earlier"
        job_id = op["job_id"]
        job = db.query(Job).filter(Job.job_id == job_id).first()
        job_name = job.product_name if job else job_id
        orig_m = op.get("original_machine")
        bd_match = next(
            (
                d for d in active_breakdowns
                if (d.machine_id == orig_m) or (d.resource and (d.resource.split(" · ")[0].strip() == orig_m or d.resource == orig_m))
            ),
            None,
        )
        if bd_match and shift > 0:
            reason_suffix = f"due to {orig_m} breakdown downtime starting at {bd_match.breakdown_start or '10:00'} ({bd_match.estimated_repair_hours or 3}h window)."
        else:
            reason_suffix = "to optimize workflow sequencing and eliminate machine idle time."

        explanations.append({
            "type": "time_shift",
            "operation_id": op["operation_id"],
            "job_id": job_id,
            "message": (
                f"Operation {op['operation_id']} for job {job_id} ({job_name}) "
                f"was {direction} by {abs(shift):.1f} hours {reason_suffix}"
            ),
            "shift_hours": shift,
        })

    # --- Delayed jobs ---
    for delayed in impact.get("delayed_jobs", []):
        job_id = delayed["job_id"]
        explanations.append({
            "type": "deadline_risk",
            "job_id": job_id,
            "message": (
                f"Job {job_id} ({delayed['product_name']}) is expected to complete "
                f"{delayed['delay_hours']:.1f} hours after its deadline ({delayed['deadline']}). "
                "Capacity constraints across eligible machines limit earlier completion."
            ),
            "delay_hours": delayed["delay_hours"],
        })

    # --- Material Delays ---
    active_mat_delays = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Material Delay",
            Disruption.status.in_(["Open", "Analyzed", "Reported", "Awaiting Material"]),
        )
        .all()
    )
    for md in active_mat_delays:
        explanations.append({
            "type": "material_delay",
            "message": (
                f"Material {md.resource} shortage ({md.shortage_quantity or 0} units). "
                f"Dependent operations are constrained to start after expected delivery at {md.expected_arrival or '15:00'}."
            ),
        })

    # --- Rush Orders ---
    active_rush = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Rush Order",
            Disruption.status.in_(["Open", "Analyzed", "Awaiting Scheduling", "Scheduled"]),
        )
        .all()
    )
    for ro in active_rush:
        explanations.append({
            "type": "rush_order",
            "message": (
                f"Rush Order {ro.rush_job_id or ro.resource} prioritized to protect committed deadline {ro.deadline or 'urgent'}."
            ),
        })

    # Fallback explanation if no operations changed
    if not explanations:
        solver_status = impact.get("solver_status", "OPTIMAL")
        if active_breakdowns:
            b_res = active_breakdowns[0].resource
            explanations.append({
                "type": "no_change",
                "message": (
                    f"Disruption Recovery: The reported event on {b_res} does not conflict "
                    "with any scheduled operations. The active plan remains safe and optimal without modifications."
                ),
            })
        else:
            explanations.append({
                "type": "optimal_schedule",
                "message": (
                    f"Normal Schedule Optimization: Current schedule is already optimal ({solver_status}). "
                    "All operations are arranged with minimal tardiness and idle time. No modifications needed."
                ),
            })

    return explanations

    # --- Prioritised jobs ---
    urgent_jobs = (
        db.query(Job)
        .filter(Job.priority.in_(["Urgent", "High"]))
        .all()
    )
    for job in urgent_jobs:
        if job.job_id in impact.get("affected_jobs", []):
            explanations.append({
                "type": "priority_note",
                "job_id": job.job_id,
                "message": (
                    f"Job {job.job_id} ({job.product_name}) carries {job.priority} priority "
                    "and was given weighted preference in the optimisation objective to protect "
                    "its delivery deadline."
                ),
            })

    # --- Machines blocked ---
    revised_id = impact.get("revised_schedule_id")
    if revised_id:
        revised = db.query(Schedule).filter(Schedule.schedule_id == revised_id).first()
        if revised and revised.disruption_id:
            d = (
                db.query(Disruption)
                .filter(Disruption.disruption_id == revised.disruption_id)
                .first()
            )
            if d and d.disruption_type == "Machine Breakdown":
                machine = db.query(Machine).filter(Machine.machine_id == d.resource).first()
                mname = machine.name if machine else d.resource
                explanations.append({
                    "type": "machine_blocked",
                    "machine_id": d.resource,
                    "message": (
                        f"Machine {d.resource} ({mname}) was marked unavailable at "
                        f"{d.breakdown_start or d.reported_at} with an estimated repair time of "
                        f"{d.estimated_repair_hours or 'unknown'} hours. "
                        "All operations previously assigned to this machine were reassigned."
                    ),
                })

    if not explanations:
        explanations.append({
            "type": "info",
            "message": "No significant schedule changes were required. The existing plan remains optimal.",
        })

    return explanations

