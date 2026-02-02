"""
Data Retention Service for enforcing retention policies.

Provides:
- Configurable retention policies per data type
- Scheduled deletion execution
- Dry run support
- Audit logging of deletions

Default policies:
- Conversations: 30 days
- Logs: 90 days
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


@dataclass
class RetentionPolicy:
    """Retention policy for a data type."""
    data_type: str
    retention_days: int = 30
    enabled: bool = True


@dataclass
class RetentionConfig:
    """Configuration for data retention."""
    policies: list[RetentionPolicy] = field(default_factory=list)
    default_retention_days: int = 30
    schedule_cron: str = "0 2 * * *"  # Daily at 2 AM

    def get_policy(self, data_type: str) -> RetentionPolicy:
        """
        Get policy for data type.

        Args:
            data_type: Type of data

        Returns:
            RetentionPolicy: Policy for data type or default
        """
        for policy in self.policies:
            if policy.data_type == data_type:
                return policy

        return RetentionPolicy(
            data_type=data_type,
            retention_days=self.default_retention_days
        )


@dataclass
class RetentionAction:
    """Record of a retention action."""
    data_type: str
    record_count: int
    timestamp: datetime
    record_ids: list[Any] = field(default_factory=list)


@dataclass
class RetentionResult:
    """Result of retention execution."""
    data_type: str
    would_delete: int
    actually_deleted: int
    dry_run: bool
    errors: list[str] = field(default_factory=list)


def get_retention_cutoff_date(policy: RetentionPolicy) -> datetime:
    """
    Calculate cutoff date for retention policy.

    Records older than this date should be deleted.

    Args:
        policy: Retention policy

    Returns:
        datetime: Cutoff date
    """
    return datetime.now(timezone.utc) - timedelta(days=policy.retention_days)


def is_record_expired(
    created_at: datetime,
    policy: RetentionPolicy
) -> bool:
    """
    Check if record is expired based on policy.

    Args:
        created_at: Record creation timestamp
        policy: Retention policy

    Returns:
        bool: True if record should be deleted
    """
    cutoff = get_retention_cutoff_date(policy)

    # Ensure timezone-aware comparison
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # Record must be strictly older than cutoff
    return created_at < cutoff


class DataRetentionService:
    """
    Service for enforcing data retention policies.

    Identifies and deletes records that exceed their
    retention period. Supports dry run mode for testing.
    """

    def __init__(self, config: Optional[RetentionConfig] = None):
        """
        Initialize retention service.

        Args:
            config: Retention configuration
        """
        self.config = config or RetentionConfig()
        self._last_run: Optional[datetime] = None

    def find_expired_records(
        self,
        records: list[dict],
        data_type: str
    ) -> list[dict]:
        """
        Find records that exceed retention period.

        Args:
            records: List of records with 'created_at' field
            data_type: Type of data

        Returns:
            list[dict]: Records that should be deleted
        """
        policy = self.config.get_policy(data_type)

        if not policy.enabled:
            return []

        expired = []
        for record in records:
            created_at = record.get("created_at")
            if created_at and is_record_expired(created_at, policy):
                expired.append(record)

        return expired

    def create_retention_action(
        self,
        data_type: str,
        records: list[dict]
    ) -> RetentionAction:
        """
        Create retention action for records.

        Args:
            data_type: Type of data
            records: Records to delete

        Returns:
            RetentionAction: Action record
        """
        record_ids = [r.get("id") for r in records if r.get("id")]

        return RetentionAction(
            data_type=data_type,
            record_count=len(records),
            timestamp=datetime.now(timezone.utc),
            record_ids=record_ids
        )

    def create_audit_log(self, action: RetentionAction) -> dict:
        """
        Create audit log entry for retention action.

        Args:
            action: Retention action

        Returns:
            dict: Audit log entry
        """
        return {
            "action": "data_retention_delete",
            "data_type": action.data_type,
            "record_count": action.record_count,
            "timestamp": action.timestamp.isoformat(),
            "record_ids": action.record_ids,
        }

    def execute_retention(
        self,
        data_type: str,
        records: list[dict],
        dry_run: bool = False
    ) -> RetentionResult:
        """
        Execute retention for data type.

        Args:
            data_type: Type of data
            records: Records to evaluate
            dry_run: If True, don't actually delete

        Returns:
            RetentionResult: Execution result
        """
        expired = self.find_expired_records(records, data_type)

        result = RetentionResult(
            data_type=data_type,
            would_delete=len(expired),
            actually_deleted=0,
            dry_run=dry_run
        )

        if dry_run:
            return result

        # In real implementation, would delete from database
        # For now, just track the count
        result.actually_deleted = len(expired)

        # Record last run
        self._last_run = datetime.now(timezone.utc)

        return result

    def get_next_scheduled_run(self) -> datetime:
        """
        Get next scheduled retention run time.

        Returns:
            datetime: Next run time
        """
        # Simple implementation: next run is tomorrow at 2 AM
        now = datetime.now(timezone.utc)
        tomorrow = now.replace(hour=2, minute=0, second=0, microsecond=0)

        if tomorrow <= now:
            tomorrow += timedelta(days=1)

        return tomorrow

    def is_retention_due(self) -> bool:
        """
        Check if retention should run.

        Returns:
            bool: True if retention is due
        """
        if self._last_run is None:
            return True

        # Run daily
        hours_since = (datetime.now(timezone.utc) - self._last_run).total_seconds() / 3600
        return hours_since >= 24
