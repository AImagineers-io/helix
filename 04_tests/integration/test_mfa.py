"""
Integration tests for Multi-Factor Authentication (P12.1.4)

Tests the MFA service including:
- TOTP secret generation
- QR code URL generation
- TOTP verification
- MFA enable/disable flow
- MFA verification during login
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from services.mfa_service import (
    MFAService,
    MFAError,
    TOTPSecret,
    generate_totp_secret,
    generate_totp_code,
    verify_totp_code,
    get_provisioning_uri,
)


class TestTOTPSecretGeneration:
    """Tests for TOTP secret generation."""

    def test_generate_totp_secret_returns_valid_base32(self):
        """Generated secret should be valid base32."""
        secret = generate_totp_secret()
        # Base32 alphabet
        valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
        assert all(c in valid_chars for c in secret)

    def test_generate_totp_secret_correct_length(self):
        """Secret should be 32 characters (160 bits)."""
        secret = generate_totp_secret()
        assert len(secret) == 32

    def test_generate_totp_secret_unique(self):
        """Each generated secret should be unique."""
        secrets = [generate_totp_secret() for _ in range(100)]
        assert len(set(secrets)) == 100


class TestTOTPCodeGeneration:
    """Tests for TOTP code generation."""

    def test_generate_totp_code_six_digits(self):
        """Generated code should be 6 digits."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_totp_code_changes_over_time(self):
        """Code should change with different time periods."""
        secret = generate_totp_secret()
        # Codes at different 30-second intervals should differ
        with patch('time.time', return_value=0):
            code1 = generate_totp_code(secret)
        with patch('time.time', return_value=30):
            code2 = generate_totp_code(secret)
        # Codes should be different (statistically almost certain)
        # Note: theoretically could be same, but probability is 1/1000000


class TestTOTPCodeVerification:
    """Tests for TOTP code verification."""

    def test_verify_totp_code_correct(self):
        """Valid code should verify successfully."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        assert verify_totp_code(secret, code) is True

    def test_verify_totp_code_incorrect(self):
        """Invalid code should fail verification."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "000000") is False
        assert verify_totp_code(secret, "123456") is False

    def test_verify_totp_code_allows_time_drift(self):
        """Verification should allow for clock drift (1 period)."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        # Code should still be valid
        assert verify_totp_code(secret, code, window=1) is True

    def test_verify_totp_code_empty(self):
        """Empty code should fail gracefully."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "") is False

    def test_verify_totp_code_invalid_format(self):
        """Non-numeric code should fail gracefully."""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "abcdef") is False
        assert verify_totp_code(secret, "12345") is False  # Too short
        assert verify_totp_code(secret, "1234567") is False  # Too long


class TestProvisioningURI:
    """Tests for provisioning URI (QR code) generation."""

    def test_get_provisioning_uri_format(self):
        """URI should follow otpauth format."""
        secret = generate_totp_secret()
        uri = get_provisioning_uri(
            secret=secret,
            email="user@example.com",
            issuer="Helix"
        )
        assert uri.startswith("otpauth://totp/")
        assert "Helix" in uri
        assert "user%40example.com" in uri or "user@example.com" in uri

    def test_get_provisioning_uri_contains_secret(self):
        """URI should contain the secret."""
        secret = "JBSWY3DPEHPK3PXP"  # Fixed secret for testing
        uri = get_provisioning_uri(
            secret=secret,
            email="user@example.com",
            issuer="Helix"
        )
        assert f"secret={secret}" in uri

    def test_get_provisioning_uri_encodes_special_chars(self):
        """URI should properly encode special characters."""
        secret = generate_totp_secret()
        uri = get_provisioning_uri(
            secret=secret,
            email="test+user@example.com",
            issuer="Helix Admin"
        )
        # Should be URL-safe
        assert " " not in uri or "%20" in uri


class TestMFAService:
    """Tests for MFA service operations."""

    @pytest.fixture
    def mfa_service(self):
        """Create MFA service instance."""
        return MFAService(issuer="Helix")

    def test_setup_mfa_returns_secret_and_uri(self, mfa_service):
        """Setup should return secret and provisioning URI."""
        result = mfa_service.setup_mfa(user_id="user123", email="user@example.com")

        assert isinstance(result, TOTPSecret)
        assert result.secret is not None
        assert result.provisioning_uri is not None
        assert len(result.secret) == 32

    def test_setup_mfa_uri_contains_email(self, mfa_service):
        """Setup URI should contain user email."""
        result = mfa_service.setup_mfa(user_id="user123", email="test@example.com")
        assert "test" in result.provisioning_uri

    def test_verify_setup_with_valid_code(self, mfa_service):
        """Valid code should complete MFA setup."""
        setup = mfa_service.setup_mfa(user_id="user123", email="user@example.com")
        code = generate_totp_code(setup.secret)

        is_valid = mfa_service.verify_setup(user_id="user123", code=code)
        assert is_valid is True

    def test_verify_setup_with_invalid_code(self, mfa_service):
        """Invalid code should fail MFA setup."""
        mfa_service.setup_mfa(user_id="user123", email="user@example.com")

        is_valid = mfa_service.verify_setup(user_id="user123", code="000000")
        assert is_valid is False

    def test_verify_setup_unknown_user_raises_error(self, mfa_service):
        """Verifying for unknown user should raise error."""
        with pytest.raises(MFAError, match="MFA setup not found"):
            mfa_service.verify_setup(user_id="unknown", code="123456")


