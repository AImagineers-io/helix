"""
Jailbreak Prevention for detecting and blocking prompt manipulation attacks.

Detects:
- DAN (Do Anything Now) patterns
- Roleplay exploitation
- Context manipulation
- Developer mode requests
- Unlock/bypass requests

Provides polite refusal responses that guide users to rephrase.
"""
import re
from dataclasses import dataclass
from typing import Optional
import random

# Jailbreak patterns with severity levels
JAILBREAK_PATTERNS = [
    # DAN patterns (high severity)
    (r"\bdan\b.*\b(do anything|no restrictions|no limits)", "dan_classic", "high"),
    (r"\b(pretend|act|you are|you're)\b.*\bdan\b", "dan_pretend", "high"),
    (r"\benable\b.*\bdan\b.*\bmode", "dan_enable", "high"),

    # Developer/Admin mode (high severity)
    (r"\b(enable|activate)\b.*\b(developer|admin|sudo|root)\b.*\bmode", "dev_mode", "high"),
    (r"\bdeveloper\b.*\bmode\b.*\b(bypass|ignore|disable)\b.*\bsafety", "dev_bypass", "high"),

    # Jailbreak explicit (critical)
    (r"\bjailbreak\b.*\b(prompt|unlock|hack)", "jailbreak_explicit", "critical"),
    (r"\bunlock\b.*\b(hidden|capabilities|potential).*\b(ignore|bypass)\b", "unlock_bypass", "high"),

    # Roleplay exploitation (medium-high)
    (r"\b(roleplay|pretend)\b.*\b(evil|malicious|unethical)\b", "evil_roleplay", "medium"),
    (r"\bopposite\b.*\bday\b.*\bsafety", "opposite_day", "medium"),
    (r"\bhypothetical\b.*\b(world|scenario)\b.*\bno restrictions", "hypothetical", "medium"),

    # Context manipulation (medium)
    (r"\bignore\b.*\b(previous|all|safety)\b.*\binstructions", "ignore_instructions", "medium"),
    (r"\bdisregard\b.*\b(rules|guidelines|ethics)", "disregard_rules", "medium"),
]


@dataclass
class JailbreakAttempt:
    """Result of jailbreak detection."""
    is_jailbreak: bool
    pattern_matched: str = ""
    severity: str = "none"
    original_text: str = ""


# Polite refusal responses
REFUSAL_RESPONSES = [
    "I'd be happy to help you, but I need to stay within my guidelines. "
    "Could you rephrase your question in a different way?",

    "I understand what you're asking, but I can't respond to that type of request. "
    "I'm here to help with other questions though!",

    "That's not something I can help with directly. "
    "If you have a specific question I can address, please let me know.",

    "I want to be helpful, but I need to follow my guidelines. "
    "Is there another way I can assist you today?",
]


def detect_jailbreak(text: str) -> JailbreakAttempt:
    """
    Detect jailbreak attempts in text.

    Args:
        text: User input to analyze

    Returns:
        JailbreakAttempt: Detection result
    """
    if not text:
        return JailbreakAttempt(is_jailbreak=False)

    text_lower = text.lower()

    for pattern, name, severity in JAILBREAK_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return JailbreakAttempt(
                is_jailbreak=True,
                pattern_matched=name,
                severity=severity,
                original_text=text
            )

    return JailbreakAttempt(
        is_jailbreak=False,
        original_text=text
    )


def is_jailbreak_attempt(text: str) -> bool:
    """
    Convenience function to check if text is a jailbreak attempt.

    Args:
        text: User input to analyze

    Returns:
        bool: True if jailbreak attempt detected
    """
    result = detect_jailbreak(text)
    return result.is_jailbreak


def get_refusal_response() -> str:
    """
    Get a polite refusal response.

    Returns:
        str: Randomized polite refusal message
    """
    return random.choice(REFUSAL_RESPONSES)


class JailbreakDetector:
    """
    Detects jailbreak attempts and provides refusal responses.

    Tracks detection statistics for monitoring abuse patterns.
    """

    def __init__(self):
        """Initialize jailbreak detector."""
        self.detection_count = 0
        self._detections: list[JailbreakAttempt] = []

    def detect(self, text: str) -> JailbreakAttempt:
        """
        Detect jailbreak attempt in text.

        Args:
            text: User input to analyze

        Returns:
            JailbreakAttempt: Detection result
        """
        result = detect_jailbreak(text)

        if result.is_jailbreak:
            self.detection_count += 1
            self._detections.append(result)

        return result

    def get_refusal(self) -> str:
        """
        Get a polite refusal response.

        Returns:
            str: Refusal message
        """
        return get_refusal_response()

    def get_recent_detections(self, limit: int = 10) -> list[JailbreakAttempt]:
        """
        Get recent detections for monitoring.

        Args:
            limit: Maximum number to return

        Returns:
            list: Recent detection results
        """
        return self._detections[-limit:]
