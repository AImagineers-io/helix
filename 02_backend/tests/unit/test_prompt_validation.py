"""
Unit tests for Prompt Validation Service.

Tests that prompt content is properly validated before saving.
"""
import pytest


class TestPromptValidator:
    """Test suite for PromptValidator service."""

    def test_validate_content_accepts_valid_prompt(self):
        """Test that validation passes for valid prompt content."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_content("You are a helpful assistant.")

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_content_rejects_empty_content(self):
        """Test that validation fails for empty content."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_content("")

        assert result.is_valid is False
        assert "Content cannot be empty" in result.errors

    def test_validate_content_rejects_whitespace_only(self):
        """Test that validation fails for whitespace-only content."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_content("   \n\t  ")

        assert result.is_valid is False
        assert "Content cannot be empty" in result.errors

    def test_validate_content_rejects_content_exceeding_max_length(self):
        """Test that validation fails for content exceeding 10,000 chars."""
        from services.prompt_validator import PromptValidator

        long_content = "a" * 10001
        result = PromptValidator.validate_content(long_content)

        assert result.is_valid is False
        assert any("10,000 characters" in e for e in result.errors)

    def test_validate_content_accepts_content_at_max_length(self):
        """Test that validation passes for content at exactly 10,000 chars."""
        from services.prompt_validator import PromptValidator

        max_content = "a" * 10000
        result = PromptValidator.validate_content(max_content)

        assert result.is_valid is True

    def test_validate_content_accepts_valid_template_variables(self):
        """Test that validation passes for valid template variables."""
        from services.prompt_validator import PromptValidator

        content = "Hello {user_name}, your order {order_id} is ready."
        result = PromptValidator.validate_content(content)

        assert result.is_valid is True

    def test_validate_content_rejects_invalid_template_variables(self):
        """Test that validation fails for invalid template variable syntax."""
        from services.prompt_validator import PromptValidator

        # Missing closing brace
        result = PromptValidator.validate_content("Hello {user_name, welcome!")

        assert result.is_valid is False
        assert any("template variable" in e.lower() for e in result.errors)

    def test_validate_content_rejects_empty_variable_names(self):
        """Test that validation fails for empty variable names like {}."""
        from services.prompt_validator import PromptValidator

        content = "Hello {}, welcome!"
        result = PromptValidator.validate_content(content)

        assert result.is_valid is False
        assert any("variable" in e.lower() for e in result.errors)

    def test_validate_content_accepts_nested_braces_in_text(self):
        """Test that validation handles JSON-like content correctly."""
        from services.prompt_validator import PromptValidator

        content = 'Respond with JSON: {"status": "ok"}'
        result = PromptValidator.validate_content(content)

        assert result.is_valid is True

    def test_validate_content_collects_multiple_errors(self):
        """Test that validation collects all errors, not just the first."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_content("")

        assert result.is_valid is False
        assert len(result.errors) >= 1


class TestPromptValidatorType:
    """Test suite for prompt type validation."""

    def test_validate_type_accepts_valid_type(self):
        """Test that validation passes for valid prompt types."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_type("system_prompt")

        assert result.is_valid is True

    def test_validate_type_rejects_invalid_type(self):
        """Test that validation fails for invalid prompt types."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_type("invalid_type")

        assert result.is_valid is False
        assert any("Invalid prompt type" in e for e in result.errors)

    def test_validate_type_lists_valid_types_in_error(self):
        """Test that error message lists valid types."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_type("bad_type")

        assert result.is_valid is False
        error_message = " ".join(result.errors).lower()
        assert "system_prompt" in error_message or "valid" in error_message


class TestPromptValidatorName:
    """Test suite for prompt name validation."""

    def test_validate_name_accepts_valid_name(self):
        """Test that validation passes for valid names."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_name("my_system_prompt")

        assert result.is_valid is True

    def test_validate_name_rejects_empty_name(self):
        """Test that validation fails for empty names."""
        from services.prompt_validator import PromptValidator

        result = PromptValidator.validate_name("")

        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_name_rejects_too_long_name(self):
        """Test that validation fails for names exceeding 255 chars."""
        from services.prompt_validator import PromptValidator

        long_name = "a" * 256
        result = PromptValidator.validate_name(long_name)

        assert result.is_valid is False
        assert any("255" in e for e in result.errors)


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""

    def test_validation_result_is_valid_default(self):
        """Test that ValidationResult defaults to valid with no errors."""
        from services.prompt_validator import ValidationResult

        result = ValidationResult()

        assert result.is_valid is True
        assert result.errors == []

    def test_validation_result_with_errors(self):
        """Test creating ValidationResult with errors."""
        from services.prompt_validator import ValidationResult

        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"]
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
