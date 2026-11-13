"""Service for computing data-driven manufacturing analytics and machine utilization."""
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ..models.job import Job, Operation
from ..models.machine import Machine
from ..models.schedule import Schedule, ScheduleOperation
from ..models.disruption import Disruption


def parse_date_window(
    range_type: str = "week",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ref_date_str: str = "2026-11-07",
) -> tuple[str, str, int]:
    """Parse reporting date window returning (start_date_str, end_date_str, num_days)."""
    if start_date and end_date:
        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.strptime(end_date, "%Y-%m-%d").date()
            num_days = max(1, (d_end - d_start).days + 1)
            return start_date, end_date, num_days
        except Exception:
            pass

    ref_d = datetime.strptime(ref_date_str, "%Y-%m-%d").date()

    if range_type.lower() == "today":
        return str(ref_d), str(ref_d), 1
    elif range_type.lower() == "month":
        d_start = date(ref_d.year, ref_d.month, 1)
        # End of month
        if ref_d.month == 12:
            d_end = date(ref_d.year + 1, 1, 1) - timedelta(days=1)
        else:
            d_end = date(ref_d.year, ref_d.month + 1, 1) - timedelta(days=1)
        num_days = (d_end - d_start).days + 1
        return str(d_start), str(d_end), num_days
    else:  # default "week"
        # Align to standard week: 2026-11-03 to 2026-11-09
        # Calculate diff from anchor 2026-11-03
        anchor = date(2026, 11, 3)
        diff_days = (ref_d - anchor).days
        week_idx = diff_days // 7
        d_start = anchor + timedelta(days=week_idx * 7)
        d_end = d_start + timedelta(days=6)
        return str(d_start), str(d_end), 7


def get_active_schedule(db: Session) -> Optional[Schedule]:
    """Retrieve currently active schedule from database."""
    return (
        db.query(Schedule)
        .filter(Schedule.status == "active")
        .order_by(Schedule.id.desc())
        .first()
    )


