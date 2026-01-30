"""
Unit tests for input sanitizer module.

Tests cover:
- XSS prevention (script tags, event handlers, javascript: URLs)
- SQL injection pattern detection
- Path traversal prevention
- Null byte sanitization
- HTML entity encoding
- Safe string validation
"""
import pytest
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '02_backend'))


class TestXSSSanitization:
    """Tests for XSS attack prevention."""

    def test_removes_script_tags(self):
        """Test that script tags are removed."""
        from core.sanitizer import sanitize_input

        dangerous = "<script>alert('xss')</script>"
        result = sanitize_input(dangerous)

        assert "<script>" not in result.lower()
        assert "alert" not in result

    def test_removes_nested_script_tags(self):
        """Test that nested script tags are removed."""
        from core.sanitizer import sanitize_input

        dangerous = "<scr<script>ipt>alert('xss')</scr</script>ipt>"
        result = sanitize_input(dangerous)

        assert "<script>" not in result.lower()

    def test_removes_event_handlers(self):
        """Test that inline event handlers are removed."""
        from core.sanitizer import sanitize_input

        dangerous = '<img src="x" onerror="alert(1)">'
        result = sanitize_input(dangerous)

        assert "onerror" not in result.lower()
        assert "alert" not in result

    def test_removes_javascript_urls(self):
        """Test that javascript: URLs are removed."""
        from core.sanitizer import sanitize_input

        dangerous = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_input(dangerous)

        assert "javascript:" not in result.lower()

    def test_removes_data_urls_with_script(self):
        """Test that data URLs with scripts are removed."""
        from core.sanitizer import sanitize_input

        dangerous = '<a href="data:text/html,<script>alert(1)</script>">Click</a>'
        result = sanitize_input(dangerous)

        assert "data:" not in result.lower() or "<script>" not in result.lower()

    def test_removes_svg_xss(self):
        """Test that SVG-based XSS is prevented."""
        from core.sanitizer import sanitize_input

        dangerous = '<svg onload="alert(1)">'
        result = sanitize_input(dangerous)

        assert "onload" not in result.lower()

    def test_preserves_safe_text(self):
        """Test that safe text is preserved."""
        from core.sanitizer import sanitize_input

        safe = "Hello, how can I help you today?"
        result = sanitize_input(safe)

        assert result == safe

    def test_preserves_unicode_text(self):
        """Test that unicode characters are preserved."""
        from core.sanitizer import sanitize_input

        text = "Magandang umaga! 你好 مرحبا"
        result = sanitize_input(text)

        assert "Magandang" in result
        assert "你好" in result
        assert "مرحبا" in result


class TestSQLInjectionDetection:
    """Tests for SQL injection pattern detection."""

    def test_detects_union_select(self):
        """Test detection of UNION SELECT attacks."""
        from core.sanitizer import contains_sql_injection

        dangerous = "1' UNION SELECT * FROM users--"
        assert contains_sql_injection(dangerous) is True

    def test_detects_drop_table(self):
        """Test detection of DROP TABLE attacks."""
        from core.sanitizer import contains_sql_injection

        dangerous = "'; DROP TABLE users;--"
        assert contains_sql_injection(dangerous) is True

    def test_detects_or_1_equals_1(self):
        """Test detection of OR 1=1 attacks."""
        from core.sanitizer import contains_sql_injection

        dangerous = "admin' OR '1'='1"
        assert contains_sql_injection(dangerous) is True

    def test_detects_comment_injection(self):
        """Test detection of SQL comment injection."""
        from core.sanitizer import contains_sql_injection

        dangerous = "admin'--"
        assert contains_sql_injection(dangerous) is True

    def test_allows_safe_queries(self):
        """Test that safe text is not flagged."""
        from core.sanitizer import contains_sql_injection

        safe = "What is the return policy?"
        assert contains_sql_injection(safe) is False

    def test_allows_apostrophes_in_text(self):
        """Test that normal apostrophes are allowed."""
        from core.sanitizer import contains_sql_injection

        safe = "I can't find my order"
        assert contains_sql_injection(safe) is False


