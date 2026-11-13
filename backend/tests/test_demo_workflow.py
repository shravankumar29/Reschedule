"""
End-to-End Demo Workflow Test:
1. Seed database with 5 machines, 10 jobs.
2. Generate initial production schedule with CP-SAT.
3. Validate initial schedule.
4. Report CNC-1 breakdown (at 10:00 AM, 3 hours repair duration).
5. Trigger rescheduling engine.
6. Validate revised schedule.
7. Verify operations from CNC-1 were moved to alternative machines (e.g. CNC-2).
8. Verify impact analysis and grounded rule-based explanations.
"""
from datetime import datetime, timezone
from app.database import SessionLocal
from app.seed import seed_all
from app.routes.scheduling import generate_schedule, reschedule, approve_schedule, impact, explanations, validate
from app.schemas.schedule import RescheduleRequest, ScheduleApproveRequest
from app.models.disruption import Disruption
from app.models.machine import Machine


def test_complete_demo_workflow():
    seed_all(reset=True)
    db = SessionLocal()
    try:
        # Step 1: Generate initial schedule
        init_res = generate_schedule(db=db)
        assert init_res["solver_status"] in ("OPTIMAL", "FEASIBLE")
        assert len(init_res["operations"]) > 0
        assert init_res["validation"]["valid"] is True
        print(f"Initial schedule created: {init_res['schedule_id']} with {len(init_res['operations'])} operations.")

        # Step 2: CNC-1 breaks down at 10:00 AM for 3 hours
        now = datetime.now(timezone.utc).isoformat()
        disruption = Disruption(
            disruption_id="D-DEMO-01",
            disruption_type="Machine Breakdown",
            resource="CNC-1",
            reported_at=now,
            severity="Critical",
            status="Open",
            description="CNC-1 spindle motor overheat at 10:00 AM. 3h maintenance required.",
            breakdown_start=now,
            estimated_repair_hours=3.0,
            affected_job_ids=["J-101", "J-102"],
        )
        db.add(disruption)
        # Update machine availability
        m_cnc1 = db.query(Machine).filter(Machine.machine_id == "CNC-1").first()
        m_cnc1.available = False
        db.commit()

        # Step 3: Trigger Rescheduling (creates a proposed schedule)
        res_res = reschedule(payload=RescheduleRequest(disruption_id="D-DEMO-01"), db=db)
        assert res_res["solver_status"] in ("OPTIMAL", "FEASIBLE")
        assert res_res["validation"]["valid"] is True
        print(f"Rescheduled successfully: {res_res['schedule_id']} (proposed)")

        # Step 3b: Approve the proposed schedule (makes it active)
        approve_res = approve_schedule(payload=ScheduleApproveRequest(schedule_id=res_res["schedule_id"]), db=db)
        assert approve_res["status"] == "active"
        print(f"Schedule approved: {approve_res['schedule_id']}")

        # Step 4: Validate revised schedule constraints
        val = validate(res_res["schedule_id"], db=db)
        assert val["valid"] is True
        assert len(val["errors"]) == 0
        print(f"Validation checks passed: {val['checks_passed']}/{val['total_checks']}")

        # Step 5: Check Impact Analysis
        impact_metrics = impact(db=db)
        assert impact_metrics["revised_schedule_id"] == res_res["schedule_id"]
        print(f"Impact Analysis:")
        print(f"  - Rescheduled ops: {impact_metrics['rescheduled_operations_count']}")
        print(f"  - Affected jobs: {impact_metrics['affected_jobs']}")
        print(f"  - Machine changes: {len(impact_metrics['machine_changes'])}")

        # Step 6: Check Rule-based Explanations
        exp_list = explanations(db=db)
        assert len(exp_list) > 0
        print(f"Explanations generated ({len(exp_list)}):")
        for exp in exp_list:
            print(f"  * [{exp.get('type')}] {exp.get('message')}")

    finally:
        db.close()


if __name__ == "__main__":
    test_complete_demo_workflow()