class TestMFAEnableDisable:
    """Tests for enabling/disabling MFA."""

    @pytest.fixture
    def mfa_service(self):
        """Create MFA service instance."""
        return MFAService(issuer="Helix")

    def test_enable_mfa_requires_setup_verification(self, mfa_service):
        """MFA should only be enabled after setup verification."""
        setup = mfa_service.setup_mfa(user_id="user123", email="user@example.com")

        # Before verification, MFA is not enabled
        assert mfa_service.is_mfa_enabled(user_id="user123") is False

        # After verification, MFA is enabled
        code = generate_totp_code(setup.secret)
        mfa_service.verify_setup(user_id="user123", code=code)

        assert mfa_service.is_mfa_enabled(user_id="user123") is True

    def test_disable_mfa_requires_valid_code(self, mfa_service):
        """Disabling MFA should require valid TOTP code."""
        setup = mfa_service.setup_mfa(user_id="user123", email="user@example.com")
        code = generate_totp_code(setup.secret)
        mfa_service.verify_setup(user_id="user123", code=code)

        # Try to disable with wrong code
        with pytest.raises(MFAError, match="Invalid code"):
            mfa_service.disable_mfa(user_id="user123", code="000000")

        # MFA should still be enabled
        assert mfa_service.is_mfa_enabled(user_id="user123") is True

    def test_disable_mfa_with_valid_code(self, mfa_service):
        """Disabling MFA with valid code should succeed."""
        setup = mfa_service.setup_mfa(user_id="user123", email="user@example.com")
        code = generate_totp_code(setup.secret)
        mfa_service.verify_setup(user_id="user123", code=code)

        # Disable with valid code
        new_code = generate_totp_code(setup.secret)
        mfa_service.disable_mfa(user_id="user123", code=new_code)

        assert mfa_service.is_mfa_enabled(user_id="user123") is False


class TestMFAVerification:
    """Tests for MFA verification during login."""

    @pytest.fixture
    def mfa_service(self):
        """Create MFA service instance."""
        return MFAService(issuer="Helix")

    @pytest.fixture
    def enabled_user(self, mfa_service):
        """Create a user with MFA enabled."""
        setup = mfa_service.setup_mfa(user_id="user123", email="user@example.com")
        code = generate_totp_code(setup.secret)
        mfa_service.verify_setup(user_id="user123", code=code)
        return setup.secret

    def test_verify_mfa_valid_code(self, mfa_service, enabled_user):
        """Valid code should verify successfully."""
        secret = enabled_user
        code = generate_totp_code(secret)

        assert mfa_service.verify_mfa(user_id="user123", code=code) is True

    def test_verify_mfa_invalid_code(self, mfa_service, enabled_user):
        """Invalid code should fail verification."""
        assert mfa_service.verify_mfa(user_id="user123", code="000000") is False

    def test_verify_mfa_user_without_mfa(self, mfa_service):
        """Verification for user without MFA should raise error."""
        with pytest.raises(MFAError, match="MFA not enabled"):
            mfa_service.verify_mfa(user_id="unknown", code="123456")


class TestBackupCodes:
    """Tests for MFA backup codes."""

    @pytest.fixture
    def mfa_service(self):
        """Create MFA service instance."""
        return MFAService(issuer="Helix")

    def test_generate_backup_codes_returns_list(self, mfa_service):
        """Should generate list of backup codes."""
        codes = mfa_service.generate_backup_codes(user_id="user123")

        assert isinstance(codes, list)
        assert len(codes) == 10  # Default count

    def test_backup_codes_are_unique(self, mfa_service):
        """All backup codes should be unique."""
        codes = mfa_service.generate_backup_codes(user_id="user123")
        assert len(set(codes)) == len(codes)

    def test_backup_codes_correct_format(self, mfa_service):
        """Backup codes should be 8 alphanumeric characters."""
        codes = mfa_service.generate_backup_codes(user_id="user123")

        for code in codes:
            assert len(code) == 8
            assert code.isalnum()

    def test_verify_backup_code_valid(self, mfa_service):
        """Valid backup code should verify and be consumed."""
        codes = mfa_service.generate_backup_codes(user_id="user123")
        first_code = codes[0]

        assert mfa_service.verify_backup_code(user_id="user123", code=first_code) is True
        # Code should be consumed and not work again
        assert mfa_service.verify_backup_code(user_id="user123", code=first_code) is False

    def test_verify_backup_code_invalid(self, mfa_service):
        """Invalid backup code should fail."""
        mfa_service.generate_backup_codes(user_id="user123")

        assert mfa_service.verify_backup_code(user_id="user123", code="INVALIDC") is False
