"""
Unit tests for LLM Output Sanitization (P12.3.2)

Tests LLM output sanitization including:
- Script tag removal
- Markdown exploit prevention
- Response length validation
- Format compliance
"""
import pytest

from services.chat.processors.output_sanitizer import (
    LLMOutputSanitizer,
    sanitize_llm_output,
    remove_script_tags,
    sanitize_markdown,
    validate_response_length,
)


class TestScriptTagRemoval:
    """Tests for script tag removal."""

    def test_removes_script_tags(self):
        """Script tags should be removed."""
        text = "Hello<script>evil()</script>World"
        result = remove_script_tags(text)
        assert "<script>" not in result
        assert "</script>" not in result
        assert "HelloWorld" in result

    def test_removes_inline_scripts(self):
        """Inline script with content should be removed."""
        text = "Info<script type='text/javascript'>alert(1)</script>more"
        result = remove_script_tags(text)
        assert "script" not in result.lower()
        assert "alert" not in result

    def test_removes_multiline_scripts(self):
        """Multiline scripts should be removed."""
        text = """
        Before
        <script>
            var x = 1;
            doEvil();
        </script>
        After
        """
        result = remove_script_tags(text)
        assert "<script>" not in result
        assert "doEvil" not in result
        assert "Before" in result
        assert "After" in result

    def test_handles_no_scripts(self):
        """Text without scripts should be unchanged."""
        text = "Just normal text here."
        result = remove_script_tags(text)
        assert result == text


class TestMarkdownSanitization:
    """Tests for markdown exploit prevention."""

    def test_removes_javascript_links(self):
        """JavaScript: links should be removed."""
        text = "[Click me](javascript:alert(1))"
        result = sanitize_markdown(text)
        assert "javascript:" not in result.lower()

    def test_preserves_normal_links(self):
        """Normal HTTPS links should be preserved."""
        text = "[Google](https://google.com)"
        result = sanitize_markdown(text)
        assert "https://google.com" in result

    def test_removes_data_urls_in_images(self):
        """data: URLs in images should be removed."""
        text = "![img](data:text/html,<script>)</img>"
        result = sanitize_markdown(text)
        assert "data:text/html" not in result

    def test_preserves_code_blocks(self):
        """Code blocks should be preserved."""
        text = "```python\nprint('hello')\n```"
        result = sanitize_markdown(text)
        assert "```python" in result
        assert "print" in result


class TestResponseLengthValidation:
    """Tests for response length validation."""

    def test_short_response_passes(self):
        """Short responses should pass validation."""
        result = validate_response_length("Short response", max_length=1000)
        assert result.is_valid is True

    def test_long_response_truncated(self):
        """Long responses should be truncated."""
        long_text = "x" * 2000
        result = validate_response_length(long_text, max_length=1000)
        assert result.is_valid is True
        assert len(result.text) <= 1000
        assert result.was_truncated is True

    def test_truncation_adds_indicator(self):
        """Truncated responses should indicate truncation."""
        long_text = "x" * 2000
        result = validate_response_length(long_text, max_length=1000)
        assert "..." in result.text or "[truncated]" in result.text.lower()


class TestLLMOutputSanitizer:
    """Tests for the full sanitizer class."""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance."""
        return LLMOutputSanitizer()

    def test_sanitize_removes_all_threats(self, sanitizer):
        """Sanitizer should remove all threat types."""
        malicious = """
        Here's info <script>steal(cookies)</script>
        Click [here](javascript:evil()) for more.
        """
        result = sanitizer.sanitize(malicious)
        assert "<script>" not in result.text
        assert "javascript:" not in result.text.lower()

    def test_sanitize_preserves_safe_content(self, sanitizer):
        """Sanitizer should preserve safe content."""
        safe = "Here's a **bold** answer with `code`."
        result = sanitizer.sanitize(safe)
        assert "**bold**" in result.text
        assert "`code`" in result.text

    def test_sanitize_returns_result_object(self, sanitizer):
        """Sanitizer should return result with metadata."""
        result = sanitizer.sanitize("Test content")
        assert hasattr(result, 'text')
        assert hasattr(result, 'was_modified')


class TestSanitizeLLMOutput:
    """Tests for the convenience function."""

    def test_sanitize_llm_output_basic(self):
        """Basic sanitization should work."""
        result = sanitize_llm_output("Hello <script>bad</script> world")
        assert "script" not in result.lower()
        assert "Hello" in result
        assert "world" in result
