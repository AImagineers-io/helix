"""
Integration tests for Consent Management (P12.8.1)

Tests consent management including:
- Record consent
- Update preferences
- Withdrawal
- Consent history
"""
import pytest
from datetime import datetime, timezone

from services.consent_service import (
    ConsentType,
    ConsentRecord,
    ConsentService,
    record_consent,
    withdraw_consent,
    get_consent_status,
)


class TestConsentType:
    """Tests for consent types."""

    def test_consent_types(self):
        """Should have expected consent types."""
        assert ConsentType.ANALYTICS is not None
        assert ConsentType.MARKETING is not None
        assert ConsentType.FUNCTIONAL is not None
        assert ConsentType.ESSENTIAL is not None


class TestConsentRecord:
    """Tests for ConsentRecord model."""

    def test_record_has_timestamp(self):
        """Record should have timestamp."""
        record = ConsentRecord(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
            granted=True
        )

        assert record.timestamp is not None

    def test_record_has_version(self):
        """Record should have policy version."""
        record = ConsentRecord(
            user_id="user456",
            consent_type=ConsentType.MARKETING,
            granted=True,
            policy_version="1.0"
        )

        assert record.policy_version == "1.0"


class TestConsentService:
    """Tests for ConsentService class."""

    @pytest.fixture
    def service(self):
        """Create consent service."""
        return ConsentService()

    def test_record_consent(self, service):
        """Should record consent."""
        record = service.record_consent(
            user_id="user1",
            consent_type=ConsentType.ANALYTICS,
            granted=True
        )

        assert record.user_id == "user1"
        assert record.granted is True

    def test_get_consent_status(self, service):
        """Should get consent status."""
        service.record_consent("user2", ConsentType.MARKETING, True)

        status = service.get_consent_status("user2", ConsentType.MARKETING)

        assert status.granted is True

    def test_withdraw_consent(self, service):
        """Should withdraw consent."""
        service.record_consent("user3", ConsentType.ANALYTICS, True)
        service.withdraw_consent("user3", ConsentType.ANALYTICS)

        status = service.get_consent_status("user3", ConsentType.ANALYTICS)

        assert status.granted is False

    def test_update_preferences(self, service):
        """Should update consent preferences."""
        service.record_consent("user4", ConsentType.ANALYTICS, True)
        service.record_consent("user4", ConsentType.ANALYTICS, False)

        status = service.get_consent_status("user4", ConsentType.ANALYTICS)

        assert status.granted is False


class TestConsentHistory:
    """Tests for consent history."""

    @pytest.fixture
    def service(self):
        return ConsentService()

    def test_tracks_history(self, service):
        """Should track consent history."""
        service.record_consent("user5", ConsentType.MARKETING, True)
        service.record_consent("user5", ConsentType.MARKETING, False)
        service.record_consent("user5", ConsentType.MARKETING, True)

        history = service.get_consent_history("user5", ConsentType.MARKETING)

        assert len(history) == 3

    def test_history_ordered_by_time(self, service):
        """History should be ordered by time."""
        service.record_consent("user6", ConsentType.ANALYTICS, True)
        service.record_consent("user6", ConsentType.ANALYTICS, False)

        history = service.get_consent_history("user6", ConsentType.ANALYTICS)

        # Most recent first
        assert history[0].timestamp >= history[1].timestamp


class TestAllUserConsents:
    """Tests for getting all consents for a user."""

    @pytest.fixture
    def service(self):
        return ConsentService()

    def test_get_all_consents(self, service):
        """Should get all consents for user."""
        service.record_consent("user7", ConsentType.ANALYTICS, True)
        service.record_consent("user7", ConsentType.MARKETING, False)
        service.record_consent("user7", ConsentType.FUNCTIONAL, True)

        consents = service.get_all_consents("user7")

        assert len(consents) >= 3

    def test_returns_latest_per_type(self, service):
        """Should return latest consent per type."""
        service.record_consent("user8", ConsentType.ANALYTICS, True)
        service.record_consent("user8", ConsentType.ANALYTICS, False)

        consents = service.get_current_consents("user8")

        # Should have one entry for ANALYTICS
        analytics_consents = [c for c in consents if c.consent_type == ConsentType.ANALYTICS]
        assert len(analytics_consents) == 1
        assert analytics_consents[0].granted is False


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_record_consent_function(self):
        """Should record consent via function."""
        record = record_consent(
            user_id="func_user1",
            consent_type=ConsentType.ANALYTICS,
            granted=True
        )

        assert record.granted is True

    def test_withdraw_consent_function(self):
        """Should withdraw consent via function."""
        record_consent("func_user2", ConsentType.MARKETING, True)
        withdraw_consent("func_user2", ConsentType.MARKETING)

        status = get_consent_status("func_user2", ConsentType.MARKETING)
        assert status.granted is False


class TestPolicyVersion:
    """Tests for policy version tracking."""

    @pytest.fixture
    def service(self):
        return ConsentService()

    def test_stores_policy_version(self, service):
        """Should store policy version with consent."""
        record = service.record_consent(
            user_id="user9",
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            policy_version="2.0"
        )

        assert record.policy_version == "2.0"

    def test_tracks_policy_changes(self, service):
        """Should track when user consents to new version."""
        service.record_consent("user10", ConsentType.ANALYTICS, True, "1.0")
        service.record_consent("user10", ConsentType.ANALYTICS, True, "2.0")

        history = service.get_consent_history("user10", ConsentType.ANALYTICS)

        versions = [h.policy_version for h in history]
        assert "1.0" in versions
        assert "2.0" in versions
