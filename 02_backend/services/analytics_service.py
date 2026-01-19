"""Analytics service for dashboard statistics.

Provides summary statistics for:
- QA pair counts (total, active, draft, pending)
- Conversation metrics (daily, weekly, monthly)
- Cost tracking (current and projected costs by provider)

Architecture Note:
    This service currently returns zero/mock data as the full PALAI database
    models (QAPair, Conversation, CostRecord) have not yet been migrated to Helix.
    Once those models are available, this service will be updated to query actual data.

Reference:
    PALAI patterns from:
    - backend/api/routers/observability.py (analytics patterns)
    - backend/api/routers/costs.py (cost tracking)
"""
from typing import TypedDict

from sqlalchemy.orm import Session


class QAStatistics(TypedDict):
    """QA pair statistics structure."""

    total: int
    active: int
    draft: int
    pending: int


class ConversationStatistics(TypedDict):
    """Conversation count statistics structure."""

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

    def get_summary(self) -> AnalyticsSummary:
        """Get complete analytics summary for admin dashboard.

        Returns:
            Analytics summary containing QA stats, conversation metrics, and costs.

        Example:
            >>> service = AnalyticsService(db)
            >>> summary = service.get_summary()
            >>> summary["qa_stats"]["total"]
            0
        """
        return {
            "qa_stats": self._get_qa_stats(),
            "conversation_stats": self._get_conversation_stats(),
            "cost_summary": self._get_cost_summary(),
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

    def _get_conversation_stats(self) -> ConversationStatistics:
        """Calculate conversation count statistics for time periods.

        Returns:
            Conversation counts for today, this week, and this month.

        TODO:
            Implement actual queries when Conversation model is migrated:
            - Query conversations created today (start of day to now)
            - Query conversations this week (Monday to now)
            - Query conversations this month (1st to now)
        """
        return {
            "today": 0,
            "this_week": 0,
            "this_month": 0,
        }

    def _get_cost_summary(self) -> CostSummaryData:
        """Calculate cost summary with projections and provider breakdown.

        Returns:
            Cost summary with current month spend, projected month-end, and breakdown by provider.

        TODO:
            Implement actual queries when CostRecord model is migrated:
            - Sum costs for current month
            - Calculate daily average and project to month-end
            - Group costs by provider (OpenAI vs Anthropic)
        """
        return {
            "current_month": 0.0,
            "projected_month_end": 0.0,
            "by_provider": {
                "openai": 0.0,
                "anthropic": 0.0,
            },
        }

