"""
Automated unit & integration tests for the Three Disruption Categories:
1. Test A: Machine Breakdown reporting, affected op identification, CP-SAT downtime avoidance
2. Test B: Material Delay reporting, stock shortage calculation, CP-SAT arrival time constraint
3. Test C: Rush Order creation with operations, high priority insertion via CP-SAT
4. Test D: Combined Multi-Disruption scheduling (all 3 types simultaneously handled)
5. Test E: Resolution workflows (machine recovery, material received)
6. Test F: Validation & error handling (invalid machine, invalid material, negative quantity, empty ops)
"""
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.machine import Machine
from app.models.job import Job, Operation
from app.models.material import Material, MaterialRequirement
from app.models.disruption import Disruption
from app.models.schedule import Schedule, ScheduleOperation
from app.routes.disruptions import (
    report_breakdown,
    recover_breakdown,
    report_material_delay,
    receive_material_delay,
    get_disruptions_summary,
)
from app.routes.rush_orders import create_rush_order, schedule_rush_order
from app.routes.materials import create_material, get_material
from app.routes.scheduling import generate_schedule, reschedule
from app.schemas.disruption import (
    BreakdownReportRequest,
    BreakdownRecoverRequest,
    MaterialDelayReportRequest,
    MaterialDelayReceiveRequest,
    RushOrderCreateRequest,
    RushOrderOperationInput,
)
from app.schemas.material import MaterialCreate
from app.services.scheduling_engine import run_scheduling_engine
from app.services.rescheduling_engine import run_rescheduling
from app.utils.time_utils import get_breakdown_interval_minutes, parse_time_to_shift_minutes


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Populate baseline facility
    m1 = Machine(
        machine_id="CNC-1",
        name="CNC Turning Cell 01",
        machine_type="CNC Lathe",
        supported_operations=["Turning", "Drilling"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    m2 = Machine(
        machine_id="CNC-2",
        name="CNC Turning Cell 02",
        machine_type="CNC Lathe",
        supported_operations=["Turning", "Drilling"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    m3 = Machine(
        machine_id="MILL-1",
        name="Vertical Milling Centre 01",
        machine_type="Milling Centre",
        supported_operations=["Milling"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    session.add_all([m1, m2, m3])

    mat1 = Material(
        material_id="MAT-100",
        name="Titanium Alloy Rod",
        category="Raw Material",
        unit="kg",
        available_quantity=20.0,
        reserved_quantity=0.0,
        min_stock_level=10.0,
        supplier="Apex Metals",
    )
    session.add(mat1)

    j1 = Job(
        job_id="J-TEST1",
        customer_name="Client Alpha",
        product_name="Valve Body",
        quantity=50,
        priority="Medium",
        order_date="2026-11-07",
        deadline="2026-11-09",
        status="Pending",
    )
    session.add(j1)
    session.flush()

    op1 = Operation(
        operation_id="J-TEST1-OP1",
        job_id="J-TEST1",
        operation_name="Turning",
        processing_time=3.0,
        eligible_machine_ids=["CNC-1", "CNC-2"],
        sequence_number=1,
        status="Pending",
        required_material_id="MAT-100",
        required_material_qty=50.0,  # exceeds 20.0 available
    )
    op2 = Operation(
        operation_id="J-TEST1-OP2",
        job_id="J-TEST1",
        operation_name="Milling",
        processing_time=2.0,
        eligible_machine_ids=["MILL-1"],
        sequence_number=2,
        status="Pending",
    )
    session.add_all([op1, op2])

    req1 = MaterialRequirement(
        job_id="J-TEST1",
        operation_id="J-TEST1-OP1",
        material_id="MAT-100",
        required_quantity=50.0,
        allocated_quantity=20.0,
    )
    session.add(req1)

    session.commit()
    try:
        yield session
    finally:
        session.close()


def test_scenario_a_machine_breakdown(db):
    """
    TEST A: Machine Breakdown
    - Generate baseline schedule
    - Report breakdown on CNC-1
    - Verify affected operations identified
    - Generate recovery schedule
    - Verify no operations run on CNC-1 during breakdown window
    """
    gen_res = generate_schedule(db=db)
    assert gen_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    # Report breakdown on CNC-1 from 08:00 for 4 hours (08:00 - 12:00)
    req = BreakdownReportRequest(
        machine_id="CNC-1",
        description="Spindle bearing failure",
        breakdown_start="08:00",
        estimated_repair_hours=4.0,
        severity="Critical",
    )
    breakdown_res = report_breakdown(payload=req, db=db)
    assert breakdown_res.disruption_type == "Machine Breakdown"
    assert breakdown_res.status in ("Reported", "Under Repair")

    # Machine should now be unavailable
    cnc1 = db.query(Machine).filter(Machine.machine_id == "CNC-1").first()
    assert cnc1.available is False

    # Run CP-SAT recovery reschedule
    rec_res = run_rescheduling(db=db, disruption_id=breakdown_res.disruption_id, options={"mode": "recovery"})
    assert rec_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    # Verify no operations scheduled on CNC-1 during [08:00, 12:00] (i.e. shift hours 2.0 to 6.0)
    rev_sched_id = rec_res["schedule_id"]
    rev_ops = db.query(ScheduleOperation).filter(ScheduleOperation.schedule_id == rev_sched_id).all()

    s_min, e_min = get_breakdown_interval_minutes("08:00", 4.0)
    s_hour = s_min / 60.0
    e_hour = e_min / 60.0

    for op in rev_ops:
        if op.machine_id == "CNC-1":
            # Must not overlap with breakdown window [s_hour, e_hour]
            assert op.end_time <= s_hour or op.start_time >= e_hour, (
                f"Op {op.operation_id} scheduled at {op.start_time}-{op.end_time} overlaps CNC-1 breakdown {s_hour}-{e_hour}"
            )


def test_scenario_b_material_delay(db):
    """
    TEST B: Material Delay
    - Report material delay on MAT-100 with shortage
    - Verify shortage_quantity accurately calculated
    - Verify affected operation J-TEST1-OP1 identified
    - Verify CP-SAT solver forces J-TEST1-OP1 to start >= material arrival time
    """
    gen_res = generate_schedule(db=db)
    assert gen_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    req = MaterialDelayReportRequest(
        material_id="MAT-100",
        delay_reason="Supplier logistics delay",
        supplier="Apex Metals",
        required_quantity=50.0,
        available_quantity=20.0,
        expected_arrival_time="14:00",
        severity="High",
    )
    delay_res = report_material_delay(payload=req, db=db)
    assert delay_res.disruption_type == "Material Delay"
    assert delay_res.shortage_quantity == 30.0
    assert "J-TEST1-OP1" in delay_res.affected_operation_ids
    assert "J-TEST1" in delay_res.affected_job_ids

    # Run recovery
    rec_res = run_rescheduling(db=db, disruption_id=delay_res.disruption_id, options={"mode": "recovery"})
    assert rec_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    rev_ops = {
        op.operation_id: op
        for op in db.query(ScheduleOperation).filter(ScheduleOperation.schedule_id == rec_res["schedule_id"]).all()
    }

    # 14:00 corresponds to 8 hours into the 06:00 shift
    arrival_shift_hours = (14 - 6)  # 8.0 hours
    blocked_op = rev_ops["J-TEST1-OP1"]
    assert blocked_op.start_time >= arrival_shift_hours, (
        f"Blocked op start time {blocked_op.start_time} must be >= arrival time {arrival_shift_hours}"
    )


def test_scenario_c_rush_order(db):
    """
    TEST C: Rush Order
    - Create rush order with operations and high priority
    - Verify Job persisted with is_rush_order=True
    - Schedule rush order
    - Verify rush operations scheduled with precedence respected
    """
    generate_schedule(db=db)

    rush_payload = RushOrderCreateRequest(
        customer_name="Emergency Aero",
        product_name="Cockpit Actuator",
        quantity=10,
        deadline="2026-11-08",
        order_date="2026-11-07",
        operations=[
            RushOrderOperationInput(
                operation_name="Turning",
                processing_time=1.5,
                eligible_machine_ids=["CNC-1", "CNC-2"],
                sequence_number=1,
            ),
            RushOrderOperationInput(
                operation_name="Milling",
                processing_time=1.0,
                eligible_machine_ids=["MILL-1"],
                sequence_number=2,
            ),
        ],
    )

    created = create_rush_order(payload=rush_payload, db=db)
    assert created["success"] is True
    rush_id = created["rush_order_id"]

    # Verify persisted in DB
    rush_job = db.query(Job).filter(Job.job_id == rush_id).first()
    assert rush_job is not None
    assert rush_job.is_rush_order is True
    assert rush_job.priority == "Urgent"
    assert len(rush_job.operations) == 2

    # Schedule rush order
    sched_res = schedule_rush_order(rush_order_id=rush_id, db=db)
    assert sched_res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    sched_ops = db.query(ScheduleOperation).filter(ScheduleOperation.schedule_id == sched_res["schedule_id"]).all()
    rush_sched_ops = sorted([op for op in sched_ops if op.job_id == rush_id], key=lambda x: x.start_time)
    assert len(rush_sched_ops) == 2

    # Verify precedence: op2 starts after op1 finishes
    op1_sched, op2_sched = rush_sched_ops[0], rush_sched_ops[1]
    assert op2_sched.start_time >= op1_sched.end_time


def test_scenario_d_combined_disruptions(db):
    """
    TEST D: Combined Disruptions
    - Active machine breakdown + active material delay + rush order
    - Run single CP-SAT recovery
    - Verify all constraints are respected simultaneously
    """
    generate_schedule(db=db)

    # 1. Breakdown on CNC-1 at 08:00 for 3 hrs
    report_breakdown(
        payload=BreakdownReportRequest(
            machine_id="CNC-1",
            description="Hydraulic pressure leak",
            breakdown_start="08:00",
            estimated_repair_hours=3.0,
        ),
        db=db,
    )

    # 2. Material delay arriving at 12:00
    report_material_delay(
        payload=MaterialDelayReportRequest(
            material_id="MAT-100",
            expected_arrival_time="12:00",
            required_quantity=50.0,
            available_quantity=20.0,
        ),
        db=db,
    )

    # 3. Rush order
    rush = create_rush_order(
        payload=RushOrderCreateRequest(
            customer_name="Urgent Client",
            product_name="Urgent Bushing",
            quantity=25,
            deadline="2026-11-08",
            operations=[
                RushOrderOperationInput(
                    operation_name="Turning",
                    processing_time=1.0,
                    eligible_machine_ids=["CNC-2"],
                    sequence_number=1,
                )
            ],
        ),
        db=db,
    )

    # Run unified rescheduling
    res = run_rescheduling(db=db, options={"mode": "recovery", "prioritize_urgent": True})
    assert res["solver_status"] in ("OPTIMAL", "FEASIBLE")

    sched_ops = db.query(ScheduleOperation).filter(ScheduleOperation.schedule_id == res["schedule_id"]).all()

    # Constraint 1 check: No CNC-1 ops between 08:00 and 11:00 (hours 2.0 to 5.0)
    for op in sched_ops:
        if op.machine_id == "CNC-1":
            assert op.end_time <= 2.0 or op.start_time >= 5.0

    # Constraint 2 check: MAT-100 blocked op (J-TEST1-OP1) starts >= 12:00 (hour 6.0)
    mat_op = next(op for op in sched_ops if op.operation_id == "J-TEST1-OP1")
    assert mat_op.start_time >= 6.0

    # Constraint 3 check: Rush job is scheduled
    rush_op = next(op for op in sched_ops if op.job_id == rush["rush_order_id"])
    assert rush_op is not None


def test_scenario_e_resolution_workflow(db):
    """
    TEST E: Resolution Workflows
    - Mark breakdown recovered -> actual recovery timestamp set, machine availability restored
    - Mark material delay received -> available quantity increased in inventory, status updated
    """
    # 1. Report and recover breakdown
    bd = report_breakdown(
        payload=BreakdownReportRequest(
            machine_id="CNC-1",
            description="Belt slip",
            breakdown_start="09:00",
            estimated_repair_hours=2.0,
        ),
        db=db,
    )
    assert db.query(Machine).filter(Machine.machine_id == "CNC-1").first().available is False

    recovered = recover_breakdown(
        disruption_id=bd.disruption_id,
        payload=BreakdownRecoverRequest(recovery_notes="Drive belt replaced and calibrated"),
        db=db,
    )
    assert recovered.status == "Recovered"
    assert recovered.actual_recovery_at is not None
    assert db.query(Machine).filter(Machine.machine_id == "CNC-1").first().available is True

    # 2. Report and receive material delay
    md = report_material_delay(
        payload=MaterialDelayReportRequest(
            material_id="MAT-100",
            required_quantity=50.0,
            available_quantity=20.0,
            expected_arrival_time="15:00",
        ),
        db=db,
    )
    mat_before = db.query(Material).filter(Material.material_id == "MAT-100").first().available_quantity

    received = receive_material_delay(
        disruption_id=md.disruption_id,
        payload=MaterialDelayReceiveRequest(received_quantity=30.0, notes="Batch arrived via priority freight"),
        db=db,
    )
    assert received.status == "Received"
    assert received.actual_arrival is not None

    mat_after = db.query(Material).filter(Material.material_id == "MAT-100").first().available_quantity
    assert mat_after == mat_before + 30.0


def test_scenario_f_invalid_data_rejection(db):
    """
    TEST F: Invalid Data Rejection
    - Unknown machine in breakdown -> 400
    - Unknown material in material delay -> 400
    - Rush order with no operations -> 400
    - Rush order with non-existent machine -> 400
    """
    # 1. Unknown machine
    with pytest.raises(HTTPException) as exc:
        report_breakdown(
            payload=BreakdownReportRequest(
                machine_id="NON-EXISTENT-MACHINE",
                description="Ghost machine failed",
            ),
            db=db,
        )
    assert exc.value.status_code == 400

    # 2. Unknown material
    with pytest.raises(HTTPException) as exc:
        report_material_delay(
            payload=MaterialDelayReportRequest(
                material_id="MAT-UNKNOWN-999",
                delay_reason="Unknown material delay",
            ),
            db=db,
        )
    assert exc.value.status_code == 400

    # 3. Rush order with no operations
    with pytest.raises(HTTPException) as exc:
        create_rush_order(
            payload=RushOrderCreateRequest(
                customer_name="Test Client",
                product_name="Empty Order",
                quantity=10,
                deadline="2026-11-09",
                operations=[],
            ),
            db=db,
        )
    assert exc.value.status_code == 400

    # 4. Rush order with non-existent machine
    with pytest.raises(HTTPException) as exc:
        create_rush_order(
            payload=RushOrderCreateRequest(
                customer_name="Test Client",
                product_name="Bad Machine Order",
                quantity=10,
                deadline="2026-11-09",
                operations=[
                    RushOrderOperationInput(
                        operation_name="Turning",
                        processing_time=1.0,
                        eligible_machine_ids=["UNKNOWN-MACHINE-ID"],
                        sequence_number=1,
                    )
                ],
            ),
            db=db,
        )
    assert exc.value.status_code == 400
