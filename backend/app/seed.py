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
from app.models.job import Job, Operation
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
            supported_operations=["Turning", "Drilling", "Boring"],
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
            supported_operations=["Turning", "Drilling", "Boring"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
            utilization=0,
        ),
        Machine(
            machine_id="MILL-1",
            name="Vertical Milling Centre 01",
            machine_type="Milling Centre",
            supported_operations=["Milling", "Drilling", "Tapping"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
            utilization=0,
        ),
        Machine(
            machine_id="MILL-2",
            name="Horizontal Milling Centre 02",
            machine_type="Milling Centre",
            supported_operations=["Milling", "Drilling"],
            available=True,
            working_start_hour=6,
            working_end_hour=22,
            maintenance_periods=[],
            utilization=0,
        ),
        Machine(
            machine_id="GRIND-1",
            name="Surface Grinding Station",
            machine_type="Surface Grinder",
            supported_operations=["Grinding", "Finishing"],
            available=True,
            working_start_hour=7,
            working_end_hour=19,
            maintenance_periods=[],
            utilization=0,
        ),
    ]
    for m in machines:
        if not db.query(Machine).filter(Machine.machine_id == m.machine_id).first():
            db.add(m)
    db.commit()
    print(f"Seeded {len(machines)} machines.")


def seed_jobs(db: Session):
    today = "2026-11-07"
    # Deadlines spread over the next 3 days
    d1 = "2026-11-08"
    d2 = "2026-11-09"
    d3 = "2026-11-10"

    jobs_data = [
        {
            "job_id": "J-101",
            "customer_name": "Mahindra Precision",
            "product_name": "Hydraulic Valve Housing",
            "quantity": 480,
            "priority": "High",
            "order_date": "2026-11-07",
            "deadline": "2026-11-09",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-101-OP1", "operation_name": "Turning", "processing_time": 3.0, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-101-OP2", "operation_name": "Drilling", "processing_time": 2.0, "eligible_machine_ids": ["CNC-1", "CNC-2", "MILL-1"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-101-OP3", "operation_name": "Grinding", "processing_time": 1.5, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-102",
            "customer_name": "Tata Motors",
            "product_name": "Drive Shaft Coupling",
            "quantity": 200,
            "priority": "Urgent",
            "order_date": "2026-11-07",
            "deadline": "2026-11-08",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-102-OP1", "operation_name": "Turning", "processing_time": 4.0, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-102-OP2", "operation_name": "Boring", "processing_time": 2.5, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-102-OP3", "operation_name": "Grinding", "processing_time": 1.0, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-103",
            "customer_name": "Bosch India",
            "product_name": "Precision Gear Ring",
            "quantity": 300,
            "priority": "High",
            "order_date": "2026-11-07",
            "deadline": "2026-11-09",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-103-OP1", "operation_name": "Milling", "processing_time": 3.5, "eligible_machine_ids": ["MILL-1", "MILL-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-103-OP2", "operation_name": "Drilling", "processing_time": 2.0, "eligible_machine_ids": ["MILL-1", "MILL-2", "CNC-1", "CNC-2"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-103-OP3", "operation_name": "Grinding", "processing_time": 2.0, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-104",
            "customer_name": "L&T Engineering",
            "product_name": "Servo Bracket Assembly",
            "quantity": 150,
            "priority": "Medium",
            "order_date": "2026-11-07",
            "deadline": "2026-11-09",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-104-OP1", "operation_name": "Milling", "processing_time": 2.5, "eligible_machine_ids": ["MILL-1", "MILL-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-104-OP2", "operation_name": "Tapping", "processing_time": 1.5, "eligible_machine_ids": ["MILL-1"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-104-OP3", "operation_name": "Finishing", "processing_time": 1.0, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-105",
            "customer_name": "Godrej Aerospace",
            "product_name": "Stainless Mount Plate",
            "quantity": 860,
            "priority": "High",
            "order_date": "2026-11-08",
            "deadline": "2026-11-10",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-105-OP1", "operation_name": "Milling", "processing_time": 4.0, "eligible_machine_ids": ["MILL-1", "MILL-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-105-OP2", "operation_name": "Drilling", "processing_time": 2.0, "eligible_machine_ids": ["MILL-2", "CNC-2"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-105-OP3", "operation_name": "Grinding", "processing_time": 1.5, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-106",
            "customer_name": "Bajaj Auto",
            "product_name": "Conveyor Idler Shaft",
            "quantity": 650,
            "priority": "Medium",
            "order_date": "2026-11-10",
            "deadline": "2026-11-13",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-106-OP1", "operation_name": "Turning", "processing_time": 3.0, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-106-OP2", "operation_name": "Drilling", "processing_time": 1.5, "eligible_machine_ids": ["CNC-1", "CNC-2", "MILL-1"], "sequence_number": 2, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-107",
            "customer_name": "Crompton Greaves",
            "product_name": "Motor End Shield",
            "quantity": 400,
            "priority": "Low",
            "order_date": "2026-11-10",
            "deadline": "2026-11-14",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-107-OP1", "operation_name": "Turning", "processing_time": 2.0, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-107-OP2", "operation_name": "Milling", "processing_time": 2.5, "eligible_machine_ids": ["MILL-1", "MILL-2"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-107-OP3", "operation_name": "Finishing", "processing_time": 1.0, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-108",
            "customer_name": "Thermax Ltd",
            "product_name": "Pump Impeller",
            "quantity": 120,
            "priority": "Medium",
            "order_date": "2026-11-11",
            "deadline": "2026-11-14",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-108-OP1", "operation_name": "Turning", "processing_time": 2.5, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-108-OP2", "operation_name": "Grinding", "processing_time": 2.0, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 2, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-109",
            "customer_name": "Atlas Copco",
            "product_name": "Bearing Retainer Cap",
            "quantity": 920,
            "priority": "Low",
            "order_date": "2026-11-11",
            "deadline": "2026-11-15",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-109-OP1", "operation_name": "Milling", "processing_time": 1.5, "eligible_machine_ids": ["MILL-1", "MILL-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-109-OP2", "operation_name": "Drilling", "processing_time": 1.0, "eligible_machine_ids": ["MILL-1", "MILL-2", "CNC-2"], "sequence_number": 2, "status": "Pending"},
            ],
        },
        {
            "job_id": "J-110",
            "customer_name": "Kirloskar Electric",
            "product_name": "Rotor Shaft Blank",
            "quantity": 75,
            "priority": "Urgent",
            "order_date": "2026-11-12",
            "deadline": "2026-11-15",
            "status": "Pending",
            "operations": [
                {"operation_id": "J-110-OP1", "operation_name": "Turning", "processing_time": 3.5, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 1, "status": "Pending"},
                {"operation_id": "J-110-OP2", "operation_name": "Boring", "processing_time": 2.0, "eligible_machine_ids": ["CNC-1", "CNC-2"], "sequence_number": 2, "status": "Pending"},
                {"operation_id": "J-110-OP3", "operation_name": "Grinding", "processing_time": 1.5, "eligible_machine_ids": ["GRIND-1"], "sequence_number": 3, "status": "Pending"},
            ],
        },
    ]

    for jd in jobs_data:
        if db.query(Job).filter(Job.job_id == jd["job_id"]).first():
            continue
        ops_data = jd.pop("operations")
        job = Job(**jd)
        db.add(job)
        db.flush()
        for od in ops_data:
            od["job_id"] = job.job_id
            db.add(Operation(**od))

    db.commit()
    print(f"Seeded {len(jobs_data)} jobs with operations.")


def seed_all(reset: bool = True):
    if reset:
        reset_db()
    db: Session = SessionLocal()
    try:
        seed_machines(db)
        seed_jobs(db)
        print("Seed complete. Run POST /api/schedule/generate to build the initial schedule.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all(reset=True)

