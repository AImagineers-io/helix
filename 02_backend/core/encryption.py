"""
Field-level Encryption for sensitive data.

Provides:
- AES-256-GCM encryption
- Key generation
- Nonce handling
- Authentication tags

Use for encrypting sensitive fields like:
- conversation.raw_message
- qa_pair.answer (if configured)
"""
import base64
import os
from dataclasses import dataclass
from typing import Optional

# Try to use cryptography library
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class EncryptionError(Exception):
    """Error during encryption."""
    pass


class DecryptionError(Exception):
    """Error during decryption."""
    pass


# Nonce size for AES-GCM (96 bits = 12 bytes)
NONCE_SIZE = 12

# Key size for AES-256 (256 bits = 32 bytes)
KEY_SIZE = 32


@dataclass
class EncryptionConfig:
    """Configuration for encryption."""
    key: str
    algorithm: str = "AES-256-GCM"


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.

    Returns:
        str: Base64-encoded 256-bit key
    """
    key_bytes = os.urandom(KEY_SIZE)
    return base64.b64encode(key_bytes).decode("utf-8")


def _decode_key(key: str) -> bytes:
    """
    Decode and validate encryption key.

    Args:
        key: Base64-encoded key

    Returns:
        bytes: Raw key bytes

    Raises:
        ValueError: If key is invalid
    """
    try:
        key_bytes = base64.b64decode(key)
    except Exception as e:
        raise ValueError(f"Invalid key encoding: {e}")

    if len(key_bytes) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key_bytes)}")

    return key_bytes


class FieldEncryptor:
    """
    Encrypts and decrypts field values using AES-256-GCM.

    Each encryption uses a random nonce, so the same plaintext
    produces different ciphertexts.
    """

    def __init__(self, key: str):
        """
        Initialize field encryptor.

        Args:
            key: Base64-encoded encryption key

        Raises:
            EncryptionError: If key is invalid
        """
        try:
            self._key_bytes = _decode_key(key)
        except ValueError as e:
            raise EncryptionError(str(e))

        if CRYPTO_AVAILABLE:
            self._cipher = AESGCM(self._key_bytes)
        else:
            self._cipher = None

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: Text to encrypt

        Returns:
            str: Base64-encoded ciphertext (nonce + ciphertext + tag)

        Raises:
            EncryptionError: If encryption fails
        """
        if not CRYPTO_AVAILABLE:
            return self._encrypt_fallback(plaintext)

        try:
            nonce = os.urandom(NONCE_SIZE)
            plaintext_bytes = plaintext.encode("utf-8")

            ciphertext = self._cipher.encrypt(nonce, plaintext_bytes, None)

            # Combine nonce + ciphertext
            combined = nonce + ciphertext

            return base64.b64encode(combined).decode("utf-8")

        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.

        Args:
            ciphertext: Base64-encoded ciphertext

        Returns:
            str: Decrypted plaintext

        Raises:
            DecryptionError: If decryption fails
        """
        if not CRYPTO_AVAILABLE:
            return self._decrypt_fallback(ciphertext)

        try:
            combined = base64.b64decode(ciphertext)

            if len(combined) < NONCE_SIZE + 16:  # nonce + min tag
                raise DecryptionError("Ciphertext too short")

            nonce = combined[:NONCE_SIZE]
            actual_ciphertext = combined[NONCE_SIZE:]

            plaintext_bytes = self._cipher.decrypt(nonce, actual_ciphertext, None)

            return plaintext_bytes.decode("utf-8")

        except DecryptionError:
            raise
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}")

    def _encrypt_fallback(self, plaintext: str) -> str:
        """
        Fallback encryption when cryptography is not available.

        WARNING: This is XOR-based and NOT secure. Only for testing.
        """
        nonce = os.urandom(NONCE_SIZE)
        plaintext_bytes = plaintext.encode("utf-8")

        # Simple XOR (NOT SECURE - fallback only)
        key_repeated = (self._key_bytes * (len(plaintext_bytes) // KEY_SIZE + 1))[:len(plaintext_bytes)]
        encrypted = bytes(a ^ b for a, b in zip(plaintext_bytes, key_repeated))

        # Create simple auth tag (NOT SECURE)
        tag = bytes((a + b) % 256 for a, b in zip(nonce, self._key_bytes[:NONCE_SIZE]))

        combined = nonce + encrypted + tag
        return base64.b64encode(combined).decode("utf-8")

    def _decrypt_fallback(self, ciphertext: str) -> str:
        """
        Fallback decryption when cryptography is not available.

        WARNING: This is XOR-based and NOT secure. Only for testing.
        """
        try:
            combined = base64.b64decode(ciphertext)

            if len(combined) < NONCE_SIZE + NONCE_SIZE:  # nonce + min tag
                raise DecryptionError("Ciphertext too short")

            nonce = combined[:NONCE_SIZE]
            tag = combined[-NONCE_SIZE:]
            encrypted = combined[NONCE_SIZE:-NONCE_SIZE]

            # Verify tag (NOT SECURE)
            expected_tag = bytes((a + b) % 256 for a, b in zip(nonce, self._key_bytes[:NONCE_SIZE]))
            if tag != expected_tag:
                raise DecryptionError("Authentication failed")

            # Simple XOR decrypt (NOT SECURE)
            key_repeated = (self._key_bytes * (len(encrypted) // KEY_SIZE + 1))[:len(encrypted)]
            decrypted = bytes(a ^ b for a, b in zip(encrypted, key_repeated))

            return decrypted.decode("utf-8")

        except DecryptionError:
            raise
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}")


def encrypt_field(plaintext: str, key: str) -> str:
    """
    Convenience function to encrypt a field.

    Args:
        plaintext: Text to encrypt
        key: Base64-encoded key

    Returns:
        str: Encrypted ciphertext
    """
    encryptor = FieldEncryptor(key)
    return encryptor.encrypt(plaintext)


def decrypt_field(ciphertext: str, key: str) -> str:
    """
    Convenience function to decrypt a field.

    Args:
        ciphertext: Encrypted ciphertext
        key: Base64-encoded key

    Returns:
        str: Decrypted plaintext
    """
    encryptor = FieldEncryptor(key)
    return encryptor.decrypt(ciphertext)
