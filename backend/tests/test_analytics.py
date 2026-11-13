"""Unit tests for analytics service and endpoints."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.machine import Machine
from app.models.job import Job, Operation
from app.models.schedule import Schedule, ScheduleOperation
from app.models.disruption import Disruption
from app.services.analytics_service import (
    compute_overview_kpis,
    compute_machine_utilization_data,
    compute_production_output_chart,
)
from app.routes.analytics import overview, machine_utilization, production_output, machine_status


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed 2 machines
    m1 = Machine(
        machine_id="CNC-1",
        name="CNC Turning Cell 1",
        machine_type="CNC",
        supported_operations=["Turning"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    m2 = Machine(
        machine_id="MILL-1",
        name="Vertical Mill 1",
        machine_type="Milling",
        supported_operations=["Milling"],
        working_start_hour=6,
        working_end_hour=22,
        available=True,
    )
    session.add_all([m1, m2])

    # Seed 2 jobs
    j1 = Job(
        job_id="J-101",
        customer_name="Customer A",
        product_name="Product 1",
        quantity=100,
        priority="High",
        order_date="2026-11-07",
        deadline="2026-11-10",
        status="Pending",
    )
    j2 = Job(
        job_id="J-102",
        customer_name="Customer B",
        product_name="Product 2",
        quantity=50,
        priority="Medium",
        order_date="2026-11-07",
        deadline="2026-11-09",
        status="Completed",
    )
    session.add_all([j1, j2])

    # Seed active schedule with 2 operations
    sched = Schedule(
        schedule_id="SCHED-TEST-1",
        created_at="2026-11-07T06:00:00",
        status="active",
        makespan_hours=12.0,
        total_jobs=2,
        on_time_count=2,
        delayed_count=0,
    )
    session.add(sched)
    session.flush()

    op1 = ScheduleOperation(
        schedule_id="SCHED-TEST-1",
        job_id="J-101",
        operation_id="J-101-OP1",
        machine_id="CNC-1",
        start_time=6.0,
        end_time=12.0,
        duration=6.0,
        date="2026-11-07",
        end_date="2026-11-07",
        status="Scheduled",
    )
    op2 = ScheduleOperation(
        schedule_id="SCHED-TEST-1",
        job_id="J-102",
        operation_id="J-102-OP1",
        machine_id="MILL-1",
        start_time=8.0,
        end_time=12.0,
        duration=4.0,
        date="2026-11-08",
        end_date="2026-11-08",
        status="Completed",
    )
    session.add_all([op1, op2])
    session.commit()

    try:
        yield session
    finally:
        session.close()


def test_overview_kpis(db):
    kpis = compute_overview_kpis(db, range_type="week")
    assert kpis["total_orders"] == 2
    assert kpis["completed_orders"] == 1
    assert kpis["total_active_orders"] == 1
    assert kpis["total_machines"] == 2
    assert kpis["available_machines"] == 2
    assert kpis["broken_machines_count"] == 0
    assert kpis["average_scheduled_utilization_pct"] >= 0


def test_machine_utilization_calculation(db):
    util_data = compute_machine_utilization_data(db, range_type="week")
    assert len(util_data) == 2
    m1_util = next(u for u in util_data if u["machine_id"] == "CNC-1")
    assert m1_util["scheduled_hours"] == 6.0
    assert m1_util["net_available_hours"] > 0
    assert m1_util["utilization_pct"] > 0


def test_downtime_reduces_available_time(db):
    # Add a breakdown disruption on CNC-1
    dis = Disruption(
        disruption_id="D-TEST-1",
        disruption_type="Machine Breakdown",
        resource="CNC-1",
        reported_at="2026-11-07T10:00:00",
        severity="Critical",
        breakdown_start="10:00",
        estimated_repair_hours=4.0,
        status="Open",
    )
    db.add(dis)
    # Mark CNC-1 unavailable
    m1 = db.query(Machine).filter(Machine.machine_id == "CNC-1").first()
    m1.available = False
    db.commit()

    util_data = compute_machine_utilization_data(db, range_type="week")
    m1_util = next(u for u in util_data if u["machine_id"] == "CNC-1")
    assert m1_util["breakdown_downtime_hours"] == 4.0
    assert m1_util["operational_status"] == "Breakdown"


def test_production_output_chart(db):
    prod = compute_production_output_chart(db, range_type="week")
    assert "data" in prod
    assert len(prod["data"]) == 7
    # Verify daily quantities sum up
    assert prod["total_planned_units"] >= 0
    assert prod["total_target_units"] > 0


def test_analytics_api_endpoints(db):
    res_ov = overview(range="week", db=db)
    assert res_ov["total_orders"] == 2

    res_util = machine_utilization(range="week", db=db)
    assert len(res_util) == 2

    res_prod = production_output(range="week", db=db)
    assert len(res_prod["data"]) == 7

    res_status = machine_status(range="week", db=db)
    assert len(res_status) == 2
    assert all("operational_status" in s or "status" in s for s in res_status)
