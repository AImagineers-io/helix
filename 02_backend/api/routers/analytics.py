"""Analytics API router.

Provides REST endpoints for dashboard analytics:
- GET /analytics/summary - Get summary statistics for dashboard
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from services.analytics_service import AnalyticsService
from api.auth import verify_api_key
from api.schemas.analytics import AnalyticsSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get analytics summary",
    description="Get summary statistics for admin dashboard including QA stats, conversations, and costs.",
)
def get_analytics_summary(
    db: Session = Depends(get_db),
):
    """Get analytics summary for dashboard.

    Args:
        db: Database session.

    Returns:
        Analytics summary with QA stats, conversation stats, and cost summary.
    """
    service = AnalyticsService(db)
    summary = service.get_summary()
    return summary
