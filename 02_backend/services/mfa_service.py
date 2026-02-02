"""
Multi-Factor Authentication (MFA) Service using TOTP.

Provides:
- TOTP secret generation (Google Authenticator compatible)
- QR code provisioning URI generation
- TOTP code verification with time drift tolerance
- Backup codes for account recovery
- MFA enable/disable lifecycle

The implementation follows RFC 6238 (TOTP) and is compatible with:
- Google Authenticator
- Authy
- Microsoft Authenticator
- 1Password
- Any standard TOTP app
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote


# TOTP Configuration
TOTP_DIGITS = 6
TOTP_PERIOD = 30  # seconds
TOTP_ALGORITHM = "SHA1"
SECRET_LENGTH = 20  # bytes (160 bits)
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8


class MFAError(Exception):
    """Raised when MFA operations fail."""
    pass


@dataclass(frozen=True)
class TOTPSecret:
    """
    Result of MFA setup containing secret and provisioning info.

    Attributes:
        secret: Base32-encoded TOTP secret (show once, never stored)
        provisioning_uri: otpauth:// URI for QR code generation
    """
    secret: str
    provisioning_uri: str


def generate_totp_secret() -> str:
    """
    Generate a cryptographically secure TOTP secret.

    Returns:
        str: Base32-encoded secret (32 characters)
    """
    random_bytes = secrets.token_bytes(SECRET_LENGTH)
    return base64.b32encode(random_bytes).decode('ascii')


def generate_totp_code(secret: str, time_step: Optional[int] = None) -> str:
    """
    Generate a TOTP code for the given secret.

    Args:
        secret: Base32-encoded secret
        time_step: Optional time step (for testing), defaults to current time

    Returns:
        str: 6-digit TOTP code
    """
    if time_step is None:
        time_step = int(time.time()) // TOTP_PERIOD

    # Decode the secret
    key = base64.b32decode(secret.upper())

    # Pack the time step as a big-endian 64-bit integer
    msg = struct.pack('>Q', time_step)

    # Calculate HMAC-SHA1
    h = hmac.new(key, msg, hashlib.sha1).digest()

    # Dynamic truncation
    offset = h[-1] & 0x0F
    code = struct.unpack('>I', h[offset:offset + 4])[0]
    code &= 0x7FFFFFFF
    code %= 10 ** TOTP_DIGITS

    return str(code).zfill(TOTP_DIGITS)


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify a TOTP code against a secret.

    Allows for clock drift by checking adjacent time windows.

    Args:
        secret: Base32-encoded secret
        code: 6-digit code to verify
        window: Number of time periods to check before/after current

    Returns:
        bool: True if code is valid
    """
    if not code or not code.isdigit() or len(code) != TOTP_DIGITS:
        return False

    current_time_step = int(time.time()) // TOTP_PERIOD

    # Check current and adjacent time windows
    for offset in range(-window, window + 1):
        expected_code = generate_totp_code(secret, current_time_step + offset)
        if hmac.compare_digest(expected_code, code):
            return True

    return False


def get_provisioning_uri(secret: str, email: str, issuer: str) -> str:
    """
    Generate otpauth:// URI for QR code generation.

    The URI can be converted to a QR code for scanning with
    authenticator apps.

    Args:
        secret: Base32-encoded secret
        email: User's email address
        issuer: Application name (e.g., "Helix")

    Returns:
        str: otpauth:// URI
    """
    label = quote(f"{issuer}:{email}", safe="")
    params = {
        "secret": secret,
        "issuer": quote(issuer),
        "algorithm": TOTP_ALGORITHM,
        "digits": str(TOTP_DIGITS),
        "period": str(TOTP_PERIOD),
    }
    param_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"otpauth://totp/{label}?{param_string}"


