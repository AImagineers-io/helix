"""
Unit tests for File Upload Validation (P12.2.3)

Tests file validation including:
- File type validation (magic bytes)
- Extension whitelist
- Virus scan hook
- Allowed types: CSV, JSON, TXT for QA import
"""
import pytest
from io import BytesIO

from services.file_validator import (
    FileValidator,
    FileValidationError,
    is_allowed_extension,
    validate_magic_bytes,
    ALLOWED_EXTENSIONS,
    MAGIC_BYTES,
)


class TestAllowedExtensions:
    """Tests for extension validation."""

    def test_csv_extension_allowed(self):
        """CSV files should be allowed."""
        assert is_allowed_extension("data.csv") is True
        assert is_allowed_extension("DATA.CSV") is True

    def test_json_extension_allowed(self):
        """JSON files should be allowed."""
        assert is_allowed_extension("data.json") is True
        assert is_allowed_extension("config.JSON") is True

    def test_txt_extension_allowed(self):
        """TXT files should be allowed."""
        assert is_allowed_extension("readme.txt") is True
        assert is_allowed_extension("README.TXT") is True

    def test_exe_extension_rejected(self):
        """Executable files should be rejected."""
        assert is_allowed_extension("program.exe") is False

    def test_php_extension_rejected(self):
        """PHP files should be rejected."""
        assert is_allowed_extension("script.php") is False

    def test_double_extension_rejected(self):
        """Double extensions should be checked properly."""
        assert is_allowed_extension("file.txt.exe") is False
        assert is_allowed_extension("file.csv.php") is False

    def test_no_extension_rejected(self):
        """Files without extension should be rejected."""
        assert is_allowed_extension("noextension") is False


class TestMagicBytes:
    """Tests for magic byte (file signature) validation."""

    def test_csv_content_detected(self):
        """CSV content should be detected."""
        content = b"name,value\ntest,123"
        assert validate_magic_bytes(content, ".csv") is True

    def test_json_object_detected(self):
        """JSON object should be detected."""
        content = b'{"key": "value"}'
        assert validate_magic_bytes(content, ".json") is True

    def test_json_array_detected(self):
        """JSON array should be detected."""
        content = b'[{"key": "value"}]'
        assert validate_magic_bytes(content, ".json") is True

    def test_txt_content_allowed(self):
        """Plain text content should be allowed."""
        content = b"This is plain text content."
        assert validate_magic_bytes(content, ".txt") is True

    def test_executable_content_rejected(self):
        """Executable content should be rejected."""
        # PE header (Windows executable)
        content = b"MZ\x90\x00..."
        assert validate_magic_bytes(content, ".txt") is False

    def test_elf_binary_rejected(self):
        """ELF binary content should be rejected."""
        content = b"\x7fELF..."
        assert validate_magic_bytes(content, ".txt") is False

    def test_zip_content_rejected(self):
        """ZIP content should be rejected for text files."""
        content = b"PK\x03\x04..."
        assert validate_magic_bytes(content, ".txt") is False


class TestFileValidator:
    """Tests for FileValidator class."""

    @pytest.fixture
    def validator(self):
        """Create file validator instance."""
        return FileValidator()

    def test_validate_valid_csv(self, validator):
        """Valid CSV file should pass validation."""
        content = b"name,email\njohn,john@test.com"
        result = validator.validate(content, "contacts.csv")
        assert result.is_valid is True

    def test_validate_valid_json(self, validator):
        """Valid JSON file should pass validation."""
        content = b'[{"question": "Q1", "answer": "A1"}]'
        result = validator.validate(content, "qa.json")
        assert result.is_valid is True

    def test_validate_invalid_extension(self, validator):
        """Invalid extension should fail validation."""
        content = b"some content"
        result = validator.validate(content, "script.exe")
        assert result.is_valid is False
        assert "extension" in result.error.lower()

    def test_validate_mismatched_content(self, validator):
        """Mismatched content type should fail validation."""
        # Claim to be CSV but actually executable content
        content = b"MZ\x90\x00..."  # PE header
        result = validator.validate(content, "data.csv")
        assert result.is_valid is False
        assert "content" in result.error.lower() or "magic" in result.error.lower()

    def test_validate_empty_file(self, validator):
        """Empty file should fail validation."""
        content = b""
        result = validator.validate(content, "empty.csv")
        assert result.is_valid is False
        assert "empty" in result.error.lower()

    def test_validate_max_size_enforced(self, validator):
        """Files exceeding max size should fail."""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        result = validator.validate(large_content, "large.csv")
        assert result.is_valid is False
        assert "size" in result.error.lower()


class TestVirusScanHook:
    """Tests for virus scan hook integration."""

    def test_scan_hook_called_when_configured(self):
        """Virus scan hook should be called when provided."""
        scan_called = False
        scan_content = None

        def mock_scanner(content: bytes) -> bool:
            nonlocal scan_called, scan_content
            scan_called = True
            scan_content = content
            return True  # Clean

        validator = FileValidator(virus_scan_hook=mock_scanner)
        content = b"name,value\ntest,123"  # Valid CSV content
        validator.validate(content, "test.csv")

        assert scan_called is True
        assert scan_content == content

    def test_scan_failure_rejects_file(self):
        """File should be rejected if virus scan fails."""
        def mock_scanner(content: bytes) -> bool:
            return False  # Infected

        validator = FileValidator(virus_scan_hook=mock_scanner)
        result = validator.validate(b"name,value\ntest,123", "test.csv")

        assert result.is_valid is False
        assert "virus" in result.error.lower() or "malware" in result.error.lower()
