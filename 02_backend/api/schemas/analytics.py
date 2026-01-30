"""Analytics API response schemas."""
from pydantic import BaseModel


class QAStats(BaseModel):
    """QA pair statistics."""

    total: int
    active: int
    draft: int
    pending: int


class ConversationStats(BaseModel):
    """Conversation count statistics."""

    total: int
    today: int
    this_week: int
    this_month: int


class ProviderCosts(BaseModel):
    """Cost breakdown by provider."""

    openai: float
    anthropic: float


class CostSummary(BaseModel):
    """Cost summary statistics."""

    current_month: float
    projected_month_end: float
    by_provider: ProviderCosts


class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response."""

    qa_stats: QAStats
    conversation_stats: ConversationStats
    cost_summary: CostSummary