class MFAService:
    """
    Service for managing Multi-Factor Authentication.

    Handles the full MFA lifecycle:
    1. Setup: Generate secret and provisioning URI
    2. Verify Setup: User proves they can generate codes
    3. Enable: MFA becomes required for login
    4. Verify: Check codes during login
    5. Disable: Turn off MFA (requires valid code)
    """

    def __init__(self, issuer: str = "Helix"):
        """
        Initialize MFA service.

        Args:
            issuer: Application name shown in authenticator apps
        """
        self.issuer = issuer
        # In-memory storage for pending setups and enabled users
        self._pending_setups: dict[str, str] = {}  # user_id -> secret
        self._enabled_users: dict[str, str] = {}  # user_id -> secret
        self._backup_codes: dict[str, set[str]] = {}  # user_id -> set of codes

    def setup_mfa(self, user_id: str, email: str) -> TOTPSecret:
        """
        Initiate MFA setup for a user.

        Generates a new secret and provisioning URI. The user must
        verify they can generate codes before MFA is enabled.

        Args:
            user_id: Unique user identifier
            email: User's email address

        Returns:
            TOTPSecret: Secret and provisioning URI for QR code
        """
        secret = generate_totp_secret()
        provisioning_uri = get_provisioning_uri(
            secret=secret,
            email=email,
            issuer=self.issuer
        )

        # Store pending setup
        self._pending_setups[user_id] = secret

        return TOTPSecret(secret=secret, provisioning_uri=provisioning_uri)

    def verify_setup(self, user_id: str, code: str) -> bool:
        """
        Verify MFA setup by checking user can generate valid codes.

        If verification succeeds, MFA is enabled for the user.

        Args:
            user_id: User identifier
            code: TOTP code from user's authenticator

        Returns:
            bool: True if code is valid and MFA is now enabled

        Raises:
            MFAError: If no pending setup found
        """
        secret = self._pending_setups.get(user_id)
        if secret is None:
            raise MFAError("MFA setup not found for user")

        if not verify_totp_code(secret, code):
            return False

        # Move from pending to enabled
        del self._pending_setups[user_id]
        self._enabled_users[user_id] = secret

        return True

    def is_mfa_enabled(self, user_id: str) -> bool:
        """
        Check if MFA is enabled for a user.

        Args:
            user_id: User identifier

        Returns:
            bool: True if MFA is enabled
        """
        return user_id in self._enabled_users

    def verify_mfa(self, user_id: str, code: str) -> bool:
        """
        Verify a TOTP code for an enabled user.

        Args:
            user_id: User identifier
            code: TOTP code to verify

        Returns:
            bool: True if code is valid

        Raises:
            MFAError: If MFA is not enabled for user
        """
        secret = self._enabled_users.get(user_id)
        if secret is None:
            raise MFAError("MFA not enabled for user")

        return verify_totp_code(secret, code)

    def disable_mfa(self, user_id: str, code: str) -> None:
        """
        Disable MFA for a user.

        Requires a valid TOTP code to prevent unauthorized disabling.

        Args:
            user_id: User identifier
            code: TOTP code to verify

        Raises:
            MFAError: If MFA not enabled or code is invalid
        """
        secret = self._enabled_users.get(user_id)
        if secret is None:
            raise MFAError("MFA not enabled for user")

        if not verify_totp_code(secret, code):
            raise MFAError("Invalid code")

        del self._enabled_users[user_id]
        # Also clear backup codes
        self._backup_codes.pop(user_id, None)

    def generate_backup_codes(self, user_id: str, count: int = BACKUP_CODE_COUNT) -> list[str]:
        """
        Generate backup codes for account recovery.

        Backup codes can be used instead of TOTP if the user loses
        access to their authenticator. Each code can only be used once.

        Args:
            user_id: User identifier
            count: Number of codes to generate

        Returns:
            list[str]: List of one-time backup codes
        """
        codes = []
        for _ in range(count):
            # Generate alphanumeric code
            code = secrets.token_hex(BACKUP_CODE_LENGTH // 2).upper()
            codes.append(code)

        # Store codes (in production, store hashed)
        self._backup_codes[user_id] = set(codes)

        return codes

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify and consume a backup code.

        If valid, the code is removed and cannot be used again.

        Args:
            user_id: User identifier
            code: Backup code to verify

        Returns:
            bool: True if code was valid (and is now consumed)
        """
        user_codes = self._backup_codes.get(user_id)
        if user_codes is None:
            return False

        code_upper = code.upper()
        if code_upper not in user_codes:
            return False

        # Consume the code
        user_codes.remove(code_upper)
        return True
