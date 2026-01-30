"""
Prompt validation service.

Provides validation for prompt content, types, and names before saving.
"""
import re
from dataclasses import dataclass, field
from typing import List

from core.constants import PromptType


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether the validation passed.
        errors: List of error messages if validation failed.
    """

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)


class PromptValidator:
    """Validator for prompt templates and content.

    Provides static methods for validating prompt content, types, and names
    before saving to the database.

    Constants:
        MAX_CONTENT_LENGTH: Maximum allowed content length (10,000 chars).
        MAX_NAME_LENGTH: Maximum allowed name length (255 chars).
    """

    MAX_CONTENT_LENGTH = 10000
    MAX_NAME_LENGTH = 255

    # Pattern to find template variables like {variable_name}
    # Matches valid variable references
    VARIABLE_PATTERN = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    # Pattern to find malformed braces (unclosed or empty)
    UNCLOSED_BRACE_PATTERN = re.compile(r'\{[^}]*$|^[^{]*\}')
    EMPTY_VARIABLE_PATTERN = re.compile(r'\{\s*\}')

    @classmethod
    def validate_content(cls, content: str) -> ValidationResult:
        """Validate prompt content.

        Validates:
        - Content is not empty or whitespace-only
        - Content does not exceed MAX_CONTENT_LENGTH
        - Template variables have valid syntax

        Args:
            content: Prompt content to validate.

        Returns:
            ValidationResult with is_valid flag and any errors.
        """
        errors: List[str] = []

        # Check for empty content
        if not content or not content.strip():
            errors.append("Content cannot be empty")
            return ValidationResult(is_valid=False, errors=errors)

        # Check length
        if len(content) > cls.MAX_CONTENT_LENGTH:
            errors.append(
                f"Content exceeds maximum length of {cls.MAX_CONTENT_LENGTH:,} characters"
            )

        # Check template variable syntax
        variable_errors = cls._validate_template_variables(content)
        errors.extend(variable_errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    @classmethod
    def _validate_template_variables(cls, content: str) -> List[str]:
        """Validate template variable syntax in content.

        Args:
            content: Content to check for template variables.

        Returns:
            List of error messages for invalid variables.
        """
        errors: List[str] = []

        # Check for empty variable names {}
        if cls.EMPTY_VARIABLE_PATTERN.search(content):
            errors.append("Empty template variable name found ({})")

        # Check for unclosed braces by counting
        # We need to be smart about this because JSON-like content is allowed
        open_braces = 0
        in_variable = False
        for i, char in enumerate(content):
            if char == '{':
                # Check if this could be a template variable start
                # Look ahead to see if it matches our pattern
                remaining = content[i:]
                if cls.VARIABLE_PATTERN.match(remaining):
                    in_variable = True
                    open_braces += 1
                elif remaining.startswith('{') and len(remaining) > 1:
                    # Could be JSON - look for closing brace
                    next_close = remaining.find('}')
                    if next_close == -1:
                        errors.append(
                            "Unclosed template variable brace found"
                        )
                        break
            elif char == '}' and in_variable:
                open_braces -= 1
                if open_braces == 0:
                    in_variable = False

        return errors

    @classmethod
    def validate_type(cls, prompt_type: str) -> ValidationResult:
        """Validate prompt type against allowed types.

        Args:
            prompt_type: Type string to validate.

        Returns:
            ValidationResult with is_valid flag and any errors.
        """
        if PromptType.is_valid_type(prompt_type):
            return ValidationResult(is_valid=True)

        valid_types = ", ".join(PromptType.get_all_types())
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid prompt type '{prompt_type}'. Valid types: {valid_types}"]
        )

    @classmethod
    def validate_name(cls, name: str) -> ValidationResult:
        """Validate prompt template name.

        Validates:
        - Name is not empty
        - Name does not exceed MAX_NAME_LENGTH

        Args:
            name: Template name to validate.

        Returns:
            ValidationResult with is_valid flag and any errors.
        """
        errors: List[str] = []

        if not name or not name.strip():
            errors.append("Name cannot be empty")
            return ValidationResult(is_valid=False, errors=errors)

        if len(name) > cls.MAX_NAME_LENGTH:
            errors.append(
                f"Name exceeds maximum length of {cls.MAX_NAME_LENGTH} characters"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    @classmethod
    def validate_all(
        cls,
        name: str,
        prompt_type: str,
        content: str
    ) -> ValidationResult:
        """Validate all prompt fields at once.

        Args:
            name: Template name.
            prompt_type: Prompt type.
            content: Prompt content.

        Returns:
            ValidationResult with combined errors from all validations.
        """
        all_errors: List[str] = []

        name_result = cls.validate_name(name)
        all_errors.extend(name_result.errors)

        type_result = cls.validate_type(prompt_type)
        all_errors.extend(type_result.errors)

        content_result = cls.validate_content(content)
        all_errors.extend(content_result.errors)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors
        )