def compute_machine_utilization_data(
    db: Session,
    range_type: str = "week",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Compute exact machine-wise utilization, downtime, and operational status."""
    start_str, end_str, num_days = parse_date_window(range_type, start_date, end_date)
    machines = db.query(Machine).all()
    active_sched = get_active_schedule(db)

    # Active disruptions
    active_disruptions = (
        db.query(Disruption)
        .filter(
            Disruption.disruption_type == "Machine Breakdown",
            Disruption.status != "Resolved",
        )
        .all()
    )

    # Map disruptions to machines and sum breakdown downtime in window
    breakdowns_by_machine: Dict[str, List[Disruption]] = {}
    downtime_hours_by_machine: Dict[str, float] = {}

    for d in active_disruptions:
        mid = d.resource.split(" · ")[0].strip()
        breakdowns_by_machine.setdefault(mid, []).append(d)
        dur = float(d.estimated_repair_hours or 3.0)
        # Check if breakdown falls within the reporting window
        # Determine date of breakdown: check reported_at first, then breakdown_start if it contains a date
        dt_date = "2026-11-07"
        if d.reported_at and len(d.reported_at) >= 10 and "-" in d.reported_at[:10]:
            dt_date = d.reported_at[:10]
        elif d.breakdown_start and len(d.breakdown_start) >= 10 and "-" in d.breakdown_start[:10]:
            dt_date = d.breakdown_start[:10]

        if start_str <= dt_date <= end_str:
            downtime_hours_by_machine[mid] = downtime_hours_by_machine.get(mid, 0.0) + dur

    # Map scheduled operation hours within date window
    scheduled_hours_by_machine: Dict[str, float] = {}
    current_tasks_by_machine: Dict[str, str] = {}

    if active_sched:
        ops = (
            db.query(ScheduleOperation)
            .filter(ScheduleOperation.schedule_id == active_sched.schedule_id)
            .all()
        )
        for op in ops:
            op_start_date = op.date or "2026-11-07"
            op_end_date = op.end_date or op_start_date

            # Check date overlap with window [start_str, end_str]
            if op_start_date <= end_str and op_end_date >= start_str:
                dur = op.duration if op.duration else max(0.5, op.end_time - op.start_time)
                scheduled_hours_by_machine[op.machine_id] = (
                    scheduled_hours_by_machine.get(op.machine_id, 0.0) + dur
                )

                if op.machine_id not in current_tasks_by_machine:
                    current_tasks_by_machine[op.machine_id] = (
                        f"{op.job_id} · {op.operation_id}"
                    )

    result = []
    for m in machines:
        mid = m.machine_id
        shift_daily_hours = float((m.working_end_hour or 22) - (m.working_start_hour or 6))
        total_available_hours = round(num_days * shift_daily_hours, 1)

        breakdown_downtime = round(downtime_hours_by_machine.get(mid, 0.0), 1)
        maintenance_downtime = 0.0
        if m.maintenance_periods:
            for mp in m.maintenance_periods:
                try:
                    mp_start = mp.get("start", "")[:10]
                    if start_str <= mp_start <= end_str:
                        maintenance_downtime += float(mp.get("hours", 2.0))
                except Exception:
                    pass

        net_available_hours = max(
            0.1, total_available_hours - breakdown_downtime - maintenance_downtime
        )
        scheduled_hours = round(scheduled_hours_by_machine.get(mid, 0.0), 1)

        utilization_pct = min(
            100.0,
            round((scheduled_hours / net_available_hours) * 100.0, 1),
        )
        remaining_capacity = max(0.0, round(net_available_hours - scheduled_hours, 1))

        # Operational status
        has_breakdown = mid in breakdowns_by_machine
        if has_breakdown or not m.available:
            op_status = "Breakdown"
            task_desc = f"Offline · Breakdown ({breakdown_downtime}h downtime)"
        elif scheduled_hours > 0:
            op_status = "Running"
            task_desc = current_tasks_by_machine.get(mid, "Scheduled operations in progress")
        else:
            op_status = "Available"
            task_desc = "Available for assignment"

        result.append({
            "machine_id": mid,
            "name": m.name,
            "machine_type": m.machine_type,
            "total_available_hours": total_available_hours,
            "scheduled_hours": scheduled_hours,
            "breakdown_downtime_hours": breakdown_downtime,
            "maintenance_downtime_hours": maintenance_downtime,
            "net_available_hours": round(net_available_hours, 1),
            "remaining_capacity_hours": remaining_capacity,
            "utilization_pct": utilization_pct,
            "operational_status": op_status,
            "current_task": task_desc,
            "reporting_window": f"{start_str} to {end_str}",
        })

    return result


def compute_overview_kpis(
    db: Session,
    range_type: str = "week",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute reconciled high-integrity dashboard KPIs."""
    start_str, end_str, num_days = parse_date_window(range_type, start_date, end_date)
    jobs = db.query(Job).all()
    machines = db.query(Machine).all()
    active_sched = get_active_schedule(db)
    active_disruptions = (
        db.query(Disruption).filter(Disruption.status != "Resolved").all()
    )

    total_orders = len(jobs)
    pending_orders = sum(1 for j in jobs if j.status == "Pending")
    in_production_orders = sum(1 for j in jobs if j.status == "In Production")
    completed_orders = sum(1 for j in jobs if j.status == "Completed")
    urgent_orders = sum(1 for j in jobs if j.priority in ("High", "Urgent"))

    # Determine delayed orders from active schedule operations vs deadlines
    delayed_job_ids = set()
    if active_sched:
        ops = (
            db.query(ScheduleOperation)
            .filter(ScheduleOperation.schedule_id == active_sched.schedule_id)
            .all()
        )
        job_max_end: Dict[str, tuple[str, float]] = {}
        for op in ops:
            op_date = op.end_date or op.date or "2026-11-07"
            curr = job_max_end.get(op.job_id)
            if not curr or op_date > curr[0] or (op_date == curr[0] and op.end_time > curr[1]):
                job_max_end[op.job_id] = (op_date, op.end_time)

        for j in jobs:
            if j.status == "Delayed":
                delayed_job_ids.add(j.job_id)
            elif j.job_id in job_max_end and j.status != "Completed":
                finish_date, finish_hr = job_max_end[j.job_id]
                # Compare finish date against deadline
                if finish_date > j.deadline:
                    delayed_job_ids.add(j.job_id)
    else:
        for j in jobs:
            if j.status == "Delayed":
                delayed_job_ids.add(j.job_id)

    delayed_orders_count = len(delayed_job_ids)
    # Active orders = orders not completed and not cancelled
    active_orders_count = sum(1 for j in jobs if j.status != "Completed")

    # Machine availability:
    broken_mids = {
        d.resource.split(" · ")[0].strip()
        for d in active_disruptions
        if d.disruption_type == "Machine Breakdown"
    }
    available_machines = sum(
        1 for m in machines if m.available and m.machine_id not in broken_mids
    )
    total_machines = len(machines)

    # Machine utilization
    util_data = compute_machine_utilization_data(db, range_type, start_date, end_date)
    avg_utilization = (
        round(sum(u["utilization_pct"] for u in util_data) / max(1, len(util_data)), 1)
        if util_data
        else 0.0
    )

    on_time_pct = (
        round(((total_orders - delayed_orders_count) / max(1, total_orders)) * 100.0, 1)
        if total_orders > 0
        else 100.0
    )

    return {
        "reporting_window": f"{start_str} to {end_str}",
        "range_type": range_type,
        "total_active_orders": active_orders_count,
        "completed_orders": completed_orders,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "in_production_orders": in_production_orders,
        "delayed_orders": delayed_orders_count,
        "urgent_orders": urgent_orders,
        "total_machines": total_machines,
        "available_machines": available_machines,
        "broken_machines_count": len(broken_mids),
        "on_time_delivery_pct": on_time_pct,
        "average_scheduled_utilization_pct": avg_utilization,
        "current_makespan_hours": active_sched.makespan_hours if active_sched else None,
        "active_schedule_id": active_sched.schedule_id if active_sched else None,
        "open_disruptions_count": len(active_disruptions),
    }


def compute_production_output_chart(
    db: Session,
    range_type: str = "week",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute daily planned vs actual output based on scheduled operations and jobs."""
    start_str, end_str, num_days = parse_date_window(range_type, start_date, end_date)
    jobs = {j.job_id: j for j in db.query(Job).all()}
    active_sched = get_active_schedule(db)

    # Create daily buckets
    d_start = datetime.strptime(start_str, "%Y-%m-%d").date()
    daily_buckets: Dict[str, Dict[str, Any]] = {}

    day_abbrs = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(num_days):
        d_curr = d_start + timedelta(days=i)
        d_str = str(d_curr)
        day_abbr = day_abbrs[d_curr.weekday()]
        daily_buckets[d_str] = {
            "date": d_str,
            "day": day_abbr,
            "planned_output": 0,
            "actual_output": 0,
            "target": 1800 if d_curr.weekday() < 5 else 1400,  # 1800 weekday, 1400 weekend
            "operations_count": 0,
        }

    if active_sched:
        ops = (
            db.query(ScheduleOperation)
            .filter(ScheduleOperation.schedule_id == active_sched.schedule_id)
            .all()
        )
        for op in ops:
            op_d = op.date or "2026-11-07"
            if op_d in daily_buckets:
                job = jobs.get(op.job_id)
                # Compute fractional units for this operation
                qty = job.quantity if job else 200
                # Approximate units proportional to duration
                dur = op.duration if op.duration else 2.0
                units = int(round(qty * (dur / 8.0)))
                daily_buckets[op_d]["planned_output"] += units
                daily_buckets[op_d]["operations_count"] += 1
                if op.status == "Completed" or op.frozen:
                    daily_buckets[op_d]["actual_output"] += units

    items = list(daily_buckets.values())
    total_planned = sum(item["planned_output"] for item in items)
    total_actual = sum(item["actual_output"] for item in items)
    total_target = sum(item["target"] for item in items)

    return {
        "chart_type": "Planned vs Actual Production Output",
        "reporting_window": f"{start_str} to {end_str}",
        "total_planned_units": total_planned,
        "total_actual_units": total_actual,
        "total_target_units": total_target,
        "data": items,
    }

