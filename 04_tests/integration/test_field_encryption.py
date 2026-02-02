"""
Integration tests for Field Encryption (P12.5.2)

Tests field-level encryption including:
- AES-256-GCM encryption
- Key management
- Encrypt/decrypt operations
- Nonce handling
- Authentication tags
"""
import pytest

from core.encryption import (
    EncryptionConfig,
    FieldEncryptor,
    encrypt_field,
    decrypt_field,
    generate_encryption_key,
    EncryptionError,
    DecryptionError,
)


class TestKeyGeneration:
    """Tests for encryption key generation."""

    def test_generates_key(self):
        """Should generate encryption key."""
        key = generate_encryption_key()
        assert key is not None
        assert len(key) > 0

    def test_keys_are_unique(self):
        """Each key should be unique."""
        keys = [generate_encryption_key() for _ in range(10)]
        assert len(set(keys)) == 10

    def test_key_is_base64(self):
        """Key should be base64 encoded."""
        key = generate_encryption_key()
        import base64
        # Should not raise
        decoded = base64.b64decode(key)
        assert len(decoded) == 32  # 256 bits


class TestEncryptionConfig:
    """Tests for encryption configuration."""

    def test_default_algorithm(self):
        """Default algorithm should be AES-256-GCM."""
        config = EncryptionConfig(key=generate_encryption_key())
        assert config.algorithm == "AES-256-GCM"


class TestFieldEncryptor:
    """Tests for FieldEncryptor class."""

    @pytest.fixture
    def encryptor(self):
        """Create field encryptor."""
        key = generate_encryption_key()
        return FieldEncryptor(key)

    def test_encrypt_returns_ciphertext(self, encryptor):
        """Encrypt should return ciphertext."""
        plaintext = "sensitive data"

        ciphertext = encryptor.encrypt(plaintext)

        assert ciphertext is not None
        assert ciphertext != plaintext

    def test_decrypt_returns_plaintext(self, encryptor):
        """Decrypt should return original plaintext."""
        plaintext = "sensitive data"

        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_same_plaintext_different_ciphertext(self, encryptor):
        """Same plaintext should produce different ciphertexts (due to nonce)."""
        plaintext = "same text"

        ct1 = encryptor.encrypt(plaintext)
        ct2 = encryptor.encrypt(plaintext)

        assert ct1 != ct2

    def test_tampered_ciphertext_fails(self, encryptor):
        """Tampered ciphertext should fail decryption."""
        plaintext = "sensitive"
        ciphertext = encryptor.encrypt(plaintext)

        # Tamper with ciphertext
        tampered = ciphertext[:-5] + "XXXXX"

        with pytest.raises(DecryptionError):
            encryptor.decrypt(tampered)

    def test_wrong_key_fails(self):
        """Wrong key should fail decryption."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        encryptor1 = FieldEncryptor(key1)
        encryptor2 = FieldEncryptor(key2)

        ciphertext = encryptor1.encrypt("secret")

        with pytest.raises(DecryptionError):
            encryptor2.decrypt(ciphertext)


class TestEncryptDecryptFunctions:
    """Tests for convenience encrypt/decrypt functions."""

    @pytest.fixture
    def key(self):
        return generate_encryption_key()

    def test_encrypt_field(self, key):
        """encrypt_field should work."""
        ciphertext = encrypt_field("data", key)
        assert ciphertext is not None

    def test_decrypt_field(self, key):
        """decrypt_field should work."""
        ciphertext = encrypt_field("data", key)
        plaintext = decrypt_field(ciphertext, key)
        assert plaintext == "data"


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def encryptor(self):
        return FieldEncryptor(generate_encryption_key())

    def test_empty_string(self, encryptor):
        """Empty string should encrypt/decrypt."""
        ciphertext = encryptor.encrypt("")
        plaintext = encryptor.decrypt(ciphertext)
        assert plaintext == ""

    def test_long_text(self, encryptor):
        """Long text should encrypt/decrypt."""
        long_text = "x" * 100000

        ciphertext = encryptor.encrypt(long_text)
        plaintext = encryptor.decrypt(ciphertext)

        assert plaintext == long_text

    def test_unicode_text(self, encryptor):
        """Unicode text should encrypt/decrypt."""
        unicode_text = "Hello 世界 🎉"

        ciphertext = encryptor.encrypt(unicode_text)
        plaintext = encryptor.decrypt(ciphertext)

        assert plaintext == unicode_text

    def test_special_characters(self, encryptor):
        """Special characters should encrypt/decrypt."""
        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?\n\t"

        ciphertext = encryptor.encrypt(special)
        plaintext = encryptor.decrypt(ciphertext)

        assert plaintext == special


class TestEncryptionError:
    """Tests for encryption errors."""

    def test_encryption_error(self):
        """EncryptionError should have message."""
        error = EncryptionError("Failed to encrypt")
        assert "Failed to encrypt" in str(error)

    def test_decryption_error(self):
        """DecryptionError should have message."""
        error = DecryptionError("Failed to decrypt")
        assert "Failed to decrypt" in str(error)


class TestCiphertextFormat:
    """Tests for ciphertext format."""

    @pytest.fixture
    def encryptor(self):
        return FieldEncryptor(generate_encryption_key())

    def test_ciphertext_is_base64(self, encryptor):
        """Ciphertext should be base64 encoded."""
        ciphertext = encryptor.encrypt("test")

        import base64
        # Should not raise
        decoded = base64.b64decode(ciphertext)
        assert len(decoded) > 0

    def test_ciphertext_contains_nonce(self, encryptor):
        """Ciphertext should contain nonce (12 bytes for GCM)."""
        ciphertext = encryptor.encrypt("test")

        import base64
        decoded = base64.b64decode(ciphertext)

        # Nonce (12) + ciphertext + tag (16)
        # Minimum size for empty plaintext
        assert len(decoded) >= 28  # 12 + 0 + 16


class TestKeyValidation:
    """Tests for key validation."""

    def test_invalid_key_raises(self):
        """Invalid key should raise error."""
        with pytest.raises((EncryptionError, ValueError)):
            FieldEncryptor("invalid_key_not_base64!")

    def test_short_key_raises(self):
        """Key too short should raise error."""
        import base64
        short_key = base64.b64encode(b"short").decode()

        with pytest.raises((EncryptionError, ValueError)):
            FieldEncryptor(short_key)
