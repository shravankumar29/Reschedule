"""
Demo seed data for ReSchedule.

Factory: Northstar Components, Plant 01
5 machines, 10 jobs, multiple operations each.

Demo disruption scenario: CNC-1 breaks down at 10:00 AM today.
Run this script from the backend/ directory:
    python -m app.seed
Or via the reset endpoint: POST /api/admin/seed
"""
from __future__ import annotations

import sys
import os

# Allow running as a module from the backend/ folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.machine import Machine
from app.models.product import Product, ProductOperation
from app.models.job import Job, Operation
from app.models.material import Material, MaterialRequirement
from app.models.disruption import Disruption
from app.models.schedule import Schedule, ScheduleOperation


def reset_db():
    """Drop and recreate all tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")


def seed_machines(db: Session):
    machines = [
        Machine(
            machine_id="CNC-1",
            name="CNC Turning Cell 01",
            machine_type="CNC Lathe",
            supported_operations=["Turning", "Drilling", "Boring", "Milling", "Grinding", "Finishing", "Tapping"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
            utilization=0,
        ),
        Machine(
            machine_id="CNC-2",
            name="CNC Turning Cell 02",
            machine_type="CNC Lathe",
            supported_operations=["Turning", "Drilling", "Boring", "Milling", "Grinding", "Finishing", "Tapping"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
            utilization=0,
        ),
    ]
    for m in machines:
        if not db.query(Machine).filter(Machine.machine_id == m.machine_id).first():
            db.add(m)
    db.commit()
    print(f"Seeded {len(machines)} machines.")


def seed_materials(db: Session):
    materials = [
        Material(
            material_id="MAT-001",
            name="4140 Alloy Steel Billet",
            category="Raw Material",
            unit="kg",
            available_quantity=500.0,
            reserved_quantity=120.0,
            min_stock_level=50.0,
            supplier="Tata Steel Ltd",
            lead_time_days=3,
        ),
        Material(
            material_id="MAT-002",
            name="Aluminum 6061-T6 Bar",
            category="Raw Material",
            unit="kg",
            available_quantity=320.0,
            reserved_quantity=80.0,
            min_stock_level=40.0,
            supplier="Hindalco Industries",
            lead_time_days=2,
        ),
        Material(
            material_id="MAT-003",
            name="SS 316L Round Bar",
            category="Raw Material",
            unit="kg",
            available_quantity=45.0,
            reserved_quantity=30.0,
            min_stock_level=50.0,
            supplier="Jindal Stainless",
            lead_time_days=4,
        ),
        Material(
            material_id="MAT-004",
            name="EN8 Carbon Steel Shaft Blank",
            category="Forgings",
            unit="pcs",
            available_quantity=150.0,
            reserved_quantity=40.0,
            min_stock_level=25.0,
            supplier="Bharat Forge",
            lead_time_days=5,
        ),
        Material(
            material_id="MAT-005",
            name="Brass C360 Hex Rod",
            category="Bar Stock",
            unit="kg",
            available_quantity=90.0,
            reserved_quantity=15.0,
            min_stock_level=20.0,
            supplier="Metals India Corp",
            lead_time_days=2,
        ),
    ]
    for m in materials:
        if not db.query(Material).filter(Material.material_id == m.material_id).first():
            db.add(m)
    db.commit()
    print(f"Seeded {len(materials)} materials.")


def seed_products(db: Session):
    products = [
        {
            "product_id": "PROD-001",
            "name": "Hydraulic Valve Housing",
            "category": "Fluid Power Components",
            "description": "High-pressure cast ductile iron valve housing with precision bore and milled port faces.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Turning", "sequence_number": 1, "processing_time": 3.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"], "required_material_id": "MAT-001", "required_material_qty": 48.0},
                {"operation_name": "Drilling", "sequence_number": 2, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Grinding", "sequence_number": 3, "processing_time": 1.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-002",
            "name": "Drive Shaft Coupling",
            "category": "Drivetrain & Transmission",
            "description": "Heavy-duty forged carbon steel drive coupling with internal splines and ground journal.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Turning", "sequence_number": 1, "processing_time": 4.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"], "required_material_id": "MAT-004", "required_material_qty": 20.0},
                {"operation_name": "Boring", "sequence_number": 2, "processing_time": 2.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Grinding", "sequence_number": 3, "processing_time": 1.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-003",
            "name": "Precision Gear Ring",
            "category": "Gearing & Power",
            "description": "High-grade alloy steel internal gear ring with CNC milled teeth and finish ground outer diameter.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Milling", "sequence_number": 1, "processing_time": 3.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"], "required_material_id": "MAT-002", "required_material_qty": 35.0},
                {"operation_name": "Drilling", "sequence_number": 2, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Grinding", "sequence_number": 3, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-004",
            "name": "Servo Bracket Assembly",
            "category": "Robotics & Automation",
            "description": "Precision milled mounting bracket for industrial servo actuators.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Milling", "sequence_number": 1, "processing_time": 2.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Tapping", "sequence_number": 2, "processing_time": 1.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Finishing", "sequence_number": 3, "processing_time": 1.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-005",
            "name": "Stainless Mount Plate",
            "category": "Structural & Aerospace",
            "description": "Corrosion-resistant SS 316L mounting interface plate with multi-hole pattern.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Milling", "sequence_number": 1, "processing_time": 4.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Drilling", "sequence_number": 2, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Grinding", "sequence_number": 3, "processing_time": 1.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-006",
            "name": "Conveyor Idler Shaft",
            "category": "Material Handling",
            "description": "EN8 turned steel shaft for bulk material conveyor rollers.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Turning", "sequence_number": 1, "processing_time": 3.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Drilling", "sequence_number": 2, "processing_time": 1.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-007",
            "name": "Motor End Shield",
            "category": "Electric Drives",
            "description": "Die-cast end bell housing with bearing seat and mounting flanges.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Turning", "sequence_number": 1, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Milling", "sequence_number": 2, "processing_time": 2.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Finishing", "sequence_number": 3, "processing_time": 1.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-008",
            "name": "Pump Impeller",
            "category": "Fluid Power Components",
            "description": "Balanced high-flow bronze impeller casting with ground bore.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Turning", "sequence_number": 1, "processing_time": 2.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Grinding", "sequence_number": 2, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-009",
            "name": "Bearing Retainer Cap",
            "category": "Precision Gearing",
            "description": "Precision milled retainer cap with oil seal groove.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Milling", "sequence_number": 1, "processing_time": 1.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Drilling", "sequence_number": 2, "processing_time": 1.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
        {
            "product_id": "PROD-010",
            "name": "Rotor Shaft Blank",
            "category": "Electric Drives",
            "description": "High-torque induction rotor blank with stepped journal diameters.",
            "is_active": True,
            "routing_operations": [
                {"operation_name": "Turning", "sequence_number": 1, "processing_time": 3.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Boring", "sequence_number": 2, "processing_time": 2.0, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
                {"operation_name": "Grinding", "sequence_number": 3, "processing_time": 1.5, "duration_basis": "fixed", "eligible_machine_ids": ["CNC-1", "CNC-2"]},
            ],
        },
    ]

    for p_data in products:
        if db.query(Product).filter(Product.product_id == p_data["product_id"]).first():
            continue
        r_ops = p_data.pop("routing_operations")
        prod = Product(**p_data)
        db.add(prod)
        db.flush()
        for r in r_ops:
            db.add(ProductOperation(product_id=prod.product_id, **r))
    db.commit()
    print(f"Seeded {len(products)} products with routing templates.")


def seed_jobs(db: Session):
    today = "2026-11-07"
    d1 = "2026-11-08"
    d2 = "2026-11-09"

    jobs_data = [
        {
            "job_id": "J-101",
            "customer_name": "Mahindra Precision",
            "product_name": "Hydraulic Valve Housing",
            "quantity": 480,
            "priority": "High",
            "order_date": today,
            "deadline": d2,
            "status": "Pending",
            "operations": [
                {
                    "operation_id": "J-101-OP1",
                    "operation_name": "Turning",
                    "processing_time": 3.0,
                    "eligible_machine_ids": ["CNC-1", "CNC-2"],
                    "sequence_number": 1,
                    "status": "Pending",
                    "required_material_id": "MAT-001",
                    "required_material_qty": 48.0,
                },
                {
                    "operation_id": "J-101-OP2",
                    "operation_name": "Drilling",
                    "processing_time": 2.0,
                    "eligible_machine_ids": ["CNC-1", "CNC-2"],
                    "sequence_number": 2,
                    "status": "Pending",
                },
            ],
        },
        {
            "job_id": "J-102",
            "customer_name": "Tata Motors",
            "product_name": "Drive Shaft Coupling",
            "quantity": 200,
            "priority": "High",
            "order_date": today,
            "deadline": d1,
            "status": "Pending",
            "operations": [
                {
                    "operation_id": "J-102-OP1",
                    "operation_name": "Turning",
                    "processing_time": 4.0,
                    "eligible_machine_ids": ["CNC-1", "CNC-2"],
                    "sequence_number": 1,
                    "status": "Pending",
                    "required_material_id": "MAT-004",
                    "required_material_qty": 20.0,
                },
                {
                    "operation_id": "J-102-OP2",
                    "operation_name": "Boring",
                    "processing_time": 2.5,
                    "eligible_machine_ids": ["CNC-1", "CNC-2"],
                    "sequence_number": 2,
                    "status": "Pending",
                },
            ],
        },
    ]

    for jd in jobs_data:
        if db.query(Job).filter(Job.job_id == jd["job_id"]).first():
            continue
        ops_data = jd.pop("operations")
        product_obj = db.query(Product).filter(Product.name == jd["product_name"]).first()
        if product_obj:
            jd["product_id"] = product_obj.product_id
        job = Job(**jd)
        db.add(job)
        db.flush()
        for od in ops_data:
            od["job_id"] = job.job_id
            mat_id = od.get("required_material_id")
            mat_qty = od.get("required_material_qty")
            db.add(Operation(**od))
            if mat_id and mat_qty:
                db.add(
                    MaterialRequirement(
                        job_id=job.job_id,
                        operation_id=od.get("operation_id"),
                        material_id=mat_id,
                        required_quantity=float(mat_qty),
                        allocated_quantity=float(mat_qty),
                    )
                )

    db.commit()
    print(f"Seeded {len(jobs_data)} jobs with operations and material requirements.")


def seed_all(reset: bool = True):
    if reset:
        reset_db()
    db: Session = SessionLocal()
    try:
        seed_machines(db)
        seed_materials(db)
        seed_products(db)
        seed_jobs(db)
        from .routes.scheduling import generate_schedule
        try:
            generate_schedule(db)
            print("Initial schedule generated successfully.")
        except Exception as e:
            print("Auto-generating initial schedule failed:", e)
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all(reset=True)

