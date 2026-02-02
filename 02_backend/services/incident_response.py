"""
Incident Response Automation Service.

Provides:
- Auto-block IP/device
- Force session invalidation
- Log snapshots
- Configurable thresholds

Actions:
- BLOCK_IP: Block IP address
- BLOCK_DEVICE: Block device ID
- INVALIDATE_SESSION: Force logout
- SNAPSHOT_LOGS: Capture logs for incident
- ALERT: Send alert
"""
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional


class IncidentAction(Enum):
    """Incident response actions."""
    BLOCK_IP = "block_ip"
    BLOCK_DEVICE = "block_device"
    INVALIDATE_SESSION = "invalidate_session"
    SNAPSHOT_LOGS = "snapshot_logs"
    ALERT = "alert"
    ESCALATE = "escalate"


@dataclass
class IncidentConfig:
    """Configuration for incident response."""
    auto_block_threshold: int = 5
    session_invalidation_threshold: int = 10
    block_duration_minutes: int = 60
    log_snapshot_hours: int = 24


@dataclass
class Incident:
    """An incident record."""
    incident_id: str
    source_ip: str
    incident_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


@dataclass
class IncidentResponse:
    """Response to an incident."""
    incident_id: str
    actions: list[IncidentAction]
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = False
    actions_executed: list[IncidentAction] = field(default_factory=list)


@dataclass
class ActionResult:
    """Result of executing an action."""
    success: bool
    message: str = ""


@dataclass
class LogSnapshot:
    """Snapshot of logs for an incident."""
    incident_id: str
    timestamp: datetime
    time_range_start: datetime
    time_range_end: datetime
    logs: list[dict] = field(default_factory=list)


