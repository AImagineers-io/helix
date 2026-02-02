"""
File Upload Validation Service for secure file handling.

Provides:
- File type validation using magic bytes (not just extension)
- Extension whitelist enforcement
- Optional virus scan hook integration
- Size limit enforcement

Allowed file types for QA import:
- CSV: Comma-separated values
- JSON: JavaScript Object Notation
- TXT: Plain text files
"""
from dataclasses import dataclass
from typing import Callable, Optional
import re

# Allowed file extensions (case-insensitive)
ALLOWED_EXTENSIONS = {".csv", ".json", ".txt"}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Magic bytes/signatures for file type detection
MAGIC_BYTES = {
    # Dangerous file signatures to reject
    "pe_exe": b"MZ",  # Windows executable
    "elf": b"\x7fELF",  # Linux executable
    "zip": b"PK\x03\x04",  # ZIP archive
    "gzip": b"\x1f\x8b",  # GZIP
    "rar": b"Rar!",  # RAR archive
    "pdf": b"%PDF",  # PDF (could contain exploits)
}


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


@dataclass
class ValidationResult:
    """Result of file validation."""
    is_valid: bool
    error: str = ""
    file_type: Optional[str] = None


def is_allowed_extension(filename: str) -> bool:
    """
    Check if file extension is in the whitelist.

    Args:
        filename: Name of the file

    Returns:
        bool: True if extension is allowed
    """
    if not filename or "." not in filename:
        return False

    # Get the final extension (handles double extensions)
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_magic_bytes(content: bytes, extension: str) -> bool:
    """
    Validate file content matches expected type.

    Checks for dangerous file signatures that shouldn't be in text files.

    Args:
        content: File content bytes
        extension: Expected file extension

    Returns:
        bool: True if content appears valid for the extension
    """
    if not content:
        return False

    # Check for dangerous file signatures
    for sig_name, signature in MAGIC_BYTES.items():
        if content.startswith(signature):
            return False

    # Additional checks based on extension
    ext = extension.lower()

    if ext == ".json":
        # JSON should start with { or [ (after stripping whitespace)
        stripped = content.lstrip()
        if stripped and stripped[0:1] not in (b"{", b"["):
            return False

    if ext == ".csv":
        # CSV should be mostly printable ASCII with commas
        try:
            # Check first 1KB for basic structure
            sample = content[:1024]
            decoded = sample.decode("utf-8", errors="ignore")
            # Should have at least one comma or newline
            if "," not in decoded and "\n" not in decoded:
                return False
        except Exception:
            return False

    return True


class FileValidator:
    """
    Validates uploaded files for security.

    Checks:
    1. Extension is in whitelist
    2. Content matches expected type (magic bytes)
    3. File is not empty
    4. File is not too large
    5. Optional virus scan

    Attributes:
        max_size: Maximum allowed file size
        virus_scan_hook: Optional function to scan for malware
    """

    def __init__(
        self,
        max_size: int = MAX_FILE_SIZE,
        virus_scan_hook: Optional[Callable[[bytes], bool]] = None
    ):
        """
        Initialize file validator.

        Args:
            max_size: Maximum file size in bytes
            virus_scan_hook: Function that returns True if file is clean
        """
        self.max_size = max_size
        self.virus_scan_hook = virus_scan_hook

    def validate(self, content: bytes, filename: str) -> ValidationResult:
        """
        Validate an uploaded file.

        Args:
            content: File content as bytes
            filename: Original filename

        Returns:
            ValidationResult: Validation result with status and error
        """
        # Check for empty file
        if not content:
            return ValidationResult(
                is_valid=False,
                error="File is empty"
            )

        # Check file size
        if len(content) > self.max_size:
            return ValidationResult(
                is_valid=False,
                error=f"File size ({len(content)} bytes) exceeds maximum ({self.max_size} bytes)"
            )

        # Check extension
        if not is_allowed_extension(filename):
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            return ValidationResult(
                is_valid=False,
                error=f"File extension not allowed. Allowed extensions: {allowed}"
            )

        # Get extension for content validation
        ext = "." + filename.rsplit(".", 1)[-1].lower()

        # Check magic bytes / content type
        if not validate_magic_bytes(content, ext):
            return ValidationResult(
                is_valid=False,
                error="File content does not match expected type or contains dangerous signatures"
            )

        # Run virus scan if configured
        if self.virus_scan_hook is not None:
            is_clean = self.virus_scan_hook(content)
            if not is_clean:
                return ValidationResult(
                    is_valid=False,
                    error="File failed virus/malware scan"
                )

        return ValidationResult(
            is_valid=True,
            file_type=ext[1:]  # Remove leading dot
        )
