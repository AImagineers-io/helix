"""
Consent Management Service.

Provides:
- Record consent
- Update preferences
- Withdraw consent
- Consent history
- Policy version tracking

Consent types:
- ESSENTIAL: Required for operation
- FUNCTIONAL: Enhanced features
- ANALYTICS: Usage analytics
- MARKETING: Marketing communications
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ConsentType(Enum):
    """Types of consent."""
    ESSENTIAL = "essential"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    MARKETING = "marketing"


@dataclass
class ConsentRecord:
    """A consent record."""
    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: str = "1.0"
    source: str = "web"  # web, app, api
    ip_address: Optional[str] = None


class ConsentService:
    """
    Service for managing user consent records.

    Tracks consent grants and withdrawals with full
    history for compliance purposes.
    """

    def __init__(self):
        """Initialize consent service."""
        # user_id -> consent_type -> list of records
        self._consents: dict[str, dict[ConsentType, list[ConsentRecord]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        policy_version: str = "1.0",
        source: str = "web",
        ip_address: Optional[str] = None
    ) -> ConsentRecord:
        """
        Record a consent decision.

        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent is granted
            policy_version: Version of privacy policy
            source: Source of consent
            ip_address: IP address if available

        Returns:
            ConsentRecord: Created record
        """
        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            policy_version=policy_version,
            source=source,
            ip_address=ip_address
        )

        self._consents[user_id][consent_type].append(record)
        return record

    def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        source: str = "web"
    ) -> ConsentRecord:
        """
        Withdraw consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent
            source: Source of withdrawal

        Returns:
            ConsentRecord: Withdrawal record
        """
        return self.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=False,
            source=source
        )

    def get_consent_status(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> ConsentRecord:
        """
        Get current consent status.

        Args:
            user_id: User identifier
            consent_type: Type of consent

        Returns:
            ConsentRecord: Latest consent record
        """
        records = self._consents[user_id][consent_type]

        if not records:
            # No consent recorded, return default (not granted)
            return ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=False
            )

        # Return most recent
        return max(records, key=lambda r: r.timestamp)

    def get_consent_history(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> list[ConsentRecord]:
        """
        Get consent history for user and type.

        Args:
            user_id: User identifier
            consent_type: Type of consent

        Returns:
            list[ConsentRecord]: History (newest first)
        """
        records = self._consents[user_id][consent_type]
        return sorted(records, key=lambda r: r.timestamp, reverse=True)

    def get_all_consents(self, user_id: str) -> list[ConsentRecord]:
        """
        Get all consent records for user.

        Args:
            user_id: User identifier

        Returns:
            list[ConsentRecord]: All consent records
        """
        all_records = []
        for consent_type in ConsentType:
            all_records.extend(self._consents[user_id][consent_type])

        return sorted(all_records, key=lambda r: r.timestamp, reverse=True)

    def get_current_consents(self, user_id: str) -> list[ConsentRecord]:
        """
        Get current (latest) consent for each type.

        Args:
            user_id: User identifier

        Returns:
            list[ConsentRecord]: Latest consent per type
        """
        current = []
        for consent_type in ConsentType:
            records = self._consents[user_id][consent_type]
            if records:
                current.append(max(records, key=lambda r: r.timestamp))

        return current

    def has_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has granted consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent

        Returns:
            bool: True if consent granted
        """
        status = self.get_consent_status(user_id, consent_type)
        return status.granted


# Global service instance
_consent_service: Optional[ConsentService] = None


def _get_consent_service() -> ConsentService:
    """Get or create global consent service."""
    global _consent_service

    if _consent_service is None:
        _consent_service = ConsentService()

    return _consent_service


def record_consent(
    user_id: str,
    consent_type: ConsentType,
    granted: bool,
    policy_version: str = "1.0"
) -> ConsentRecord:
    """
    Convenience function to record consent.

    Args:
        user_id: User identifier
        consent_type: Type of consent
        granted: Whether granted
        policy_version: Policy version

    Returns:
        ConsentRecord: Created record
    """
    return _get_consent_service().record_consent(
        user_id=user_id,
        consent_type=consent_type,
        granted=granted,
        policy_version=policy_version
    )


def withdraw_consent(
    user_id: str,
    consent_type: ConsentType
) -> ConsentRecord:
    """
    Convenience function to withdraw consent.

    Args:
        user_id: User identifier
        consent_type: Type of consent

    Returns:
        ConsentRecord: Withdrawal record
    """
    return _get_consent_service().withdraw_consent(user_id, consent_type)


def get_consent_status(
    user_id: str,
    consent_type: ConsentType
) -> ConsentRecord:
    """
    Convenience function to get consent status.

    Args:
        user_id: User identifier
        consent_type: Type of consent

    Returns:
        ConsentRecord: Current status
    """
    return _get_consent_service().get_consent_status(user_id, consent_type)
