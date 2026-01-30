"""
Cost projection service for analytics.

Provides algorithms for projecting month-end costs based on current usage patterns.
"""
from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


@dataclass
class CostProjection:
    """Result of a cost projection calculation.

    Attributes:
        month_to_date: Actual cost incurred so far this month.
        projected_total: Projected total cost for the full month (None if cannot project).
        daily_average: Average daily cost based on current data.
        days_elapsed: Number of days elapsed in current month.
        days_in_month: Total number of days in current month.
        confidence: Confidence level of projection ('low', 'medium', 'high').
        can_project: Whether a meaningful projection can be made.
    """
    month_to_date: Decimal
    projected_total: Optional[Decimal]
    daily_average: Decimal
    days_elapsed: int
    days_in_month: int
    confidence: str
    can_project: bool


class CostProjectionService:
    """Service for calculating cost projections.

    Uses a simple linear projection algorithm:
    projected_total = (month_to_date / days_elapsed) * days_in_month

    Confidence levels are based on percentage of month elapsed:
    - Low: < 25% of month elapsed
    - Medium: 25-75% of month elapsed
    - High: > 75% of month elapsed
    """

    def project_cost(
        self,
        month_to_date: Decimal,
        current_date: Optional[datetime] = None,
    ) -> CostProjection:
        """Calculate projected month-end cost.

        Args:
            month_to_date: Total cost incurred so far this month.
            current_date: Date to use for calculation (defaults to now).

        Returns:
            CostProjection with calculated values.
        """
        if current_date is None:
            current_date = datetime.now(timezone.utc)

        days_elapsed = current_date.day
        days_in_month = monthrange(current_date.year, current_date.month)[1]

        # Cannot project on first day - insufficient data
        if days_elapsed <= 1:
            return CostProjection(
                month_to_date=month_to_date,
                projected_total=None,
                daily_average=month_to_date,
                days_elapsed=days_elapsed,
                days_in_month=days_in_month,
                confidence='low',
                can_project=False,
            )

        # Calculate daily average
        daily_average = month_to_date / days_elapsed
        daily_average = daily_average.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Calculate projection
        projected_total = (month_to_date / days_elapsed) * days_in_month
        projected_total = projected_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Calculate confidence based on percentage of month elapsed
        pct_elapsed = days_elapsed / days_in_month
        if pct_elapsed >= 0.75:
            confidence = 'high'
        elif pct_elapsed >= 0.25:
            confidence = 'medium'
        else:
            confidence = 'low'

        return CostProjection(
            month_to_date=month_to_date,
            projected_total=projected_total,
            daily_average=daily_average,
            days_elapsed=days_elapsed,
            days_in_month=days_in_month,
            confidence=confidence,
            can_project=True,
        )
