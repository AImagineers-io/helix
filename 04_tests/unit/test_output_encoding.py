"""
Unit tests for Output Encoding (P12.2.5)

Tests output encoding including:
- HTML entity encoding for web responses
- JSON escape for API responses
- LLM output encoding
- User-generated content encoding
"""
import pytest

from core.encoder import (
    encode_html,
    encode_json_string,
    encode_for_api,
    encode_llm_output,
    OutputEncoder,
)


class TestHTMLEncoding:
    """Tests for HTML entity encoding."""

    def test_encodes_less_than(self):
        """< should be encoded as &lt;"""
        assert encode_html("<script>") == "&lt;script&gt;"

    def test_encodes_greater_than(self):
        """> should be encoded as &gt;"""
        assert encode_html("<div>test</div>") == "&lt;div&gt;test&lt;/div&gt;"

    def test_encodes_ampersand(self):
        """& should be encoded as &amp;"""
        assert encode_html("Tom & Jerry") == "Tom &amp; Jerry"

    def test_encodes_quotes(self):
        """Quotes should be encoded."""
        assert encode_html('Say "hello"') == "Say &quot;hello&quot;"
        assert encode_html("It's") == "It&#x27;s"

    def test_preserves_safe_text(self):
        """Safe text should be unchanged."""
        text = "Hello World 123"
        assert encode_html(text) == text

    def test_handles_none(self):
        """None should return empty string."""
        assert encode_html(None) == ""

    def test_handles_empty_string(self):
        """Empty string should return empty string."""
        assert encode_html("") == ""

    def test_encodes_script_tag(self):
        """Script tags should be fully encoded."""
        malicious = "<script>alert('xss')</script>"
        encoded = encode_html(malicious)
        assert "<script>" not in encoded
        assert "</script>" not in encoded


class TestJSONEncoding:
    """Tests for JSON string encoding."""

    def test_escapes_backslash(self):
        """Backslashes should be escaped."""
        assert encode_json_string("path\\to\\file") == "path\\\\to\\\\file"

    def test_escapes_quotes(self):
        """Quotes should be escaped."""
        assert encode_json_string('say "hi"') == 'say \\"hi\\"'

    def test_escapes_newlines(self):
        """Newlines should be escaped."""
        assert encode_json_string("line1\nline2") == "line1\\nline2"

    def test_escapes_tabs(self):
        """Tabs should be escaped."""
        assert encode_json_string("col1\tcol2") == "col1\\tcol2"

    def test_escapes_carriage_return(self):
        """Carriage returns should be escaped."""
        assert encode_json_string("line1\rline2") == "line1\\rline2"

    def test_preserves_safe_text(self):
        """Safe text should be unchanged."""
        text = "Hello World 123"
        assert encode_json_string(text) == text

    def test_handles_unicode(self):
        """Unicode should be preserved (may be escaped)."""
        text = "Hello \u4e16\u754c"  # Hello 世界
        result = encode_json_string(text)
        # Unicode may be preserved or escaped as \\uXXXX
        # Either representation is valid JSON
        assert "Hello" in result
        # The result should be valid when used in JSON
        import json
        test_json = '{"text": "' + result + '"}'
        parsed = json.loads(test_json)
        assert parsed["text"] == text


class TestAPIEncoding:
    """Tests for API response encoding."""

    def test_encodes_string_values(self):
        """String values in dict should be encoded."""
        data = {"message": "<script>alert('xss')</script>"}
        encoded = encode_for_api(data)
        assert "<script>" not in encoded["message"]

    def test_encodes_nested_strings(self):
        """Nested string values should be encoded."""
        data = {"user": {"bio": "<b>bold</b>"}}
        encoded = encode_for_api(data)
        assert "<b>" not in encoded["user"]["bio"]

    def test_encodes_list_items(self):
        """List items should be encoded."""
        data = {"items": ["<a>link</a>", "normal"]}
        encoded = encode_for_api(data)
        assert "<a>" not in encoded["items"][0]
        assert encoded["items"][1] == "normal"

    def test_preserves_non_strings(self):
        """Non-string values should be preserved."""
        data = {"count": 42, "active": True, "ratio": 3.14}
        encoded = encode_for_api(data)
        assert encoded["count"] == 42
        assert encoded["active"] is True
        assert encoded["ratio"] == 3.14


class TestLLMOutputEncoding:
    """Tests for LLM output encoding."""

    def test_encodes_html_in_response(self):
        """HTML in LLM response should be encoded."""
        llm_output = "Try running <code>python script.py</code>"
        encoded = encode_llm_output(llm_output)
        assert "<code>" not in encoded

    def test_removes_script_tags(self):
        """Script tags should be removed from LLM output."""
        llm_output = "Here's info<script>evil()</script> about topic"
        encoded = encode_llm_output(llm_output)
        assert "script" not in encoded.lower()

    def test_preserves_markdown(self):
        """Markdown formatting should be preserved."""
        llm_output = "**bold** and *italic*"
        encoded = encode_llm_output(llm_output)
        assert "**bold**" in encoded
        assert "*italic*" in encoded

    def test_encodes_markdown_link_xss(self):
        """XSS in markdown links should be encoded."""
        llm_output = "[Click](javascript:alert(1))"
        encoded = encode_llm_output(llm_output)
        assert "javascript:" not in encoded.lower()


class TestOutputEncoder:
    """Tests for OutputEncoder class."""

    @pytest.fixture
    def encoder(self):
        """Create output encoder instance."""
        return OutputEncoder()

    def test_encode_for_html_context(self, encoder):
        """HTML context should use HTML encoding."""
        result = encoder.encode("<script>", context="html")
        assert "<script>" not in result

    def test_encode_for_json_context(self, encoder):
        """JSON context should use JSON encoding."""
        result = encoder.encode('say "hi"', context="json")
        assert '\\"' in result

    def test_encode_for_llm_context(self, encoder):
        """LLM context should use LLM encoding."""
        result = encoder.encode("<script>", context="llm")
        assert "<script>" not in result

    def test_encode_defaults_to_html(self, encoder):
        """Default context should be HTML."""
        result = encoder.encode("<b>test</b>")
        assert "<b>" not in result
