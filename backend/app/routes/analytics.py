"""FastAPI router – Analytics endpoints."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.impact_analyzer import get_impact_analysis
from ..services.analytics_service import (
    compute_overview_kpis,
    compute_machine_utilization_data,
    compute_production_output_chart,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def overview(
    range: str = Query("week", description="Reporting range: today, week, month"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return comprehensive data-driven KPI overview for dashboard."""
    kpis = compute_overview_kpis(db, range_type=range, start_date=start_date, end_date=end_date)
    # Ensure backward compatibility aliases
    kpis["total_jobs"] = kpis["total_orders"]
    kpis["pending_jobs"] = kpis["pending_orders"]
    kpis["in_production_jobs"] = kpis["in_production_orders"]
    kpis["completed_jobs"] = kpis["completed_orders"]
    kpis["delayed_jobs"] = kpis["delayed_orders"]
    kpis["urgent_jobs"] = kpis["urgent_orders"]
    return kpis


@router.get("/machine-utilization")
def machine_utilization(
    range: str = Query("week", description="Reporting range: today, week, month"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return machine utilization calculated from actual scheduled operations and downtime."""
    return compute_machine_utilization_data(
        db, range_type=range, start_date=start_date, end_date=end_date
    )


@router.get("/production-output")
def production_output(
    range: str = Query("week", description="Reporting range: today, week, month"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return daily planned and actual production output quantities."""
    return compute_production_output_chart(
        db, range_type=range, start_date=start_date, end_date=end_date
    )


@router.get("/machine-status")
def machine_status(
    range: str = Query("week", description="Reporting range: today, week, month"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return operational status and assigned task for every machine."""
    util_data = compute_machine_utilization_data(db, range_type=range)
    return [
        {
            "machine_id": item["machine_id"],
            "name": item["name"],
            "machine_type": item["machine_type"],
            "status": item["operational_status"],
            "current_task": item["current_task"],
            "utilization_pct": item["utilization_pct"],
            "downtime_hours": item["breakdown_downtime_hours"],
        }
        for item in util_data
    ]


@router.get("/delayed-jobs")
def delayed_jobs(db: Session = Depends(get_db)) -> Dict[str, Any]:
    impact = get_impact_analysis(db)
    return {
        "delayed_jobs": impact.get("delayed_jobs", []),
        "delayed_count": impact.get("delayed_count", 0),
        "on_time_count": impact.get("on_time_count", 0),
        "on_time_delivery_pct": impact.get("on_time_delivery_pct", 0.0),
    }


