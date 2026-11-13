# ReSchedule Backend — Disruption-Recovery Production Scheduling

ReSchedule is an intelligent production scheduling and disruption-recovery engine designed for MSME job shops.

---

## 1. Technology Stack

- **Framework**: Python 3.14+, FastAPI (REST API with OpenAPI documentation)
- **Mathematical Optimization**: Google OR-Tools CP-SAT Solver (`ortools.sat.python.cp_model`)
- **ORM & Database**: SQLAlchemy 2.0 with SQLite (`reschedule.db`)
- **Validation**: Pydantic v2
- **Testing**: PyTest with automated constraint verification

---

## 2. Core Scheduling & Rescheduling Engine (Google OR-Tools CP-SAT)

The scheduling problem is formulated as a **Flexible Job Shop Problem (FJSP)** with:
1. **Precedence constraints**: $Start(Op_{i+1}) \ge End(Op_i)$ for successive operations of a job.
2. **Machine resource constraints**: Non-overlapping interval variables (`AddNoOverlap`) on each machine.
3. **Machine eligibility**: Optional interval variables on alternative eligible machines (`NewOptionalIntervalVar`), constrained by `AddExactlyOne` across eligible alternatives.
4. **Maintenance & Breakdown windows**: Fixed downtime intervals participating in `AddNoOverlap`.
5. **Freeze constraints for completed tasks**: Completed operations are locked at their historical start/end times and cannot be moved during disruption recovery.
6. **Multi-objective optimisation**:
   $$\min \sum \left( W_{tardiness} \cdot P_{job} \cdot \max(0, End - Deadline) \right) + W_{makespan} \cdot C_{max} + W_{change} \cdot \Delta_{schedule}$$

---

## 3. API Endpoints

### Machine Management
- `GET /api/machines/`: List all machines and current availability/utilization.
- `POST /api/machines/`: Register a new machine.
- `GET /api/machines/{machine_id}`: Get machine details.
- `PUT /api/machines/{machine_id}`: Update machine details.
- `DELETE /api/machines/{machine_id}`: Delete a machine.
- `PATCH /api/machines/{machine_id}/availability`: Toggle machine availability.

### Job & Order Management
- `GET /api/jobs/`: List all jobs and their routing operations.
- `POST /api/jobs/`: Create a production job with sequential operations and eligible machines.
- `GET /api/jobs/{job_id}`: Get job details.
- `PUT /api/jobs/{job_id}`: Update job.
- `DELETE /api/jobs/{job_id}`: Delete job.
- `GET /api/jobs/{job_id}/operations`: List required operations for a job.

### Disruption Management
- `POST /api/disruptions/`: Report a machine breakdown, rush order, or material delay. Automatically flags machine downtime.
- `GET /api/disruptions/`: View disruption history.
- `GET /api/disruptions/{disruption_id}`: Get disruption details.
- `PATCH /api/disruptions/{disruption_id}/resolve`: Resolve disruption and restore machine availability.

### Production Scheduling & Rescheduling
- `POST /api/schedule/generate`: Run initial CP-SAT solver, validate 7 constraints, and save schedule.
- `POST /api/reschedule`: Run disruption recovery engine, preserve frozen operations, reassign affected operations to alternative machines, and save revised schedule.
- `GET /api/schedule/current`: Retrieve active schedule.
- `GET /api/schedule/history`: Retrieve full schedule history for audit and comparison.
- `GET /api/schedule/{schedule_id}`: Retrieve a specific schedule.
- `GET /api/schedule/{schedule_id}/validate`: Run the 7-point validation suite on any schedule.

### Impact Analysis & Grounded Explanations
- `GET /api/reschedule/impact`: Compare original vs revised schedules (makespan change, rescheduled operations, machine changes, delay hours, machine utilization).
- `GET /api/reschedule/explanations`: Grounded rule-based explanations explaining why operations were moved and which machines were selected.

### Analytics & Administration
- `GET /api/analytics/overview`: Factory KPI overview.
- `GET /api/analytics/machine-utilization`: Utilization metrics per machine.
- `GET /api/analytics/delayed-jobs`: List of jobs at risk of deadline breach.
- `POST /api/admin/seed`: Seed demo factory data (5 machines, 10 jobs, multi-operation routings).

---

## 4. Running the Backend

From the `backend` folder:

```bash
# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation (Swagger UI) is available at:
`http://localhost:8000/docs`

---

## 5. Running Automated Tests

```bash
pytest -v
```

All 7 core test scenarios are validated:
1. Initial scheduling
2. Machine breakdown
3. Alternative machine allocation
4. Urgent order insertion
5. Operation dependencies
6. Machine overlap prevention
7. Infeasible schedule handling

