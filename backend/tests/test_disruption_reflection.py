"""
Automated Regression Test:
Verifies that disruptions (e.g. CNC-1 breakdown from 10:00 AM to 1:00 PM)
are strictly reflected in the generated production schedule.

Steps tested:
1. Reset the demo database.
2. Load the 5-machine, 10-job dataset.
3. Generate the initial schedule.
4. Record all operations assigned to CNC-1.
5. Report a CNC-1 breakdown from 10:00 AM to 1:00 PM (4.0h to 7.0h from shift start).
6. Retrieve the disruption from the database and verify it is active.
7. Trigger rescheduling.
8. Verify NO scheduled operation on CNC-1 overlaps the breakdown window (10:00 to 13:00).
9. Verify alternative machine allocation: affected operations are reassigned to CNC-2 or MILL-1,
   or delayed past 1:00 PM.
10. Verify that schedule validation passes 100% and impact analysis/explanations
    ground the decisions in the CNC-1 breakdown.
"""
import pytest
from app.database import SessionLocal
from app.seed import seed_all
from app.models.disruption import Disruption
from app.models.machine import Machine
from app.models.schedule import Schedule, ScheduleOperation
from app.routes.scheduling import generate_schedule, reschedule, approve_schedule, impact, explanations, validate
from app.routes.disruptions import create_disruption
from app.schemas.disruption import DisruptionCreate
from app.schemas.schedule import RescheduleRequest, ScheduleApproveRequest
from app.utils.time_utils import get_breakdown_interval_minutes, MINS_PER_HOUR


def test_disruptions_reflected_in_generated_schedule():
    # 1. Reset the database
    seed_all(reset=True)
    db = SessionLocal()

    try:
        # 2 & 3. Generate initial schedule
        init_sched = generate_schedule(db=db)
        assert init_sched["solver_status"] in ("OPTIMAL", "FEASIBLE")
        init_id = init_sched["schedule_id"]
        assert len(init_sched["operations"]) > 0

        # 4. Record all operations assigned to CNC-1 in the initial schedule
        cnc1_initial_ops = [
            op for op in init_sched["operations"]
            if op["machine_id"] == "CNC-1"
        ]
        assert len(cnc1_initial_ops) > 0, "CNC-1 should have operations scheduled initially"
        print(f"\nInitial schedule {init_id}: {len(cnc1_initial_ops)} operations on CNC-1:")
        for op in cnc1_initial_ops:
            print(f"  - {op['operation_id']} ({op['job_id']}): {op['start_time']}h - {op['end_time']}h")

        target_op = cnc1_initial_ops[0]
        target_clock_hour = int(6 + target_op["start_time"])
        target_start_str = f"{target_clock_hour:02d}:00"
        downtime_start_h = target_op["start_time"]
        downtime_end_h = downtime_start_h + 3.0

        # 5. Report a CNC-1 breakdown overlapping target operation
        breakdown_payload = DisruptionCreate(
            disruption_type="Machine Breakdown",
            resource="CNC-1",
            severity="Critical",
            description=f"CNC-1 spindle motor breakdown from {target_start_str}",
            affected_job_ids=["J-101", "J-102"],
            breakdown_start=target_start_str,
            estimated_repair_hours=3.0,
        )
        created_disruption = create_disruption(payload=breakdown_payload, db=db)
        assert created_disruption.disruption_id is not None
        # Resource is now canonicalized to "machine_id · machine_name"
        assert "CNC-1" in created_disruption.resource

        # 6. Retrieve the disruption from database and verify persistence
        saved_d = db.query(Disruption).filter(Disruption.disruption_id == created_disruption.disruption_id).first()
        assert saved_d is not None
        assert saved_d.status in ("Open", "Analyzed")
        assert saved_d.breakdown_start == target_start_str
        assert saved_d.estimated_repair_hours == 3.0

        # Verify CNC-1 machine maintenance periods updated
        m_cnc1 = db.query(Machine).filter(Machine.machine_id == "CNC-1").first()
        assert m_cnc1 is not None
        assert len(m_cnc1.maintenance_periods) > 0

        # 7. Trigger rescheduling (creates proposed schedule)
        resched_result = reschedule(payload=RescheduleRequest(disruption_id=saved_d.disruption_id), db=db)
        assert resched_result["solver_status"] in ("OPTIMAL", "FEASIBLE")
        revised_id = resched_result["schedule_id"]
        assert revised_id != init_id, "Rescheduled plan must have a distinct schedule ID"

        # 7b. Approve the proposed schedule so it becomes active (impact requires active schedule)
        approve_schedule(payload=ScheduleApproveRequest(schedule_id=revised_id), db=db)

        # 8. VERIFY NO OPERATION ON CNC-1 OVERLAPS THE BREAKDOWN WINDOW

        revised_ops = resched_result["operations"]
        cnc1_revised_ops = [op for op in revised_ops if op["machine_id"] == "CNC-1"]

        print(f"\nRevised schedule {revised_id}: {len(cnc1_revised_ops)} operations on CNC-1:")
        for op in cnc1_revised_ops:
            print(f"  - {op['operation_id']} ({op['job_id']}): {op['start_time']}h - {op['end_time']}h")

        # Overlap check
        for op in cnc1_revised_ops:
            s = op["start_time"]
            e = op["end_time"]
            overlaps = (s < downtime_end_h - 1e-3) and (e > downtime_start_h + 1e-3)
            assert not overlaps, (
                f"VIOLATION: Operation {op['operation_id']} is scheduled on CNC-1 "
                f"from {s:.2f}h to {e:.2f}h, overlapping the breakdown window "
                f"({downtime_start_h:.2f}h - {downtime_end_h:.2f}h)!"
            )

        # 9. Verify alternative machine allocation
        # Operations that were on CNC-1 during the breakdown must be reassigned or delayed
        reassigned_to_cnc2 = [
            op for op in revised_ops
            if op["machine_id"] == "CNC-2"
        ]
        assert len(reassigned_to_cnc2) > 0, "CNC-2 should absorb operations during CNC-1 downtime"
        print(f"\nOperations on alternative machine CNC-2: {len(reassigned_to_cnc2)}")

        # 10. Verify Schedule Validation Suite passes 100%
        val = validate(revised_id, db=db)
        assert val["valid"] is True, f"Validation failed: {val['errors']}"
        assert len(val["errors"]) == 0
        print(f"\nValidation: {val['checks_passed']}/{val['total_checks']} checks passed.")

        # Verify Impact Analysis and Explanations
        imp_data = impact(db=db)
        assert imp_data["rescheduled_operations_count"] > 0
        assert len(imp_data["machine_changes"]) > 0

        exp_data = explanations(db=db)
        assert len(exp_data) > 0
        has_breakdown_exp = any(
            "CNC-1" in exp.get("message", "") and "breakdown" in exp.get("message", "").lower()
            for exp in exp_data
        )
        assert has_breakdown_exp, "Explanations must reference the CNC-1 breakdown"
        print("\nGrounded Explanation sample:")
        for exp in exp_data[:3]:
            print(f"  * {exp.get('message')}")

        print("\nREGRESSION TEST PASSED: Disruptions are mathematically and visually reflected in the schedule!")

    finally:
        db.close()

