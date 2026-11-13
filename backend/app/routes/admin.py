"""Admin endpoints – seed reset and health (dev only)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..seed import seed_all

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/seed")
def seed_database(reset: bool = True):
    """Reset the database and populate demo data."""
    seed_all(reset=reset)
    return {"message": "Database seeded successfully"}

