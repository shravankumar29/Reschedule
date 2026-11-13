"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import (
    machines_router,
    jobs_router,
    products_router,
    disruptions_router,
    scheduling_router,
    analytics_router,
    admin_router,
    materials_router,
    rush_orders_router,
)

# Create all tables on startup (dev mode; use Alembic for production)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import SessionLocal
    from .models.machine import Machine
    from .seed import seed_all
    db = SessionLocal()
    try:
        if db.query(Machine).count() == 0:
            seed_all(reset=False)
    finally:
        db.close()
    yield


app = FastAPI(
    title="ReSchedule API",
    description="Production scheduling & disruption-recovery engine for MSME job shops.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines_router)
app.include_router(jobs_router)
app.include_router(products_router)
app.include_router(disruptions_router)
app.include_router(scheduling_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(materials_router)
app.include_router(rush_orders_router)


@app.get("/")
def root():
    return {"message": "ReSchedule API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
