"""
Data Access Audit Service.

Provides:
- Track who accessed what data
- Track when data was accessed
- Configurable retention
- Query capabilities

Tracks:
- User who accessed
- Data type accessed
- Record ID
- Access type (read, write, delete, export)
- Timestamp
- IP address
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DataAccessType(Enum):
    """Types of data access."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXPORT = "export"


@dataclass
class DataAccessLog:
    """A data access log entry."""
    user_id: str
    data_type: str
    access_type: DataAccessType
    record_id: str
    log_id: str = field(default_factory=lambda: f"log_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


class DataAuditService:
    """
    Service for tracking data access.

    Maintains audit trail of who accessed what data and when.
    """

    def __init__(self, retention_days: int = 365):
        """
        Initialize audit service.

        Args:
            retention_days: How long to retain logs
        """
        self.retention_days = retention_days
        self._logs: list[DataAccessLog] = []

    def log_access(
        self,
        user_id: str,
        data_type: str,
        access_type: DataAccessType,
        record_id: str,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None
    ) -> DataAccessLog:
        """
        Log a data access event.

        Args:
            user_id: User who accessed data
            data_type: Type of data accessed
            access_type: Type of access
            record_id: ID of record accessed
            ip_address: Source IP address
            details: Additional details

        Returns:
            DataAccessLog: Created log entry
        """
        log = DataAccessLog(
            user_id=user_id,
            data_type=data_type,
            access_type=access_type,
            record_id=record_id,
            ip_address=ip_address,
            details=details or {}
        )

        self._logs.append(log)
        return log

    def get_access_by_user(self, user_id: str) -> list[DataAccessLog]:
        """
        Get access logs for a user.

        Args:
            user_id: User identifier

        Returns:
            list[DataAccessLog]: User's access logs
        """
        return [log for log in self._logs if log.user_id == user_id]

    def get_access_by_record(self, record_id: str) -> list[DataAccessLog]:
        """
        Get access logs for a record.

        Args:
            record_id: Record identifier

        Returns:
            list[DataAccessLog]: Record's access logs
        """
        return [log for log in self._logs if log.record_id == record_id]

    def get_recent_access(self, limit: int = 100) -> list[DataAccessLog]:
        """
        Get recent access logs.

        Args:
            limit: Maximum logs to return

        Returns:
            list[DataAccessLog]: Recent logs
        """
        return sorted(
            self._logs,
            key=lambda log: log.timestamp,
            reverse=True
        )[:limit]

    def get_by_access_type(
        self,
        access_type: DataAccessType
    ) -> list[DataAccessLog]:
        """
        Get logs by access type.

        Args:
            access_type: Type of access

        Returns:
            list[DataAccessLog]: Matching logs
        """
        return [log for log in self._logs if log.access_type == access_type]

    def get_by_data_type(self, data_type: str) -> list[DataAccessLog]:
        """
        Get logs by data type.

        Args:
            data_type: Type of data

        Returns:
            list[DataAccessLog]: Matching logs
        """
        return [log for log in self._logs if log.data_type == data_type]

    def get_total_count(self) -> int:
        """
        Get total log count.

        Returns:
            int: Total number of logs
        """
        return len(self._logs)

    def export_logs(self) -> list[dict]:
        """
        Export all logs.

        Returns:
            list[dict]: Logs as dictionaries
        """
        return [
            {
                "log_id": log.log_id,
                "user_id": log.user_id,
                "data_type": log.data_type,
                "access_type": log.access_type.value,
                "record_id": log.record_id,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
                "details": log.details,
            }
            for log in self._logs
        ]


# Global service instance
_audit_service: Optional[DataAuditService] = None


def _get_audit_service() -> DataAuditService:
    """Get or create global audit service."""
    global _audit_service

    if _audit_service is None:
        _audit_service = DataAuditService()

    return _audit_service


def log_data_access(
    user_id: str,
    data_type: str,
    access_type: DataAccessType,
    record_id: str,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None
) -> DataAccessLog:
    """
    Convenience function to log data access.

    Args:
        user_id: User who accessed
        data_type: Type of data
        access_type: Type of access
        record_id: Record ID
        ip_address: Source IP
        details: Additional details

    Returns:
        DataAccessLog: Created log
    """
    return _get_audit_service().log_access(
        user_id=user_id,
        data_type=data_type,
        access_type=access_type,
        record_id=record_id,
        ip_address=ip_address,
        details=details
    )


def get_access_history(
    user_id: Optional[str] = None,
    record_id: Optional[str] = None,
    limit: int = 100
) -> list[DataAccessLog]:
    """
    Convenience function to get access history.

    Args:
        user_id: Filter by user
        record_id: Filter by record
        limit: Maximum results

    Returns:
        list[DataAccessLog]: Access history
    """
    service = _get_audit_service()

    if user_id:
        return service.get_access_by_user(user_id)[:limit]

    if record_id:
        return service.get_access_by_record(record_id)[:limit]

    return service.get_recent_access(limit)
