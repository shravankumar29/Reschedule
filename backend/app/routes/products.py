"""FastAPI router – Product Catalog and Production Routing Templates."""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.product import Product, ProductOperation
from ..models.machine import Machine
from ..models.job import Job
from ..schemas.product import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProductOperationCreate,
    ProductOperationRead,
)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=List[ProductRead])
def list_products(
    active_only: bool = Query(False, description="Filter for active products only"),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    return query.order_by(Product.name).all()


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.product_id == payload.product_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with ID '{payload.product_id}' already exists.",
        )

    # Validate machines for routing operations
    all_machines = {m.machine_id for m in db.query(Machine).all()}
    sequences_seen = set()

    for op in payload.routing_operations:
        if op.sequence_number in sequences_seen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate sequence number {op.sequence_number} in routing operations.",
            )
        sequences_seen.add(op.sequence_number)

        if not op.eligible_machine_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operation '{op.operation_name}' must have at least one eligible machine.",
            )

        if all_machines:
            invalid_machines = [m for m in op.eligible_machine_ids if m not in all_machines]
            if invalid_machines:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid eligible machines for '{op.operation_name}': {invalid_machines}. Must exist in factory machines.",
                )

    now_iso = datetime.now(timezone.utc).isoformat()
    prod_data = payload.model_dump(exclude={"routing_operations"})
    prod_data["created_at"] = now_iso
    prod_data["updated_at"] = now_iso

    product = Product(**prod_data)
    db.add(product)
    db.flush()

    for op in payload.routing_operations:
        op_obj = ProductOperation(
            product_id=product.product_id,
            **op.model_dump(),
        )
        db.add(op_obj)

    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found.",
        )
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found.",
        )

    data = payload.model_dump(exclude_unset=True)
    routing_ops = data.pop("routing_operations", None)

    for field, value in data.items():
        setattr(product, field, value)

    if routing_ops is not None:
        all_machines = {m.machine_id for m in db.query(Machine).all()}
        sequences_seen = set()

        for op in routing_ops:
            seq = op.get("sequence_number")
            if seq in sequences_seen:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate sequence number {seq} in routing operations.",
                )
            sequences_seen.add(seq)

            mids = op.get("eligible_machine_ids", [])
            if not mids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Operation '{op.get('operation_name')}' must have at least one eligible machine.",
                )
            if all_machines:
                invalid_machines = [m for m in mids if m not in all_machines]
                if invalid_machines:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid machines for '{op.get('operation_name')}': {invalid_machines}.",
                    )

        # Delete existing operations and replace
        db.query(ProductOperation).filter(ProductOperation.product_id == product_id).delete()
        for op_dict in routing_ops:
            op_obj = ProductOperation(product_id=product_id, **op_dict)
            db.add(op_obj)

    product.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_or_deactivate_product(
    product_id: str,
    hard_delete: bool = Query(False),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if jobs reference this product
    active_jobs = db.query(Job).filter(Job.product_id == product_id).count()
    if active_jobs > 0 and hard_delete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete product '{product_id}' because {active_jobs} order(s) reference it. Deactivate instead.",
        )

    if hard_delete and active_jobs == 0:
        db.delete(product)
    else:
        product.is_active = False
        product.updated_at = datetime.now(timezone.utc).isoformat()
    
    db.commit()


@router.get("/{product_id}/routing", response_model=List[ProductOperationRead])
def get_product_routing(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.routing_operations

