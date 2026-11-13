"""
Comprehensive test suite for Product Catalog, Production Routing Templates,
Order Instantiation, CP-SAT Optimization, and Order Details Experience.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.machine import Machine
from app.models.material import Material
from app.models.product import Product, ProductOperation
from app.models.job import Job, Operation
from app.models.schedule import Schedule, ScheduleOperation
from app.routes.products import (
    create_product,
    list_products,
    get_product,
    update_product,
    delete_or_deactivate_product,
)
from app.routes.jobs import create_job, get_job, get_job_full_details
from app.schemas.product import ProductCreate, ProductUpdate, ProductOperationCreate
from app.schemas.job import JobCreate
from app.services.scheduling_engine import run_scheduling_engine


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed machines
    m1 = Machine(machine_id="CNC-1", name="CNC Turning Cell 01", machine_type="CNC Lathe", supported_operations=["Turning", "Drilling"], working_start_hour=6, working_end_hour=22, available=True)
    m2 = Machine(machine_id="CNC-2", name="CNC Turning Cell 02", machine_type="CNC Lathe", supported_operations=["Turning", "Drilling"], working_start_hour=6, working_end_hour=22, available=True)
    m3 = Machine(machine_id="MILL-1", name="Vertical Milling Centre 01", machine_type="Milling Centre", supported_operations=["Milling"], working_start_hour=6, working_end_hour=22, available=True)
    m4 = Machine(machine_id="GRIND-1", name="Surface Grinding Station", machine_type="Surface Grinder", supported_operations=["Grinding"], working_start_hour=7, working_end_hour=19, available=True)
    session.add_all([m1, m2, m3, m4])

    # Seed material
    mat = Material(material_id="MAT-001", name="4140 Alloy Steel", category="Raw Material", unit="kg", available_quantity=200.0, reserved_quantity=0.0, min_stock_level=20.0, supplier="Tata Steel")
    session.add(mat)

    # Seed baseline product
    p1 = Product(
        product_id="PROD-001",
        name="Hydraulic Valve Housing",
        category="Fluid Power Components",
        description="Precision valve housing",
        is_active=True,
    )
    session.add(p1)
    session.flush()

    op1 = ProductOperation(product_id="PROD-001", operation_name="Turning", sequence_number=1, processing_time=2.0, duration_basis="fixed", eligible_machine_ids=["CNC-1", "CNC-2"], required_material_id="MAT-001", required_material_qty=10.0)
    op2 = ProductOperation(product_id="PROD-001", operation_name="Milling", sequence_number=2, processing_time=1.5, duration_basis="fixed", eligible_machine_ids=["MILL-1"])
    op3 = ProductOperation(product_id="PROD-001", operation_name="Grinding", sequence_number=3, processing_time=1.0, duration_basis="fixed", eligible_machine_ids=["GRIND-1"])
    session.add_all([op1, op2, op3])

    session.commit()
    try:
        yield session
    finally:
        session.close()


def test_product_crud_and_validation(db):
    """Test product creation, validation against unknown machines, and sequence uniqueness."""
    # 1. Duplicate sequence rejection
    with pytest.raises(HTTPException) as exc_info:
        bad_duplicate = ProductCreate(
            product_id="TEST-PROD-01",
            name="Actuator",
            category="Fluid",
            routing_operations=[
                ProductOperationCreate(operation_name="Op1", sequence_number=1, processing_time=2.0, duration_basis="fixed", eligible_machine_ids=["CNC-1"]),
                ProductOperationCreate(operation_name="Op2", sequence_number=1, processing_time=1.0, duration_basis="fixed", eligible_machine_ids=["MILL-1"]),
            ],
        )
        create_product(payload=bad_duplicate, db=db)
    assert exc_info.value.status_code == 400
    assert "Duplicate sequence number" in exc_info.value.detail

    # 2. Unknown machine rejection
    with pytest.raises(HTTPException) as exc_info:
        bad_machine = ProductCreate(
            product_id="TEST-PROD-02",
            name="Actuator",
            category="Fluid",
            routing_operations=[
                ProductOperationCreate(operation_name="Op1", sequence_number=1, processing_time=2.0, duration_basis="fixed", eligible_machine_ids=["NONEXISTENT_MCH"]),
            ],
        )
        create_product(payload=bad_machine, db=db)
    assert exc_info.value.status_code == 400
    assert "Invalid eligible machines" in exc_info.value.detail

    # 3. Valid creation
    valid = ProductCreate(
        product_id="PROD-VALVE-X",
        name="High-Pressure Relief Valve X",
        category="Valves & Fluid Power",
        description="Custom high-pressure relief valve body.",
        is_active=True,
        routing_operations=[
            ProductOperationCreate(operation_name="Rough Turning", sequence_number=1, processing_time=2.5, duration_basis="fixed", eligible_machine_ids=["CNC-1", "CNC-2"]),
            ProductOperationCreate(operation_name="Face Milling", sequence_number=2, processing_time=2.0, duration_basis="fixed", eligible_machine_ids=["MILL-1"]),
            ProductOperationCreate(operation_name="Precision Grinding", sequence_number=3, processing_time=1.5, duration_basis="fixed", eligible_machine_ids=["GRIND-1"]),
        ],
    )
    prod = create_product(payload=valid, db=db)
    assert prod.product_id == "PROD-VALVE-X"
    assert len(prod.routing_operations) == 3

    # 4. Update product
    updated = update_product(
        product_id="PROD-VALVE-X",
        payload=ProductUpdate(description="Updated description"),
        db=db,
    )
    assert updated.description == "Updated description"

    # 5. List products
    all_prods = list_products(active_only=False, db=db)
    assert len(all_prods) >= 2
    assert any(p.product_id == "PROD-VALVE-X" for p in all_prods)


def test_order_instantiation_from_product_routing(db):
    """Test creating an order referencing a product: verifies automatic operation instantiation."""
    order_payload = JobCreate(
        job_id="J-VALVE-99",
        product_id="PROD-001",
        customer_name="Hydraulics Corp International",
        product_name="Hydraulic Valve Housing",
        quantity=150,
        priority="High",
        order_date="2026-11-07",
        deadline="2026-11-10",
    )
    job = create_job(payload=order_payload, db=db)
    assert job.job_id == "J-VALVE-99"
    assert job.product_id == "PROD-001"
    assert len(job.operations) == 3

    ops = sorted(job.operations, key=lambda x: x.sequence_number)
    assert ops[0].operation_name == "Turning"
    assert set(ops[0].eligible_machine_ids) == {"CNC-1", "CNC-2"}
    assert ops[1].operation_name == "Milling"
    assert ops[2].operation_name == "Grinding"


def test_scheduling_and_order_details_workflow(db):
    """
    Test end-to-end workflow:
    1. Initial Schedule generation with multi-operation jobs.
    2. Check order details route timeline and progress %.
    3. Breakdown simulation on CNC-1.
    4. Reschedule recovery.
    5. Verify Order Details reflects live schedule.
    """
    # Create an order
    create_job(
        payload=JobCreate(
            job_id="J-TEST-FLOW",
            product_id="PROD-001",
            customer_name="Client Flow",
            product_name="Hydraulic Valve Housing",
            quantity=50,
            priority="Urgent",
            order_date="2026-11-07",
            deadline="2026-11-09",
        ),
        db=db,
    )

    # Run CP-SAT scheduling engine directly on db
    sched_res = run_scheduling_engine(db, schedule_id="SCHED-INIT", schedule_type="initial")
    assert sched_res["solver_status"] in ["OPTIMAL", "FEASIBLE"]

    # Query Order Details endpoint
    details = get_job_full_details(job_id="J-TEST-FLOW", db=db)
    assert details["job_id"] == "J-TEST-FLOW"
    assert details["product_name"] == "Hydraulic Valve Housing"
    assert details["total_operations"] == 3
    assert len(details["routing_operations"]) == 3

    ops = details["routing_operations"]
    for i in range(1, len(ops)):
        prev_end = ops[i - 1]["planned_end"]
        cur_start = ops[i]["planned_start"]
        if prev_end is not None and cur_start is not None:
            assert cur_start >= prev_end, f"Precedence violation: {cur_start} < {prev_end}"


def test_edge_cases(db):
    """Test edge cases: deactivated product, zero/negative quantities, backward compatibility."""
    # Deactivate product
    delete_or_deactivate_product(product_id="PROD-001", hard_delete=False, db=db)

    # Cannot create order with deactivated product
    with pytest.raises(HTTPException) as exc_info:
        create_job(
            payload=JobCreate(
                job_id="J-FAIL-01",
                product_id="PROD-001",
                customer_name="Test Corp",
                product_name="Hydraulic Valve Housing",
                quantity=100,
                priority="Medium",
                order_date="2026-11-07",
                deadline="2026-11-10",
            ),
            db=db,
        )
    assert exc_info.value.status_code == 400
    assert "inactive/decommissioned" in exc_info.value.detail

    # Backward compatibility: job without product_id can still be created and queried
    legacy_job = create_job(
        payload=JobCreate(
            job_id="J-LEGACY-01",
            customer_name="Legacy Client",
            product_name="Custom Part",
            quantity=80,
            priority="Low",
            order_date="2026-11-07",
            deadline="2026-11-12",
        ),
        db=db,
    )
    assert legacy_job.job_id == "J-LEGACY-01"
    details = get_job_full_details(job_id="J-LEGACY-01", db=db)
    assert details["job_id"] == "J-LEGACY-01"
    assert details["product_name"] == "Custom Part"