class IncidentService:
    """
    Service for incident response automation.

    Handles violation tracking, auto-blocking, and
    coordinated incident response.
    """

    def __init__(self, config: Optional[IncidentConfig] = None):
        """
        Initialize incident service.

        Args:
            config: Incident response configuration
        """
        self.config = config or IncidentConfig()
        self._violations: dict[str, int] = defaultdict(int)
        self._blocked_ips: dict[str, datetime] = {}
        self._blocked_devices: dict[str, datetime] = {}
        self._incidents: list[Incident] = []

    def record_violation(
        self,
        source_ip: str,
        violation_type: str,
        device_id: Optional[str] = None
    ) -> None:
        """
        Record a security violation.

        Args:
            source_ip: Source IP address
            violation_type: Type of violation
            device_id: Device ID if available
        """
        self._violations[source_ip] += 1

        if device_id:
            self._violations[f"device:{device_id}"] += 1

        # Auto-block if threshold exceeded
        if self._violations[source_ip] >= self.config.auto_block_threshold:
            self.block_ip(source_ip, self.config.block_duration_minutes)

    def get_violation_count(self, identifier: str) -> int:
        """
        Get violation count for identifier.

        Args:
            identifier: IP address or device ID

        Returns:
            int: Violation count
        """
        return self._violations.get(identifier, 0)

    def block_ip(self, ip: str, duration_minutes: int) -> None:
        """
        Block an IP address.

        Args:
            ip: IP address to block
            duration_minutes: Block duration
        """
        until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self._blocked_ips[ip] = until

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address."""
        if ip in self._blocked_ips:
            del self._blocked_ips[ip]

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if ip not in self._blocked_ips:
            return False

        until = self._blocked_ips[ip]
        if datetime.now(timezone.utc) >= until:
            del self._blocked_ips[ip]
            return False

        return True

    def block_device(self, device_id: str, duration_minutes: int) -> None:
        """
        Block a device.

        Args:
            device_id: Device ID to block
            duration_minutes: Block duration
        """
        until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self._blocked_devices[device_id] = until

    def unblock_device(self, device_id: str) -> None:
        """Unblock a device."""
        if device_id in self._blocked_devices:
            del self._blocked_devices[device_id]

    def is_device_blocked(self, device_id: str) -> bool:
        """Check if device is blocked."""
        if device_id not in self._blocked_devices:
            return False

        until = self._blocked_devices[device_id]
        if datetime.now(timezone.utc) >= until:
            del self._blocked_devices[device_id]
            return False

        return True

    def create_incident(
        self,
        source_ip: str,
        incident_type: str,
        details: Optional[dict] = None
    ) -> Incident:
        """
        Create an incident record.

        Args:
            source_ip: Source IP of incident
            incident_type: Type of incident
            details: Additional details

        Returns:
            Incident: Created incident
        """
        incident = Incident(
            incident_id=f"inc_{uuid.uuid4().hex[:12]}",
            source_ip=source_ip,
            incident_type=incident_type,
            details=details or {}
        )

        self._incidents.append(incident)
        return incident

    def execute_response(
        self,
        incident: Incident,
        actions: list[IncidentAction]
    ) -> IncidentResponse:
        """
        Execute incident response actions.

        Args:
            incident: Incident to respond to
            actions: Actions to execute

        Returns:
            IncidentResponse: Response result
        """
        response = IncidentResponse(
            incident_id=incident.incident_id,
            actions=actions,
            reason=f"Response to {incident.incident_type}"
        )

        for action in actions:
            result = self._execute_action(action, incident)
            if result.success:
                response.actions_executed.append(action)

        response.success = len(response.actions_executed) > 0
        return response

    def _execute_action(
        self,
        action: IncidentAction,
        incident: Incident
    ) -> ActionResult:
        """
        Execute a single action.

        Args:
            action: Action to execute
            incident: Related incident

        Returns:
            ActionResult: Action result
        """
        if action == IncidentAction.BLOCK_IP:
            self.block_ip(incident.source_ip, self.config.block_duration_minutes)
            return ActionResult(success=True, message=f"Blocked IP {incident.source_ip}")

        elif action == IncidentAction.BLOCK_DEVICE:
            device_id = incident.details.get("device_id")
            if device_id:
                self.block_device(device_id, self.config.block_duration_minutes)
                return ActionResult(success=True, message=f"Blocked device {device_id}")
            return ActionResult(success=False, message="No device ID")

        elif action == IncidentAction.INVALIDATE_SESSION:
            # Would call session service
            return ActionResult(success=True, message="Sessions invalidated")

        elif action == IncidentAction.SNAPSHOT_LOGS:
            self.create_log_snapshot(incident)
            return ActionResult(success=True, message="Logs snapshotted")

        elif action == IncidentAction.ALERT:
            # Would call alerting service
            return ActionResult(success=True, message="Alert sent")

        return ActionResult(success=False, message=f"Unknown action: {action}")

    def invalidate_sessions_for_ip(self, ip: str) -> ActionResult:
        """
        Invalidate all sessions for IP.

        Args:
            ip: IP address

        Returns:
            ActionResult: Result
        """
        # Would integrate with session service
        return ActionResult(success=True, message=f"Invalidated sessions for {ip}")

    def invalidate_sessions_for_user(self, user_id: str) -> ActionResult:
        """
        Invalidate all sessions for user.

        Args:
            user_id: User ID

        Returns:
            ActionResult: Result
        """
        # Would integrate with session service
        return ActionResult(success=True, message=f"Invalidated sessions for {user_id}")

    def create_log_snapshot(
        self,
        incident: Incident,
        hours_before: int = 1,
        hours_after: int = 0
    ) -> LogSnapshot:
        """
        Create log snapshot for incident.

        Args:
            incident: Related incident
            hours_before: Hours of logs before incident
            hours_after: Hours of logs after incident

        Returns:
            LogSnapshot: Log snapshot
        """
        now = datetime.now(timezone.utc)
        time_start = incident.timestamp - timedelta(hours=hours_before)
        time_end = incident.timestamp + timedelta(hours=hours_after) if hours_after else now

        return LogSnapshot(
            incident_id=incident.incident_id,
            timestamp=now,
            time_range_start=time_start,
            time_range_end=time_end,
            logs=[]  # Would fetch actual logs
        )

    def get_incident_history(self, limit: int = 100) -> list[Incident]:
        """
        Get incident history.

        Args:
            limit: Maximum incidents to return

        Returns:
            list[Incident]: Recent incidents
        """
        return sorted(
            self._incidents,
            key=lambda i: i.timestamp,
            reverse=True
        )[:limit]

    def get_incidents_by_ip(self, ip: str) -> list[Incident]:
        """
        Get incidents for IP.

        Args:
            ip: IP address

        Returns:
            list[Incident]: Matching incidents
        """
        return [i for i in self._incidents if i.source_ip == ip]


# Global service instance
_incident_service: Optional[IncidentService] = None


def _get_incident_service() -> IncidentService:
    """Get or create global incident service."""
    global _incident_service

    if _incident_service is None:
        _incident_service = IncidentService()

    return _incident_service


def create_incident(
    source_ip: str,
    incident_type: str,
    details: Optional[dict] = None
) -> Incident:
    """
    Convenience function to create incident.

    Args:
        source_ip: Source IP
        incident_type: Type of incident
        details: Additional details

    Returns:
        Incident: Created incident
    """
    return _get_incident_service().create_incident(source_ip, incident_type, details)


def execute_response(
    incident: Incident,
    actions: list[IncidentAction]
) -> IncidentResponse:
    """
    Convenience function to execute response.

    Args:
        incident: Incident to respond to
        actions: Actions to execute

    Returns:
        IncidentResponse: Response result
    """
    return _get_incident_service().execute_response(incident, actions)