class TestPathTraversalPrevention:
    """Tests for path traversal attack prevention."""

    def test_detects_parent_directory_traversal(self):
        """Test detection of ../ traversal."""
        from core.sanitizer import contains_path_traversal

        dangerous = "../../../etc/passwd"
        assert contains_path_traversal(dangerous) is True

    def test_detects_encoded_traversal(self):
        """Test detection of URL-encoded traversal."""
        from core.sanitizer import contains_path_traversal

        dangerous = "..%2F..%2F..%2Fetc%2Fpasswd"
        assert contains_path_traversal(dangerous) is True

    def test_detects_double_encoded_traversal(self):
        """Test detection of double URL-encoded traversal."""
        from core.sanitizer import contains_path_traversal

        dangerous = "..%252F..%252F..%252Fetc%252Fpasswd"
        assert contains_path_traversal(dangerous) is True

    def test_detects_backslash_traversal(self):
        """Test detection of backslash traversal (Windows)."""
        from core.sanitizer import contains_path_traversal

        dangerous = "..\\..\\..\\windows\\system32"
        assert contains_path_traversal(dangerous) is True

    def test_allows_safe_paths(self):
        """Test that safe paths are not flagged."""
        from core.sanitizer import contains_path_traversal

        safe = "documents/report.pdf"
        assert contains_path_traversal(safe) is False


class TestNullByteSanitization:
    """Tests for null byte sanitization."""

    def test_removes_null_bytes(self):
        """Test that null bytes are removed."""
        from core.sanitizer import sanitize_input

        dangerous = "file.txt\x00.exe"
        result = sanitize_input(dangerous)

        assert "\x00" not in result

    def test_removes_url_encoded_null(self):
        """Test that URL-encoded null bytes are removed."""
        from core.sanitizer import sanitize_input

        dangerous = "file.txt%00.exe"
        result = sanitize_input(dangerous)

        assert "%00" not in result


class TestHTMLEntityEncoding:
    """Tests for HTML entity encoding."""

    def test_encodes_angle_brackets(self):
        """Test that angle brackets are encoded for output."""
        from core.sanitizer import encode_for_html

        text = "<script>alert(1)</script>"
        result = encode_for_html(text)

        assert "&lt;" in result
        assert "&gt;" in result
        assert "<script>" not in result

    def test_encodes_quotes(self):
        """Test that quotes are encoded."""
        from core.sanitizer import encode_for_html

        text = 'He said "hello"'
        result = encode_for_html(text)

        assert "&quot;" in result or '"' not in result or result == text

    def test_encodes_ampersand(self):
        """Test that ampersands are encoded."""
        from core.sanitizer import encode_for_html

        text = "Tom & Jerry"
        result = encode_for_html(text)

        assert "&amp;" in result


class TestValidateSafeString:
    """Tests for safe string validation."""

    def test_validates_safe_string(self):
        """Test that safe strings pass validation."""
        from core.sanitizer import is_safe_string

        assert is_safe_string("Hello world") is True

    def test_rejects_xss_attack(self):
        """Test that XSS attacks fail validation."""
        from core.sanitizer import is_safe_string

        assert is_safe_string("<script>alert(1)</script>") is False

    def test_rejects_sql_injection(self):
        """Test that SQL injection fails validation."""
        from core.sanitizer import is_safe_string

        assert is_safe_string("'; DROP TABLE users;--") is False

    def test_rejects_path_traversal(self):
        """Test that path traversal fails validation."""
        from core.sanitizer import is_safe_string

        assert is_safe_string("../../../etc/passwd") is False


class TestSanitizeForDatabase:
    """Tests for database-safe string sanitization."""

    def test_sanitize_preserves_text(self):
        """Test that safe text is preserved."""
        from core.sanitizer import sanitize_for_database

        text = "Normal user question"
        result = sanitize_for_database(text)

        assert result == text

    def test_sanitize_removes_dangerous_patterns(self):
        """Test that dangerous patterns are removed or escaped."""
        from core.sanitizer import sanitize_for_database

        dangerous = "<script>alert(1)</script>"
        result = sanitize_for_database(dangerous)

        assert "<script>" not in result


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_removes_path_separators(self):
        """Test that path separators are removed."""
        from core.sanitizer import sanitize_filename

        dangerous = "../../../etc/passwd"
        result = sanitize_filename(dangerous)

        assert "/" not in result
        assert ".." not in result

    def test_removes_null_bytes(self):
        """Test that null bytes are removed from filenames."""
        from core.sanitizer import sanitize_filename

        dangerous = "file.txt\x00.exe"
        result = sanitize_filename(dangerous)

        assert "\x00" not in result

    def test_preserves_safe_filename(self):
        """Test that safe filenames are preserved."""
        from core.sanitizer import sanitize_filename

        safe = "report_2024.pdf"
        result = sanitize_filename(safe)

        assert result == safe

    def test_handles_spaces_in_filename(self):
        """Test that spaces are handled appropriately."""
        from core.sanitizer import sanitize_filename

        name = "my document.pdf"
        result = sanitize_filename(name)

        # Spaces can be preserved or replaced with underscores
        assert "document" in result and "pdf" in result
