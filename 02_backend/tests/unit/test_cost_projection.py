"""
Unit tests for cost projection logic.

Tests the algorithm for projecting month-end costs based on current usage.
"""
import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest

# Set required environment variables BEFORE importing modules
os.environ['APP_NAME'] = 'TestApp'
os.environ['BOT_NAME'] = 'TestBot'
os.environ['DATABASE_URL'] = 'postgresql://localhost/test'

from services.cost_service import CostProjectionService, CostProjection


class TestCostProjection:
    """Test suite for cost projection calculations."""

    @pytest.fixture
    def service(self):
        """Create cost projection service instance."""
        return CostProjectionService()

    def test_project_cost_returns_projection_object(self, service):
        """Test that project_cost returns a CostProjection dataclass."""
        # Arrange
        month_to_date = Decimal('15.00')
        current_date = datetime(2025, 1, 15, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert
        assert isinstance(result, CostProjection)

    def test_project_cost_calculates_correct_projection_mid_month(self, service):
        """Test projection for mid-month (day 15 of 31-day month)."""
        # Arrange: $15 spent in first 15 days
        month_to_date = Decimal('15.00')
        current_date = datetime(2025, 1, 15, tzinfo=timezone.utc)  # Jan has 31 days

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: ($15 / 15 days) * 31 days = $31.00
        assert result.projected_total == Decimal('31.00')

    def test_project_cost_calculates_correct_projection_early_month(self, service):
        """Test projection for early month (day 5)."""
        # Arrange: $10 spent in first 5 days
        month_to_date = Decimal('10.00')
        current_date = datetime(2025, 1, 5, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: ($10 / 5 days) * 31 days = $62.00
        assert result.projected_total == Decimal('62.00')

    def test_project_cost_handles_first_day_of_month(self, service):
        """Test that first day of month returns no projection."""
        # Arrange: First day of month - no meaningful projection possible
        month_to_date = Decimal('1.00')
        current_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: No projection on first day (insufficient data)
        assert result.projected_total is None
        assert result.can_project is False

    def test_project_cost_includes_month_to_date(self, service):
        """Test that result includes month-to-date cost."""
        # Arrange
        month_to_date = Decimal('20.00')
        current_date = datetime(2025, 1, 20, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert
        assert result.month_to_date == Decimal('20.00')

    def test_project_cost_includes_days_elapsed(self, service):
        """Test that result includes number of days elapsed."""
        # Arrange
        month_to_date = Decimal('10.00')
        current_date = datetime(2025, 1, 10, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert
        assert result.days_elapsed == 10

    def test_project_cost_includes_days_in_month(self, service):
        """Test that result includes total days in month."""
        # Arrange
        month_to_date = Decimal('10.00')
        current_date = datetime(2025, 2, 10, tzinfo=timezone.utc)  # Feb 2025

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: Feb 2025 has 28 days (not a leap year)
        assert result.days_in_month == 28

    def test_project_cost_handles_leap_year_february(self, service):
        """Test that leap year February is handled correctly."""
        # Arrange
        month_to_date = Decimal('10.00')
        current_date = datetime(2024, 2, 15, tzinfo=timezone.utc)  # 2024 is leap year

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: Feb 2024 has 29 days
        assert result.days_in_month == 29

    def test_project_cost_calculates_daily_average(self, service):
        """Test that daily average is calculated correctly."""
        # Arrange
        month_to_date = Decimal('20.00')
        current_date = datetime(2025, 1, 10, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: $20 / 10 days = $2.00/day
        assert result.daily_average == Decimal('2.00')

    def test_project_cost_confidence_high_late_month(self, service):
        """Test that confidence is high when late in month."""
        # Arrange
        month_to_date = Decimal('25.00')
        current_date = datetime(2025, 1, 25, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: >75% of month elapsed = high confidence
        assert result.confidence == 'high'

    def test_project_cost_confidence_medium_mid_month(self, service):
        """Test that confidence is medium when mid-month."""
        # Arrange
        month_to_date = Decimal('15.00')
        current_date = datetime(2025, 1, 15, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: 25-75% of month elapsed = medium confidence
        assert result.confidence == 'medium'

    def test_project_cost_confidence_low_early_month(self, service):
        """Test that confidence is low when early in month."""
        # Arrange
        month_to_date = Decimal('5.00')
        current_date = datetime(2025, 1, 5, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: <25% of month elapsed = low confidence
        assert result.confidence == 'low'

    def test_project_cost_handles_zero_costs(self, service):
        """Test projection with zero costs."""
        # Arrange
        month_to_date = Decimal('0.00')
        current_date = datetime(2025, 1, 15, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert
        assert result.projected_total == Decimal('0.00')
        assert result.daily_average == Decimal('0.00')

    def test_project_cost_rounds_to_two_decimal_places(self, service):
        """Test that projection is rounded to 2 decimal places."""
        # Arrange: $10 over 7 days in a 31-day month
        # ($10 / 7) * 31 = $44.285714...
        month_to_date = Decimal('10.00')
        current_date = datetime(2025, 1, 7, tzinfo=timezone.utc)

        # Act
        result = service.project_cost(month_to_date, current_date)

        # Assert: Should be rounded to 2 decimal places
        assert result.projected_total == Decimal('44.29')
