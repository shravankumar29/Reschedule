"""FastAPI router for Material Inventory and Requirements."""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.material import Material, MaterialRequirement
from ..models.job import Job
from ..schemas.material import MaterialCreate, MaterialRead, MaterialUpdate, MaterialRequirementRead

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("/", response_model=List[MaterialRead])
def list_materials(db: Session = Depends(get_db)):
    return db.query(Material).order_by(Material.material_id.asc()).all()


@router.post("/", response_model=MaterialRead, status_code=201)
def create_material(payload: MaterialCreate, db: Session = Depends(get_db)):
    existing = db.query(Material).filter(Material.material_id == payload.material_id).first()
    if existing:
        raise HTTPException(400, f"Material with ID '{payload.material_id}' already exists.")

    if payload.available_quantity < 0:
        raise HTTPException(400, "Available quantity cannot be negative.")

    m = Material(
        material_id=payload.material_id,
        name=payload.name,
        category=payload.category,
        unit=payload.unit,
        available_quantity=payload.available_quantity,
        reserved_quantity=0.0,
        min_stock_level=payload.min_stock_level,
        supplier=payload.supplier,
        lead_time_days=payload.lead_time_days,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/{material_id}", response_model=MaterialRead)
def get_material(material_id: str, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.material_id == material_id).first()
    if not m:
        raise HTTPException(404, f"Material '{material_id}' not found.")
    return m


@router.put("/{material_id}", response_model=MaterialRead)
def update_material(material_id: str, payload: MaterialUpdate, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.material_id == material_id).first()
    if not m:
        raise HTTPException(404, f"Material '{material_id}' not found.")

    if payload.name is not None:
        m.name = payload.name
    if payload.category is not None:
        m.category = payload.category
    if payload.unit is not None:
        m.unit = payload.unit
    if payload.available_quantity is not None:
        if payload.available_quantity < 0:
            raise HTTPException(400, "Available quantity cannot be negative.")
        m.available_quantity = payload.available_quantity
    if payload.reserved_quantity is not None:
        if payload.reserved_quantity < 0:
            raise HTTPException(400, "Reserved quantity cannot be negative.")
        m.reserved_quantity = payload.reserved_quantity
    if payload.min_stock_level is not None:
        m.min_stock_level = payload.min_stock_level
    if payload.supplier is not None:
        m.supplier = payload.supplier
    if payload.lead_time_days is not None:
        m.lead_time_days = payload.lead_time_days

    db.commit()
    db.refresh(m)
    return m


@router.get("/{material_id}/requirements", response_model=List[MaterialRequirementRead])
def get_material_requirements(material_id: str, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.material_id == material_id).first()
    if not m:
        raise HTTPException(404, f"Material '{material_id}' not found.")
    return db.query(MaterialRequirement).filter(MaterialRequirement.material_id == material_id).all()

