"""
Unit tests for Manual Schedule Editor and Operation Modification APIs.
Verifies all 5 scenarios (A through E), proposal drafting, validation, and approval.
"""
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.database import Base
from backend.app.models.disruption import Disruption
from backend.app.models.job import Job, Operation
from backend.app.models.machine import Machine
from backend.app.models.schedule import Schedule, ScheduleOperation
from backend.app.schemas.schedule import (
    DraftProposalRequest,
    OperationUpdateRequest,
    ScheduleApproveRequest,
)
from backend.app.routes.scheduling import (
    create_draft_proposal,
    get_eligible_machines_for_op,
    update_proposal_operation,
    discard_proposal,
    approve_schedule,
)


@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSession()
    try:
        # 1. Setup Machines
        m1 = Machine(
            machine_id="CNC-1",
            name="CNC Turning Cell 1",
            machine_type="CNC Turning",
            supported_operations=["Turning", "Roughing", "Threading"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
        )
        m2 = Machine(
            machine_id="CNC-2",
            name="CNC Turning Cell 2",
            machine_type="CNC Turning",
            supported_operations=["Turning", "Roughing"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
        )
        m3 = Machine(
            machine_id="MILL-1",
            name="Vertical Machining Center",
            machine_type="Milling",
            supported_operations=["Milling", "Drilling"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
        )
        db.add_all([m1, m2, m3])

        # 2. Setup Job & Operations
        job = Job(
            job_id="J-101",
            customer_name="AeroPrecision",
            product_name="Turbine Spindle",
            quantity=50,
            priority="High",
            order_date="2026-11-07",
            deadline="2026-11-10",
            status="In Production",
        )
        db.add(job)

        op1 = Operation(
            operation_id="J-101-OP1",
            job_id="J-101",
            operation_name="Turning",
            processing_time=3.0,
            eligible_machine_ids=["CNC-1", "CNC-2"],
            sequence_number=1,
            status="Scheduled",
        )
        op2 = Operation(
            operation_id="J-101-OP2",
            job_id="J-101",
            operation_name="Milling",
            processing_time=4.0,
            eligible_machine_ids=["MILL-1"],
            sequence_number=2,
            status="Scheduled",
        )
        db.add_all([op1, op2])

        # 3. Setup Active Schedule
        sched = Schedule(
            schedule_id="SCH-ACTIVE-001",
            created_at=datetime.now(timezone.utc).isoformat(),
            schedule_type="initial",
            status="active",
            makespan_hours=7.0,
            total_jobs=1,
            on_time_count=1,
            delayed_count=0,
            solver_status="OPTIMAL",
        )
        db.add(sched)
        db.flush()

        sop1 = ScheduleOperation(
            schedule_id="SCH-ACTIVE-001",
            job_id="J-101",
            operation_id="J-101-OP1",
            machine_id="CNC-1",
            start_time=0.0,
            end_time=3.0,
            duration=3.0,
            date="2026-11-07",
            end_date="2026-11-07",
            status="Scheduled",
            frozen=False,
        )
        sop2 = ScheduleOperation(
            schedule_id="SCH-ACTIVE-001",
            job_id="J-101",
            operation_id="J-101-OP2",
            machine_id="MILL-1",
            start_time=3.0,
            end_time=7.0,
            duration=4.0,
            date="2026-11-07",
            end_date="2026-11-07",
            status="Scheduled",
            frozen=False,
        )
        db.add_all([sop1, sop2])
        db.commit()

        yield db
    finally:
        db.close()


def test_draft_proposal_creation(db_session: Session):
    """Verify that a draft proposal is created without altering the active schedule."""
    result = create_draft_proposal(db=db_session)
    proposal_id = result["schedule_id"]
    assert proposal_id.startswith("SCH-MANUAL-")
    assert len(result["operations"]) == 2

    # Check database state
    active = db_session.query(Schedule).filter(Schedule.status == "active").first()
    assert active.schedule_id == "SCH-ACTIVE-001"
    proposal = db_session.query(Schedule).filter(Schedule.schedule_id == proposal_id).first()
    assert proposal.status == "proposed"


def test_get_eligible_machines(db_session: Session):
    """Verify eligible machine query returns compatibility flags accurately."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    machines_for_op1 = get_eligible_machines_for_op(pid, "J-101-OP1", db=db_session)
    m_map = {m["machine_id"]: m for m in machines_for_op1}
    assert m_map["CNC-1"]["is_compatible"] is True
    assert m_map["CNC-2"]["is_compatible"] is True
    assert m_map["MILL-1"]["is_compatible"] is False
    assert "does not support" in m_map["MILL-1"]["incompatibility_reason"]


def test_scenario_d_machine_incompatibility(db_session: Session):
    """Scenario D: Reject assigning operation to an incompatible machine."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    # OP1 requires Turning (eligible: CNC-1, CNC-2). Try assigning to MILL-1.
    with pytest.raises(HTTPException) as exc:
        update_proposal_operation(
            proposal_id=pid,
            operation_id="J-101-OP1",
            payload=OperationUpdateRequest(machine_id="MILL-1", start_time=0.0, end_time=3.0),
            db=db_session,
        )
    assert exc.value.status_code == 400
    assert "Machine incompatibility" in exc.value.detail


def test_scenario_a_machine_conflict(db_session: Session):
    """Scenario A: Reject assigning operation to a machine already occupied during that time."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    # Add a second job operation on CNC-1 from 0.0 to 4.0
    sop_extra = ScheduleOperation(
        schedule_id=pid,
        job_id="J-102",
        operation_id="J-102-OP1",
        machine_id="CNC-1",
        start_time=0.0,
        end_time=4.0,
        duration=4.0,
        status="Scheduled",
        frozen=False,
    )
    db_session.add(sop_extra)
    db_session.commit()

    # Try moving OP1 on CNC-1 overlapping with J-102-OP1
    with pytest.raises(HTTPException) as exc:
        update_proposal_operation(
            proposal_id=pid,
            operation_id="J-101-OP1",
            payload=OperationUpdateRequest(machine_id="CNC-1", start_time=2.0, end_time=5.0),
            db=db_session,
        )
    assert exc.value.status_code == 400
    assert "Machine conflict" in exc.value.detail


def test_scenario_b_precedence_violation(db_session: Session):
    """Scenario B: Reject moving operation before predecessor finishes or after successor starts."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    # OP1 runs 0.0 - 3.0. Try moving OP2 (Milling) to start at 2.0 (before OP1 finishes at 3.0).
    with pytest.raises(HTTPException) as exc:
        update_proposal_operation(
            proposal_id=pid,
            operation_id="J-101-OP2",
            payload=OperationUpdateRequest(machine_id="MILL-1", start_time=2.0, end_time=6.0),
            db=db_session,
        )
    assert exc.value.status_code == 400
    assert "Precedence violation" in exc.value.detail


def test_scenario_c_breakdown_downtime_overlap(db_session: Session):
    """Scenario C: Reject scheduling operation during active machine breakdown."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    # Record active breakdown on CNC-2 from 06:00 for 4 hours (0.0 to 4.0h)
    bd = Disruption(
        disruption_id="DIS-901",
        disruption_type="Machine Breakdown",
        resource="CNC-2",
        reported_at=datetime.now(timezone.utc).isoformat(),
        severity="High",
        breakdown_start="06:00",
        estimated_repair_hours=4.0,
        status="Open",
        description="Spindle bearing failure",
    )
    db_session.add(bd)
    db_session.commit()

    # Try moving OP1 to CNC-2 from 1.0h to 4.0h (overlaps breakdown 0-4h)
    with pytest.raises(HTTPException) as exc:
        update_proposal_operation(
            proposal_id=pid,
            operation_id="J-101-OP1",
            payload=OperationUpdateRequest(machine_id="CNC-2", start_time=1.0, end_time=4.0),
            db=db_session,
        )
    assert exc.value.status_code == 400
    assert "Machine unavailable" in exc.value.detail


def test_scenario_e_valid_modification_and_approval(db_session: Session):
    """Scenario E: Valid edit succeeds, updates metrics, and can be approved into active schedule."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    # OP1 is eligible for CNC-1 and CNC-2. Move to CNC-2 at 0.0h–3.0h (CNC-2 is free).
    res = update_proposal_operation(
        proposal_id=pid,
        operation_id="J-101-OP1",
        payload=OperationUpdateRequest(machine_id="CNC-2", start_time=0.0, end_time=3.0),
        db=db_session,
    )
    assert res["success"] is True
    assert res["operation"]["machine_id"] == "CNC-2"
    assert res["has_changes"] is True
    assert res["changes_count"] == 1
    assert res["reassigned_count"] == 1

    # Verify active baseline is STILL SCH-ACTIVE-001 (CNC-1)
    active_before = db_session.query(Schedule).filter(Schedule.status == "active").first()
    assert active_before.schedule_id == "SCH-ACTIVE-001"
    op_active = [o for o in active_before.operations if o.operation_id == "J-101-OP1"][0]
    assert op_active.machine_id == "CNC-1"

    # Now approve the proposal
    appr_res = approve_schedule(ScheduleApproveRequest(schedule_id=pid), db=db_session)
    assert appr_res["status"] == "active"
    assert appr_res["schedule_id"] == pid

    # Check that previous active is superseded and new proposal is active
    old_active = db_session.query(Schedule).filter(Schedule.schedule_id == "SCH-ACTIVE-001").first()
    assert old_active.status == "superseded"
    new_active = db_session.query(Schedule).filter(Schedule.schedule_id == pid).first()
    assert new_active.status == "active"
    new_op1 = [o for o in new_active.operations if o.operation_id == "J-101-OP1"][0]
    assert new_op1.machine_id == "CNC-2"


def test_discard_proposal(db_session: Session):
    """Verify that discarding a proposal deletes it and leaves active schedule intact."""
    draft = create_draft_proposal(db=db_session)
    pid = draft["schedule_id"]

    discard_res = discard_proposal(pid, db=db_session)
    assert discard_res["success"] is True

    # Ensure proposal is gone
    prop = db_session.query(Schedule).filter(Schedule.schedule_id == pid).first()
    assert prop is None

    # Ensure active schedule is intact
    active = db_session.query(Schedule).filter(Schedule.status == "active").first()
    assert active.schedule_id == "SCH-ACTIVE-001"
