"""Test adding new machine and new order, and scheduling them."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.routes.machines import create_machine, list_machines
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
