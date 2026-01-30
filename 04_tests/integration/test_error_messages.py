"""Error message audit tests (P4.6a).

Verifies that exception messages and error responses don't contain
client-specific branding terms (palai, philrice).
"""
import subprocess
from pathlib import Path

import pytest


class TestExceptionMessages:
    """Audit exception messages for prohibited terms."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    BACKEND_DIR = PROJECT_ROOT / "02_backend"

    PROHIBITED_TERMS = ["palai", "philrice"]

    def _grep_for_term_in_exceptions(self, term: str) -> list[str]:
        """Search for prohibited term in exception strings."""
        # Look for raise statements with the term
        patterns = [
            f'raise.*"{term}',
            f"raise.*'{term}",
            f'Exception.*"{term}',
            f"Exception.*'{term}",
            f'Error.*"{term}',
            f"Error.*'{term}",
        ]

        found_files = []
        for pattern in patterns:
            result = subprocess.run(
                ["grep", "-r", "-i", "-l", "--include=*.py", pattern, str(self.BACKEND_DIR)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                found_files.extend(result.stdout.strip().split("\n"))

        return list(set(found_files))

    def test_no_palai_in_exceptions(self):
        """Exception messages should not contain 'palai'."""
        files = self._grep_for_term_in_exceptions("palai")
        if files:
            pytest.fail(
                f"Found 'palai' in exception messages:\n" +
                "\n".join(f"  - {f}" for f in files)
            )

    def test_no_philrice_in_exceptions(self):
        """Exception messages should not contain 'philrice'."""
        files = self._grep_for_term_in_exceptions("philrice")
        if files:
            pytest.fail(
                f"Found 'philrice' in exception messages:\n" +
                "\n".join(f"  - {f}" for f in files)
            )


class TestValidationErrorMessages:
    """Audit validation error messages."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    BACKEND_DIR = PROJECT_ROOT / "02_backend"

    def _grep_validation_messages(self, term: str) -> list[str]:
        """Search for term in validation message strings."""
        patterns = [
            f'ValidationError.*"{term}',
            f"ValidationError.*'{term}",
            f'HTTPException.*"{term}',
            f"HTTPException.*'{term}",
            f'detail=.*"{term}',
            f"detail=.*'{term}",
        ]

        found_files = []
        for pattern in patterns:
            result = subprocess.run(
                ["grep", "-r", "-i", "-l", "--include=*.py", pattern, str(self.BACKEND_DIR)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                found_files.extend(result.stdout.strip().split("\n"))

        return list(set(found_files))

    def test_no_palai_in_validation_errors(self):
        """Validation errors should not contain 'palai'."""
        files = self._grep_validation_messages("palai")
        if files:
            pytest.fail(
                f"Found 'palai' in validation error messages:\n" +
                "\n".join(f"  - {f}" for f in files)
            )


class TestLogMessages:
    """Audit log messages for prohibited terms."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    BACKEND_DIR = PROJECT_ROOT / "02_backend"

    def _grep_log_messages(self, term: str) -> list[str]:
        """Search for term in log messages."""
        patterns = [
            f'logger\\..*"{term}',
            f"logger\\..*'{term}",
            f'logging\\..*"{term}',
            f"logging\\..*'{term}",
            f'log\\..*"{term}',
            f"log\\..*'{term}",
        ]

        found_files = []
        for pattern in patterns:
            result = subprocess.run(
                ["grep", "-r", "-i", "-l", "--include=*.py", pattern, str(self.BACKEND_DIR)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                found_files.extend(result.stdout.strip().split("\n"))

        return list(set(found_files))

    def test_no_palai_in_log_messages(self):
        """Log messages should not contain 'palai'."""
        files = self._grep_log_messages("palai")
        if files:
            pytest.fail(
                f"Found 'palai' in log messages:\n" +
                "\n".join(f"  - {f}" for f in files)
            )


class TestUserFacingMessages:
    """Audit user-facing messages in responses."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_prompts_seeds_no_palai(self):
        """Prompt seeds should not contain 'palai'."""
        seeds_dir = self.PROJECT_ROOT / "02_backend" / "database" / "seeds"
        if not seeds_dir.exists():
            pytest.skip("Seeds directory not found")

        for seed_file in seeds_dir.glob("*.py"):
            content = seed_file.read_text().lower()
            assert "palai" not in content, \
                f"Seed file {seed_file.name} contains 'palai'"
            assert "philrice" not in content, \
                f"Seed file {seed_file.name} contains 'philrice'"

    def test_config_defaults_no_palai(self):
        """Config defaults should not contain 'palai'."""
        config_files = [
            self.PROJECT_ROOT / "02_backend" / "core" / "config.py",
            self.PROJECT_ROOT / "02_backend" / "core" / "constants.py",
        ]

        for config_file in config_files:
            if config_file.exists():
                content = config_file.read_text()
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue
                    # Check for string literals containing prohibited terms
                    if '"palai"' in line.lower() or "'palai'" in line.lower():
                        pytest.fail(
                            f"{config_file.name} line {i} contains 'palai' default: {line.strip()}"
                        )
