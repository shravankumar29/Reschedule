"""FastAPI router – Job and Operation CRUD."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.job import Job, Operation
from ..schemas.job import JobCreate, JobRead, JobUpdate, OperationRead

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _gen_op_id(job_id: str, seq: int) -> str:
    return f"{job_id}-OP{seq}"


@router.get("/", response_model=List[JobRead])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()


@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    if db.query(Job).filter(Job.job_id == payload.job_id).first():
        raise HTTPException(400, "job_id already exists")
    ops_data = payload.operations
    job_data = payload.model_dump(exclude={"operations"})
    job = Job(**job_data)
    db.add(job)
    db.flush()  # get job PK
    for op in ops_data:
        op_obj = Operation(
            operation_id=_gen_op_id(payload.job_id, op.sequence_number),
            job_id=payload.job_id,
            **op.model_dump(),
        )
        db.add(op_obj)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    return j


@router.put("/{job_id}", response_model=JobRead)
def update_job(job_id: str, payload: JobUpdate, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(j, field, value)
    db.commit()
    db.refresh(j)
    return j


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    db.delete(j)
    db.commit()


@router.get("/{job_id}/operations", response_model=List[OperationRead])
def list_operations(job_id: str, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    return j.operations

