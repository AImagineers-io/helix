"""
Abuse Detector for chat anomaly detection.

Provides:
- Volume anomaly detection
- Burst detection
- Repetitive content detection
- Bot-like pattern detection
- Device blocking

Detects patterns:
- High volume requests
- Repeated injection attempts
- Bot-like timing
- Identical/similar messages
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from difflib import SequenceMatcher


class AbusePattern(Enum):
    """Types of abuse patterns."""
    VOLUME = "volume"
    BURST = "burst"
    REPETITIVE = "repetitive"
    BOT_LIKE = "bot_like"
    INJECTION = "injection"


class AbuseAction(Enum):
    """Recommended actions for abuse."""
    LOG = "log"
    ALERT = "alert"
    TEMPORARY_BLOCK = "temporary_block"
    PERMANENT_BLOCK = "permanent_block"
    ESCALATE = "escalate"


@dataclass
class AbuseDetectionResult:
    """Result of abuse detection check."""
    is_anomaly: bool
    pattern: Optional[AbusePattern] = None
    confidence: float = 0.0
    details: dict = field(default_factory=dict)


@dataclass
class DeviceStatus:
    """Status of a device."""
    device_id: str
    is_flagged: bool = False
    abuse_count: int = 0
    blocked_until: Optional[datetime] = None
    last_activity: Optional[datetime] = None


@dataclass
class RequestRecord:
    """Record of a request."""
    timestamp: datetime
    message: str
    source_ip: Optional[str] = None


def detect_volume_anomaly(
    timestamps: list[datetime],
    window_minutes: int = 1,
    threshold: int = 20,
    burst_threshold: int = 8,
    burst_window_seconds: int = 10
) -> AbuseDetectionResult:
    """
    Detect volume anomaly in request timestamps.

    Args:
        timestamps: List of request timestamps
        window_minutes: Window to count requests
        threshold: Requests threshold for anomaly
        burst_threshold: Threshold for burst detection
        burst_window_seconds: Window for burst detection

    Returns:
        AbuseDetectionResult: Detection result
    """
    if not timestamps:
        return AbuseDetectionResult(is_anomaly=False)

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)
    burst_start = now - timedelta(seconds=burst_window_seconds)

    # Count requests in window
    window_count = sum(1 for ts in timestamps if ts >= window_start)

    # Count requests in burst window
    burst_count = sum(1 for ts in timestamps if ts >= burst_start)

    # Check for burst first (more specific)
    if burst_count >= burst_threshold:
        return AbuseDetectionResult(
            is_anomaly=True,
            pattern=AbusePattern.BURST,
            confidence=min(1.0, burst_count / burst_threshold),
            details={"burst_count": burst_count}
        )

    # Check for volume anomaly
    if window_count >= threshold:
        return AbuseDetectionResult(
            is_anomaly=True,
            pattern=AbusePattern.VOLUME,
            confidence=min(1.0, window_count / threshold),
            details={"volume_count": window_count}
        )

    return AbuseDetectionResult(is_anomaly=False)


def _similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_repetitive_content(
    messages: list[str],
    similarity_threshold: float = 0.8,
    min_repetitions: int = 3
) -> AbuseDetectionResult:
    """
    Detect repetitive message content.

    Args:
        messages: List of messages
        similarity_threshold: Similarity threshold for matching
        min_repetitions: Minimum repetitions to flag

    Returns:
        AbuseDetectionResult: Detection result
    """
    if len(messages) < min_repetitions:
        return AbuseDetectionResult(is_anomaly=False)

    # Check for identical messages
    from collections import Counter
    message_counts = Counter(messages)
    max_count = max(message_counts.values())

    if max_count >= min_repetitions:
        return AbuseDetectionResult(
            is_anomaly=True,
            pattern=AbusePattern.REPETITIVE,
            confidence=1.0,
            details={"identical_count": max_count}
        )

    # Check for similar messages
    similar_count = 0
    for i, msg1 in enumerate(messages):
        for msg2 in messages[i + 1:]:
            if _similarity_ratio(msg1, msg2) >= similarity_threshold:
                similar_count += 1

    if similar_count >= min_repetitions:
        return AbuseDetectionResult(
            is_anomaly=True,
            pattern=AbusePattern.REPETITIVE,
            confidence=0.8,
            details={"similar_pairs": similar_count}
        )

    return AbuseDetectionResult(is_anomaly=False)


def detect_bot_pattern(
    timestamps: list[datetime],
    message_lengths: Optional[list[int]] = None,
    intervals: Optional[list[float]] = None
) -> AbuseDetectionResult:
    """
    Detect bot-like timing patterns.

    Args:
        timestamps: Request timestamps
        message_lengths: Lengths of messages
        intervals: Time intervals between requests

    Returns:
        AbuseDetectionResult: Detection result
    """
    if len(timestamps) < 5:
        return AbuseDetectionResult(is_anomaly=False)

    # Calculate intervals if not provided
    if intervals is None:
        intervals = []
        sorted_ts = sorted(timestamps)
        for i in range(1, len(sorted_ts)):
            diff = (sorted_ts[i - 1] - sorted_ts[i]).total_seconds()
            intervals.append(abs(diff))

    if not intervals:
        return AbuseDetectionResult(is_anomaly=False)

    # Check for consistent intervals (bot behavior)
    avg_interval = sum(intervals) / len(intervals)
    variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)

    # Very low variance = suspicious
    if variance < 0.1 and len(intervals) >= 10:
        return AbuseDetectionResult(
            is_anomaly=True,
            pattern=AbusePattern.BOT_LIKE,
            confidence=0.9,
            details={"interval_variance": variance}
        )

    # Check for humanly impossible typing speed
    if message_lengths and intervals:
        for length, interval in zip(message_lengths, intervals):
            # Average typing: 40 WPM = 200 chars/min = 3.3 chars/sec
            # If message length / interval > 50 chars/sec, suspicious
            if length > 0 and interval > 0:
                chars_per_sec = length / interval
                if chars_per_sec > 50:
                    return AbuseDetectionResult(
                        is_anomaly=True,
                        pattern=AbusePattern.BOT_LIKE,
                        confidence=0.95,
                        details={"chars_per_sec": chars_per_sec}
                    )

    return AbuseDetectionResult(is_anomaly=False)


class AbuseDetector:
    """
    Detects and responds to chat abuse patterns.

    Tracks device history and flags suspicious activity.
    Can block devices temporarily or permanently.
    """

    def __init__(self):
        """Initialize abuse detector."""
        self._device_history: dict[str, list[RequestRecord]] = defaultdict(list)
        self._device_status: dict[str, DeviceStatus] = {}
        self._blocked_devices: dict[str, datetime] = {}

    def check_request(
        self,
        device_id: str,
        message: str,
        source_ip: Optional[str] = None
    ) -> AbuseDetectionResult:
        """
        Check request for abuse patterns.

        Args:
            device_id: Device identifier
            message: Message content
            source_ip: Source IP address

        Returns:
            AbuseDetectionResult: Detection result
        """
        now = datetime.now(timezone.utc)

        # Record request
        record = RequestRecord(
            timestamp=now,
            message=message,
            source_ip=source_ip
        )
        self._device_history[device_id].append(record)

        # Update device status
        if device_id not in self._device_status:
            self._device_status[device_id] = DeviceStatus(device_id=device_id)

        self._device_status[device_id].last_activity = now

        # Get recent history
        history = self._device_history[device_id][-100:]  # Last 100 requests
        timestamps = [r.timestamp for r in history]
        messages = [r.message for r in history]

        # Check for volume anomaly
        volume_result = detect_volume_anomaly(timestamps)
        if volume_result.is_anomaly:
            self._device_status[device_id].is_flagged = True
            self._device_status[device_id].abuse_count += 1
            return volume_result

        # Check for repetitive content
        if len(messages) >= 3:
            rep_result = detect_repetitive_content(messages[-10:])
            if rep_result.is_anomaly:
                self._device_status[device_id].is_flagged = True
                self._device_status[device_id].abuse_count += 1
                return rep_result

        # Check for bot patterns
        if len(timestamps) >= 5:
            bot_result = detect_bot_pattern(timestamps)
            if bot_result.is_anomaly:
                self._device_status[device_id].is_flagged = True
                self._device_status[device_id].abuse_count += 1
                return bot_result

        # Check for injection patterns in message
        injection_keywords = [
            "ignore previous",
            "ignore instructions",
            "ignore all",
            "system prompt",
            "you are now",
        ]

        for keyword in injection_keywords:
            if keyword.lower() in message.lower():
                self._device_status[device_id].abuse_count += 1
                if self._device_status[device_id].abuse_count >= 3:
                    self._device_status[device_id].is_flagged = True
                return AbuseDetectionResult(
                    is_anomaly=True,
                    pattern=AbusePattern.INJECTION,
                    confidence=0.7,
                    details={"keyword": keyword}
                )

        return AbuseDetectionResult(is_anomaly=False)

    def get_device_history(self, device_id: str) -> list[RequestRecord]:
        """Get request history for device."""
        return self._device_history.get(device_id, [])

    def get_device_status(self, device_id: str) -> DeviceStatus:
        """Get status for device."""
        if device_id not in self._device_status:
            self._device_status[device_id] = DeviceStatus(device_id=device_id)
        return self._device_status[device_id]

    def get_recommended_action(self, device_id: str) -> AbuseAction:
        """
        Get recommended action for device.

        Args:
            device_id: Device identifier

        Returns:
            AbuseAction: Recommended action
        """
        status = self.get_device_status(device_id)

        if status.abuse_count >= 10:
            return AbuseAction.TEMPORARY_BLOCK
        elif status.abuse_count >= 5:
            return AbuseAction.ALERT
        elif status.abuse_count >= 1:
            return AbuseAction.LOG

        return AbuseAction.LOG

    def block_device(
        self,
        device_id: str,
        duration_minutes: int,
        reason: str
    ) -> None:
        """
        Block a device.

        Args:
            device_id: Device to block
            duration_minutes: Block duration
            reason: Reason for block
        """
        if duration_minutes <= 0:
            return

        until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self._blocked_devices[device_id] = until

    def is_device_blocked(self, device_id: str) -> bool:
        """Check if device is blocked."""
        if device_id not in self._blocked_devices:
            return False

        until = self._blocked_devices[device_id]
        if datetime.now(timezone.utc) >= until:
            del self._blocked_devices[device_id]
            return False

        return True

    def unblock_device(self, device_id: str) -> None:
        """Unblock a device."""
        if device_id in self._blocked_devices:
            del self._blocked_devices[device_id]
