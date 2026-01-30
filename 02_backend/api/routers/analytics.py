"""Analytics API router.

Provides REST endpoints for dashboard analytics:
- GET /analytics/summary - Get summary statistics for dashboard
- GET /analytics/export - Export analytics data as CSV
"""
import csv
import io
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import DailyAggregate
from services.analytics_service import AnalyticsService
from api.auth import verify_api_key
from api.schemas.analytics import AnalyticsSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(verify_api_key)],
)


def parse_date(date_str: str) -> date:
    """Parse ISO date string to date object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {date_str}")


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get analytics summary",
    description="Get summary statistics for admin dashboard including QA stats, conversations, and costs.",
)
def get_analytics_summary(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(
        None,
        description="Start date (YYYY-MM-DD). Defaults to 30 days ago.",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date (YYYY-MM-DD). Defaults to today.",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
):
    """Get analytics summary for dashboard.

    Args:
        db: Database session.
        start_date: Filter start date (inclusive).
        end_date: Filter end date (inclusive).

    Returns:
        Analytics summary with QA stats, conversation stats, and cost summary.
    """
    # Parse and validate dates
    if end_date:
        end_dt = parse_date(end_date)
    else:
        end_dt = date.today()

    if start_date:
        start_dt = parse_date(start_date)
    else:
        start_dt = end_dt - timedelta(days=30)

    # Validate date range
    if start_dt > end_dt:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )

    service = AnalyticsService(db)
    summary = service.get_summary(start_date=start_dt, end_date=end_dt)
    return summary


@router.get(
    "/export",
    summary="Export analytics data",
    description="Export daily analytics data as CSV.",
)
def export_analytics(
    db: Session = Depends(get_db),
    start_date: str = Query(
        ...,
        description="Start date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: str = Query(
        ...,
        description="End date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
    format: str = Query(
        "csv",
        description="Export format (csv)",
        pattern=r"^csv$"
    ),
):
    """Export analytics data as CSV.

    Args:
        db: Database session.
        start_date: Filter start date (inclusive).
        end_date: Filter end date (inclusive).
        format: Export format (only 'csv' supported).

    Returns:
        CSV file with daily analytics data.
    """
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    if start_dt > end_dt:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )

    # Query aggregates
    aggregates = db.query(DailyAggregate).filter(
        DailyAggregate.date >= start_dt,
        DailyAggregate.date <= end_dt
    ).order_by(DailyAggregate.date).all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'date',
        'conversations',
        'messages',
        'avg_response_time_ms',
        'cost_total'
    ])

    # Write data rows
    for agg in aggregates:
        writer.writerow([
            agg.date.isoformat(),
            agg.conversation_count,
            agg.message_count,
            agg.avg_response_time_ms or '',
            float(agg.cost_total) if agg.cost_total else 0.0
        ])

    output.seek(0)

    # Return as streaming response
    filename = f"analytics_{start_date}_to_{end_date}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
