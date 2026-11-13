"""Test adding new machine and new order, and scheduling them."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.routes.machines import create_machine, list_machines, delete_machine
from app.routes.jobs import create_job, list_jobs
from app.routes.scheduling import generate_schedule
from app.schemas.machine import MachineCreate
from app.schemas.job import JobCreate, OperationCreate


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_add_machine_and_add_order(db):
    # 1. Add new machine
    new_m = MachineCreate(
        machine_id="CNC-3",
        name="High-Speed CNC Cell 03",
        machine_type="CNC Lathe",
        supported_operations=["Turning", "Milling", "Drilling"],
        working_start_hour=6,
        working_end_hour=22,
    )
    m_record = create_machine(new_m, db=db)
    assert m_record.machine_id == "CNC-3"
    assert m_record.available is True

    # Verify machine is listed
    all_machines = list_machines(db=db)
    assert any(m.machine_id == "CNC-3" for m in all_machines)

    # 2. Add new order targeting CNC-3
    new_j = JobCreate(
        job_id="J-111",
        customer_name="Precision Aero Corp",
        product_name="Titanium Turbine Flange",
        quantity=120,
        priority="High",
        order_date="2026-11-07",
        deadline="2026-11-12",
        operations=[
            OperationCreate(
                operation_name="Titanium Turning",
                processing_time=3.5,
                eligible_machine_ids=["CNC-3"],
                sequence_number=1,
            )
        ],
    )
    j_record = create_job(new_j, db=db)
    assert j_record.job_id == "J-111"

    # Verify job is listed
    all_jobs = list_jobs(db=db)
    assert any(j.job_id == "J-111" for j in all_jobs)

    # 3. Generate schedule and verify J-111 is scheduled on CNC-3
    sched = generate_schedule(db=db)
    assert sched["solver_status"] in ["OPTIMAL", "FEASIBLE"]
    assert len(sched["operations"]) == 1
    op = sched["operations"][0]
    assert op["job_id"] == "J-111"
    assert op["machine_id"] == "CNC-3"


def test_delete_machine_workflow(db):
    from fastapi import HTTPException

    # 1. Add an idle machine
    create_machine(
        MachineCreate(
            machine_id="TEMP-01",
            name="Temporary Laser",
            machine_type="Fiber Laser",
            supported_operations=["Laser Cutting"],
        ),
        db=db,
    )
    assert any(m.machine_id == "TEMP-01" for m in list_machines(db=db))

    # 2. Successfully delete the idle machine
    delete_machine("TEMP-01", db=db)
    assert not any(m.machine_id == "TEMP-01" for m in list_machines(db=db))

    # 3. Deleting non-existent machine raises 404
    with pytest.raises(HTTPException) as exc_info_404:
        delete_machine("NON-EXISTENT", db=db)
    assert exc_info_404.value.status_code == 404

    # 4. Add a machine and assign an active operation to it
    create_machine(
        MachineCreate(
            machine_id="MCH-ACTIVE",
            name="Active Production Machine",
            machine_type="Milling Center",
            supported_operations=["Milling"],
        ),
        db=db,
    )
    create_job(
        JobCreate(
            job_id="J-ACTIVE-1",
            customer_name="Test Customer",
            product_name="Active Component",
            quantity=50,
            priority="Medium",
            order_date="2026-11-07",
            deadline="2026-11-12",
            operations=[
                OperationCreate(
                    operation_name="Milling",
                    processing_time=2.0,
                    eligible_machine_ids=["MCH-ACTIVE"],
                    sequence_number=1,
                )
            ],
        ),
        db=db,
    )
    # Create active schedule with operation on MCH-ACTIVE
    from app.models.schedule import Schedule, ScheduleOperation
    sched = Schedule(
        schedule_id="SCHED-TEST-ACTIVE",
        created_at="2026-11-07T10:00:00",
        status="active",
    )
    db.add(sched)
    db.flush()
    sched_op = ScheduleOperation(
        schedule_id="SCHED-TEST-ACTIVE",
        job_id="J-ACTIVE-1",
        operation_id="OP-ACTIVE-1",
        machine_id="MCH-ACTIVE",
        start_time=8.0,
        end_time=10.0,
        duration=2.0,
        status="Scheduled",
    )
    db.add(sched_op)
    db.commit()

    # 5. Attempting to delete a machine with active operations raises 409
    with pytest.raises(HTTPException) as exc_info_409:
        delete_machine("MCH-ACTIVE", db=db)
    assert exc_info_409.value.status_code == 409
    assert "active scheduled operation" in exc_info_409.value.detail


def test_empty_orders_schedule_workflow(db):
    from app.routes.jobs import delete_job
    from app.routes.scheduling import get_current_schedule
    from app.models.schedule import ScheduleOperation

    # 1. Setup machine and job
    create_machine(
        MachineCreate(
            machine_id="MCH-CLEAN",
            name="Clean Test Machine",
            machine_type="CNC Lathe",
            supported_operations=["Turning"],
        ),
        db=db,
    )
    create_job(
        JobCreate(
            job_id="J-TO-DELETE",
            customer_name="Customer X",
            product_name="Product X",
            quantity=10,
            priority="Medium",
            order_date="2026-11-07",
            deadline="2026-11-12",
            operations=[
                OperationCreate(
                    operation_name="Turning",
                    processing_time=1.0,
                    eligible_machine_ids=["MCH-CLEAN"],
                    sequence_number=1,
                )
            ],
        ),
        db=db,
    )

    # 2. Generate schedule - should contain 1 operation
    sched = generate_schedule(db=db)
    assert sched["solver_status"] in ["OPTIMAL", "FEASIBLE"]
    assert len(sched["operations"]) >= 1

    # 3. Delete the job
    delete_job("J-TO-DELETE", db=db)

    # 4. Verify ScheduleOperation for deleted job was removed from database
    orphan_ops = db.query(ScheduleOperation).filter(ScheduleOperation.job_id == "J-TO-DELETE").count()
    assert orphan_ops == 0

    # 5. Verify get_current_schedule returns 0 operations since all jobs are deleted
    curr = get_current_schedule(db=db)
    assert len(curr.operations) == 0

    # 6. Generate schedule with 0 jobs - should succeed with 0 operations and OPTIMAL status
    empty_sched = generate_schedule(db=db)
    assert empty_sched["solver_status"] == "OPTIMAL"
    assert len(empty_sched["operations"]) == 0
    assert empty_sched["makespan_hours"] == 0.0
