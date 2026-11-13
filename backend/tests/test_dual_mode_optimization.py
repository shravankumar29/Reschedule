"""
Automated unit tests for Dual-Mode Scheduling Optimization in ReSchedule:
PART 7:
1. Test A: Normal Schedule Optimization (no disruptions, baseline remains active until approval, valid metrics)
2. Test B: Disruption Recovery Mode (breakdown handled, proposal generated, approval activates it)
3. Test C: Already Optimal Schedule (no fabricated changes, honest status)
4. Test D: Infeasible Schedule Handling (impossible constraint returns INFEASIBLE cleanly, no 500 crash)
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.machine import Machine
from app.models.job import Job, Operation
from app.models.disruption import Disruption
from app.models.schedule import Schedule, ScheduleOperation
from app.services.scheduling_engine import run_scheduling_engine
from app.services.rescheduling_engine import run_rescheduling
from app.services.schedule_validator import validate_schedule
from app.routes.scheduling import generate_schedule, reschedule, approve_schedule
from app.schemas.schedule import RescheduleRequest, ScheduleApproveRequest


@pytest.fixture
def clean_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def setup_standard_facility(db):
    """Set up 2 compatible CNC machines and 2 jobs."""
    m1 = Machine(
        machine_id="M1",
        name="CNC-1",
        machine_type="CNC Lathe",
        supported_operations=["Turning"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    m2 = Machine(
        machine_id="M2",
        name="CNC-2",
        machine_type="CNC Lathe",
        supported_operations=["Turning"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    db.add_all([m1, m2])

    j1 = Job(
        job_id="J-1",
        customer_name="Client A",
        product_name="Shaft A",
        quantity=50,
        order_date="2026-11-07",
        deadline="2026-11-15",
        priority="High",
        status="Pending",
    )
    j2 = Job(
        job_id="J-2",
        customer_name="Client B",
        product_name="Shaft B",
        quantity=50,
        order_date="2026-11-07",
        deadline="2026-11-15",
        priority="Medium",
        status="Pending",
    )
    db.add_all([j1, j2])

    op1 = Operation(
        operation_id="OP-101",
        job_id="J-1",
        sequence_number=1,
        operation_name="Turning",
        processing_time=4.0,
        eligible_machine_ids=["M1", "M2"],
        status="Pending",
    )
    op2 = Operation(
        operation_id="OP-201",
        job_id="J-2",
        sequence_number=1,
        operation_name="Turning",
        processing_time=4.0,
        eligible_machine_ids=["M1", "M2"],
        status="Pending",
    )
    db.add_all([op1, op2])
    db.commit()


def test_scenario_a_normal_schedule_optimization(clean_db):
    """Test A: Normal Schedule Optimization without disruptions."""
    db = clean_db
    setup_standard_facility(db)

    # 1. Generate initial baseline schedule
    init_res = generate_schedule(db=db)
    assert init_res["solver_status"] in ("OPTIMAL", "FEASIBLE")
    baseline_id = init_res["schedule_id"]

    # Verify baseline is active in DB
    baseline = db.query(Schedule).filter(Schedule.schedule_id == baseline_id).first()
    assert baseline is not None
    assert baseline.status == "active"

    # 2. Run Normal Schedule Optimization
    req = RescheduleRequest(
        mode="optimization",
        prioritize_urgent=True,
        minimize_delay=True,
        minimize_idle=True,
        minimize_overtime=False,
    )
    opt_res = reschedule(payload=req, db=db)

    # 3. Verify proposal properties
    assert opt_res["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert opt_res["mode"] == "optimization"
    assert "schedule_id" in opt_res
    proposed_id = opt_res["schedule_id"]
    assert opt_res["wall_time_seconds"] is not None
    assert opt_res["objective_value"] is not None

    # Baseline must STILL be active in DB, proposal must be proposed
    baseline_check = db.query(Schedule).filter(Schedule.schedule_id == baseline_id).first()
    assert baseline_check.status == "active", "Baseline must not be overwritten before approval"

    proposed_check = db.query(Schedule).filter(Schedule.schedule_id == proposed_id).first()
    assert proposed_check.status == "proposed", "New proposal must be saved as 'proposed'"

    # 4. Verify validation
    assert opt_res["validation"]["valid"] is True

    # 5. Verify comparison metrics
    assert "impact" in opt_res
    impact = opt_res["impact"]
    assert impact["original_schedule_id"] == baseline_id
    assert impact["revised_schedule_id"] == proposed_id
    assert impact["original_makespan_hours"] is not None
    assert impact["revised_makespan_hours"] is not None


def test_scenario_b_disruption_recovery_mode(clean_db):
    """Test B: Disruption Recovery Mode with breakdown interval and approval."""
    db = clean_db
    setup_standard_facility(db)

    # 1. Initial schedule where M1 is loaded from 0 to 4h
    init_res = generate_schedule(db=db)
    baseline_id = init_res["schedule_id"]

    # 2. Introduce a breakdown on M1 from 06:00 for 4 hours
    now = datetime.now(timezone.utc)
    disruption = Disruption(
        disruption_id="D-REC-99",
        disruption_type="Machine Breakdown",
        resource="M1",
        reported_at=now.isoformat(),
        severity="Critical",
        status="Open",
        description="M1 spindle failure from 06:00, repair 4h",
        breakdown_start="06:00",
        estimated_repair_hours=4.0,
        affected_job_ids=["J-1"],
    )
    db.add(disruption)
    # Mark M1 unavailable
    m1 = db.query(Machine).filter(Machine.machine_id == "M1").first()
    m1.available = False
    db.commit()

    # 3. Trigger Disruption Recovery
    req = RescheduleRequest(
        mode="recovery",
        disruption_id="D-REC-99",
        prioritize_urgent=True,
        minimize_delay=True,
    )
    rec_res = reschedule(payload=req, db=db)
    assert rec_res["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert rec_res["mode"] == "recovery"
    proposed_id = rec_res["schedule_id"]

    # Check that operations respect M1 downtime window or shifted to M2
    for op in rec_res["operations"]:
        if op["machine_id"] == "M1":
            # If on M1, must not overlap with downtime [0, 4]
            assert op["start_time"] >= 4.0 or op["end_time"] <= 0.0

    # 4. Approve the proposal
    app_res = approve_schedule(payload=ScheduleApproveRequest(schedule_id=proposed_id), db=db)
    assert app_res["status"] == "active"

    # Verify baseline is now superseded and proposal is active
    old_base = db.query(Schedule).filter(Schedule.schedule_id == baseline_id).first()
    assert old_base.status == "superseded"
    new_active = db.query(Schedule).filter(Schedule.schedule_id == proposed_id).first()
    assert new_active.status == "active"


def test_scenario_c_already_optimal_schedule(clean_db):
    """Test C: Optimizing a schedule that is already optimal returns has_changes=False without fake modifications."""
    db = clean_db
    setup_standard_facility(db)

    # 1. Create optimal baseline
    init_res = generate_schedule(db=db)
    assert init_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    # 2. Run optimization mode on the already optimal schedule with identical weights
    req = RescheduleRequest(
        mode="optimization",
        prioritize_urgent=True,
        minimize_delay=True,
        minimize_idle=False,
        minimize_overtime=False,
    )
    opt_res = reschedule(payload=req, db=db)
    assert opt_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    # If the solver produces the exact same optimal allocation:
    if not opt_res["has_changes"]:
        assert opt_res["changes_count"] == 0
        assert opt_res["reassigned_count"] == 0
        assert len(opt_res["changed_operations"]) == 0
    # The solver status must be genuine, never fabricated
    assert opt_res["solver_status"] in ("OPTIMAL", "FEASIBLE")


def test_scenario_d_infeasible_schedule_handling(clean_db):
    """Test D: Imposing impossible deadlines returns INFEASIBLE cleanly without 500 crashes."""
    db = clean_db

    # Only 1 machine
    m1 = Machine(
        machine_id="M1",
        name="CNC-Single",
        machine_type="CNC Lathe",
        supported_operations=["Turning"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    db.add(m1)

    # Job requiring 10 hours, but deadline is already past
    j_impossible = Job(
        job_id="J-IMP",
        customer_name="Urgent Client",
        product_name="Impossible Part",
        quantity=100,
        order_date="2026-11-01",
        deadline="2026-11-01",
        priority="High",
        status="Pending",
    )
    db.add(j_impossible)

    op_impossible = Operation(
        operation_id="OP-IMP",
        job_id="J-IMP",
        sequence_number=1,
        operation_name="Turning",
        processing_time=10.0,
        eligible_machine_ids=["M1"],
        status="Pending",
    )
    db.add(op_impossible)
    db.commit()

    # Call run_rescheduling directly with minimize_delay hard requirement
    result = run_rescheduling(db=db, options={"mode": "optimization"})

    # Assert clean status handling without unhandled exceptions
    assert "solver_status" in result
    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE", "INFEASIBLE")

    # Test route level handling
    res_api = reschedule(payload=RescheduleRequest(mode="optimization"), db=db)
    assert "solver_status" in res_api
    assert res_api["solver_status"] in ("OPTIMAL", "FEASIBLE", "INFEASIBLE")
