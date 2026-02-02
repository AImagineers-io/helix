"""
Data Subject Access Request (DSAR) Service.

Provides:
- Export user data
- Data anonymization
- Data deletion
- Request tracking

Supports GDPR Article 15-17 rights:
- Right of access
- Right to erasure
- Right to data portability
"""
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DSARType(Enum):
    """Types of DSAR requests."""
    ACCESS = "access"  # Right to access
    DELETION = "deletion"  # Right to erasure
    RECTIFICATION = "rectification"  # Right to correct
    PORTABILITY = "portability"  # Right to export


class DSARStatus(Enum):
    """Status of DSAR request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class DSARRequest:
    """A DSAR request."""
    user_id: str
    request_type: DSARType
    email: str
    request_id: str = field(default_factory=lambda: f"dsar_{uuid.uuid4().hex[:12]}")
    status: DSARStatus = DSARStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    notes: str = ""


@dataclass
class ProcessingResult:
    """Result of DSAR processing."""
    success: bool
    message: str = ""
    data: Optional[dict] = None


class DSARService:
    """
    Service for handling Data Subject Access Requests.

    Manages the lifecycle of DSAR requests including
    data export, anonymization, and deletion.
    """

    def __init__(self):
        """Initialize DSAR service."""
        self._requests: dict[str, DSARRequest] = {}
        self._user_data: dict[str, dict[str, Any]] = defaultdict(dict)

    def create_request(
        self,
        user_id: str,
        request_type: DSARType,
        email: str,
        notes: str = ""
    ) -> DSARRequest:
        """
        Create a DSAR request.

        Args:
            user_id: User identifier
            request_type: Type of request
            email: Contact email
            notes: Optional notes

        Returns:
            DSARRequest: Created request
        """
        request = DSARRequest(
            user_id=user_id,
            request_type=request_type,
            email=email,
            notes=notes
        )

        self._requests[request.request_id] = request
        return request

    def get_request(self, request_id: str) -> Optional[DSARRequest]:
        """
        Get request by ID.

        Args:
            request_id: Request identifier

        Returns:
            Optional[DSARRequest]: Request if found
        """
        return self._requests.get(request_id)

    def update_status(
        self,
        request_id: str,
        status: DSARStatus,
        notes: str = ""
    ) -> None:
        """
        Update request status.

        Args:
            request_id: Request identifier
            status: New status
            notes: Optional notes
        """
        request = self._requests.get(request_id)
        if request:
            request.status = status
            if notes:
                request.notes = notes
            if status == DSARStatus.COMPLETED:
                request.completed_at = datetime.now(timezone.utc)

    def list_requests(
        self,
        status: Optional[DSARStatus] = None,
        user_id: Optional[str] = None
    ) -> list[DSARRequest]:
        """
        List DSAR requests.

        Args:
            status: Filter by status
            user_id: Filter by user

        Returns:
            list[DSARRequest]: Matching requests
        """
        requests = list(self._requests.values())

        if status:
            requests = [r for r in requests if r.status == status]

        if user_id:
            requests = [r for r in requests if r.user_id == user_id]

        return sorted(requests, key=lambda r: r.created_at, reverse=True)

    def add_user_data(
        self,
        user_id: str,
        data_type: str,
        data: Any
    ) -> None:
        """
        Add user data (for testing/mocking).

        Args:
            user_id: User identifier
            data_type: Type of data
            data: Data to store
        """
        self._user_data[user_id][data_type] = data

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        """
        Export all data for a user.

        Args:
            user_id: User identifier

        Returns:
            dict: User data export
        """
        export = {
            "user_id": user_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add all stored data
        user_data = self._user_data.get(user_id, {})
        for data_type, data in user_data.items():
            export[data_type] = data

        return export

    def delete_user_data(self, user_id: str) -> ProcessingResult:
        """
        Delete all data for a user.

        Args:
            user_id: User identifier

        Returns:
            ProcessingResult: Deletion result
        """
        if user_id in self._user_data:
            del self._user_data[user_id]

        return ProcessingResult(
            success=True,
            message=f"Deleted all data for user {user_id}"
        )

    def anonymize_user_data(self, user_id: str) -> ProcessingResult:
        """
        Anonymize PII for a user.

        Args:
            user_id: User identifier

        Returns:
            ProcessingResult: Anonymization result
        """
        user_data = self._user_data.get(user_id, {})

        # Anonymize known PII fields
        pii_fields = ["name", "email", "phone", "address", "ssn"]

        for data_type, data in user_data.items():
            if isinstance(data, dict):
                for field in pii_fields:
                    if field in data:
                        data[field] = "[ANONYMIZED]"
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for field in pii_fields:
                            if field in item:
                                item[field] = "[ANONYMIZED]"

        return ProcessingResult(
            success=True,
            message=f"Anonymized PII for user {user_id}"
        )

    def process_request(self, request_id: str) -> ProcessingResult:
        """
        Process a DSAR request.

        Args:
            request_id: Request identifier

        Returns:
            ProcessingResult: Processing result
        """
        request = self.get_request(request_id)
        if not request:
            return ProcessingResult(
                success=False,
                message=f"Request not found: {request_id}"
            )

        self.update_status(request_id, DSARStatus.PROCESSING)

        if request.request_type == DSARType.ACCESS:
            data = self.export_user_data(request.user_id)
            result = ProcessingResult(success=True, data=data)

        elif request.request_type == DSARType.DELETION:
            result = self.delete_user_data(request.user_id)

        elif request.request_type == DSARType.PORTABILITY:
            data = self.export_user_data(request.user_id)
            result = ProcessingResult(success=True, data=data)

        else:
            result = ProcessingResult(
                success=False,
                message=f"Unsupported request type: {request.request_type}"
            )

        if result.success:
            self.update_status(request_id, DSARStatus.COMPLETED)
        else:
            self.update_status(request_id, DSARStatus.REJECTED, result.message)

        return result


# Global service instance
_dsar_service: Optional[DSARService] = None


def _get_dsar_service() -> DSARService:
    """Get or create global DSAR service."""
    global _dsar_service

    if _dsar_service is None:
        _dsar_service = DSARService()

    return _dsar_service


def create_dsar_request(
    user_id: str,
    request_type: DSARType,
    email: str
) -> DSARRequest:
    """
    Convenience function to create DSAR request.

    Args:
        user_id: User identifier
        request_type: Type of request
        email: Contact email

    Returns:
        DSARRequest: Created request
    """
    return _get_dsar_service().create_request(user_id, request_type, email)


def process_dsar_request(request_id: str) -> ProcessingResult:
    """
    Convenience function to process DSAR request.

    Args:
        request_id: Request identifier

    Returns:
        ProcessingResult: Processing result
    """
    return _get_dsar_service().process_request(request_id)
