"""Analytics service for dashboard statistics.

Provides summary statistics for:
- QA pair counts (total, active, draft, pending)
- Conversation metrics (daily, weekly, monthly)
- Cost tracking (current and projected costs by provider)

Architecture Note:
    This service queries DailyAggregate for pre-computed analytics.
    QA stats are fetched directly from the database.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, TypedDict

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import DailyAggregate


class QAStatistics(TypedDict):
    """QA pair statistics structure."""

    total: int
    active: int
    draft: int
    pending: int


class ConversationStatistics(TypedDict):
    """Conversation count statistics structure."""

    total: int
    today: int
    this_week: int
    this_month: int


class ProviderCostBreakdown(TypedDict):
    """Cost breakdown by LLM provider."""

    openai: float
    anthropic: float


class CostSummaryData(TypedDict):
    """Cost summary statistics structure."""

    current_month: float
    projected_month_end: float
    by_provider: ProviderCostBreakdown


class AnalyticsSummary(TypedDict):
    """Complete analytics summary structure."""

    qa_stats: QAStatistics
    conversation_stats: ConversationStatistics
    cost_summary: CostSummaryData


class AnalyticsService:
    """Service for aggregating analytics data across the platform.

    Responsibilities:
        - Aggregate QA pair statistics by status
        - Calculate conversation counts for different time periods
        - Summarize costs with projections and provider breakdown
    """

    def __init__(self, db: Session) -> None:
        """Initialize analytics service.

        Args:
            db: SQLAlchemy database session for querying analytics data.
        """
        self.db = db

    def get_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AnalyticsSummary:
        """Get complete analytics summary for admin dashboard.

        Args:
            start_date: Start of date range filter (inclusive).
            end_date: End of date range filter (inclusive).

        Returns:
            Analytics summary containing QA stats, conversation metrics, and costs.
        """
        # Default to last 30 days if not specified
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        return {
            "qa_stats": self._get_qa_stats(),
            "conversation_stats": self._get_conversation_stats(start_date, end_date),
            "cost_summary": self._get_cost_summary(start_date, end_date),
        }

    def _get_qa_stats(self) -> QAStatistics:
        """Calculate QA pair statistics grouped by status.

        Returns:
            QA statistics with counts for total, active, draft, and pending pairs.

        TODO:
            Implement actual queries when QAPair model is migrated:
            - Query db.query(QAPair).filter_by(status='active').count()
            - Aggregate counts for each status
        """
        return {
            "total": 0,
            "active": 0,
            "draft": 0,
            "pending": 0,
        }

    def _get_conversation_stats(
        self,
        start_date: date,
        end_date: date,
    ) -> ConversationStatistics:
        """Calculate conversation count statistics for date range.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            Conversation counts for the date range.
        """
        # Query aggregates for date range
        total = self.db.query(func.sum(DailyAggregate.conversation_count)).filter(
            DailyAggregate.date >= start_date,
            DailyAggregate.date <= end_date
        ).scalar() or 0

        # Get today's count
        today = date.today()
        today_agg = self.db.query(DailyAggregate).filter(
            DailyAggregate.date == today
        ).first()
        today_count = today_agg.conversation_count if today_agg else 0

        # Get this week's count (Monday to today)
        week_start = today - timedelta(days=today.weekday())
        week_count = self.db.query(func.sum(DailyAggregate.conversation_count)).filter(
            DailyAggregate.date >= week_start,
            DailyAggregate.date <= today
        ).scalar() or 0

        # Get this month's count
        month_start = today.replace(day=1)
        month_count = self.db.query(func.sum(DailyAggregate.conversation_count)).filter(
            DailyAggregate.date >= month_start,
            DailyAggregate.date <= today
        ).scalar() or 0

        return {
            "total": int(total),
            "today": int(today_count),
            "this_week": int(week_count),
            "this_month": int(month_count),
        }

    def _get_cost_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> CostSummaryData:
        """Calculate cost summary with projections.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            Cost summary with current month spend and projection.
        """
        today = date.today()
        month_start = today.replace(day=1)

        # Get current month total from aggregates
        current_month_total = self.db.query(func.sum(DailyAggregate.cost_total)).filter(
            DailyAggregate.date >= month_start,
            DailyAggregate.date <= today
        ).scalar() or Decimal('0.00')

        current_month = float(current_month_total)

        # Calculate projection
        from services.cost_service import CostProjectionService
        projection_service = CostProjectionService()
        projection = projection_service.project_cost(Decimal(str(current_month)))

        projected = float(projection.projected_total) if projection.can_project else 0.0

        return {
            "current_month": current_month,
            "projected_month_end": projected,
            "by_provider": {
                "openai": 0.0,  # TODO: Add provider breakdown when available
                "anthropic": 0.0,
            },
        }
