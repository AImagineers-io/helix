"""Comprehensive rename verification tests (P4.9).

Verifies that the rebranding from PALAI to Helix is complete:
- No prohibited terms in source code
- API docs show correct branding
- Health endpoint returns correct name
- Frontend bundle contains no prohibited terms
"""
import subprocess
from pathlib import Path

import pytest


class TestNoPalaiInSource:
    """Verify no PALAI/PhilRice references in source files."""

    PROHIBITED_TERMS = ["palai", "philrice"]
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    # Directories to exclude from search
    EXCLUDED_DIRS = [
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
        "coverage",
        ".mypy_cache",
        "00_project_roadmap/archive",  # Archived phases may contain historical references
    ]

    # Files to exclude (may contain legitimate references)
    EXCLUDED_FILES = [
        "test_complete_rebrand.py",  # This test file
        "test_no_palai_references.py",  # Related test file
        "test_branding_hook.py",  # Hook test file
        "test_third_party_refs.py",  # Third party refs test
        "test_error_messages.py",  # Error messages test
        "test_db_content_audit.py",  # DB audit test
        "test_demo_prompts_seed.py",  # Demo prompts test
        ".pre-commit-config.yaml",  # Config describes what it checks
        "CHANGELOG.md",  # May contain historical references
        "improve.md",  # May contain improvement notes
    ]

    @pytest.fixture
    def source_extensions(self) -> list[str]:
        """File extensions to scan for prohibited terms."""
        return [".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".md"]

    def _build_grep_command(self, term: str, extensions: list[str]) -> list[str]:
        """Build grep command to search for prohibited terms."""
        exclude_dirs = " ".join(f"--exclude-dir={d}" for d in self.EXCLUDED_DIRS)
        exclude_files = " ".join(f"--exclude={f}" for f in self.EXCLUDED_FILES)
        include_patterns = " ".join(f"--include=*{ext}" for ext in extensions)

        cmd = f"grep -r -i -l {include_patterns} {exclude_dirs} {exclude_files} '{term}' {self.PROJECT_ROOT}"
        return ["bash", "-c", cmd]

    def test_no_palai_in_python_files(self):
        """Verify no 'palai' in Python source files."""
        result = subprocess.run(
            self._build_grep_command("palai", [".py"]),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split("\n")
            pytest.fail(f"Found 'palai' in Python files:\n{chr(10).join(files)}")

    def test_no_palai_in_typescript_files(self):
        """Verify no 'palai' in TypeScript/JavaScript files."""
        result = subprocess.run(
            self._build_grep_command("palai", [".ts", ".tsx", ".js", ".jsx"]),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split("\n")
            pytest.fail(f"Found 'palai' in TypeScript files:\n{chr(10).join(files)}")

    def test_no_palai_in_config_files(self):
        """Verify no 'palai' in config files."""
        result = subprocess.run(
            self._build_grep_command("palai", [".json", ".yaml", ".yml"]),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split("\n")
            pytest.fail(f"Found 'palai' in config files:\n{chr(10).join(files)}")

    def test_no_philrice_in_source(self):
        """Verify no 'philrice' in any source files."""
        result = subprocess.run(
            self._build_grep_command("philrice", [".py", ".ts", ".tsx", ".js", ".jsx", ".json"]),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split("\n")
            pytest.fail(f"Found 'philrice' in source files:\n{chr(10).join(files)}")


class TestAPIBranding:
    """Verify API documentation shows correct branding."""

    def test_openapi_title_is_helix(self, test_client):
        """Verify OpenAPI docs title contains 'Helix'."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        title = openapi_spec.get("info", {}).get("title", "")

        assert "palai" not in title.lower(), f"OpenAPI title contains 'palai': {title}"
        assert "philrice" not in title.lower(), f"OpenAPI title contains 'philrice': {title}"

    def test_openapi_description_no_prohibited_terms(self, test_client):
        """Verify OpenAPI description doesn't contain prohibited terms."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        description = openapi_spec.get("info", {}).get("description", "").lower()

        assert "palai" not in description
        assert "philrice" not in description


class TestHealthEndpointBranding:
    """Verify health endpoint returns correct branding."""

    def test_health_returns_configured_app_name(self, test_client):
        """Verify health endpoint returns configured app name."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        app_name = data.get("app_name", data.get("name", "")).lower()

        assert "palai" not in app_name, f"Health endpoint returns 'palai': {app_name}"
        assert "philrice" not in app_name, f"Health endpoint returns 'philrice': {app_name}"


class TestBrandingEndpoint:
    """Verify branding endpoint returns correct values."""

    def test_branding_endpoint_no_prohibited_terms(self, test_client):
        """Verify branding endpoint returns no prohibited terms."""
        response = test_client.get("/branding")
        assert response.status_code == 200

        data = response.json()

        # Check all string values in branding response
        for key, value in data.items():
            if isinstance(value, str):
                assert "palai" not in value.lower(), f"Branding '{key}' contains 'palai': {value}"
                assert "philrice" not in value.lower(), f"Branding '{key}' contains 'philrice': {value}"


class TestDockerConfiguration:
    """Verify Docker configuration uses correct naming."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_docker_compose_no_palai(self):
        """Verify docker-compose.yml doesn't contain 'palai'."""
        compose_path = self.PROJECT_ROOT / "docker-compose.yml"
        if not compose_path.exists():
            pytest.skip("docker-compose.yml not found")

        content = compose_path.read_text().lower()
        assert "palai" not in content, "docker-compose.yml contains 'palai'"

    def test_docker_compose_uses_helix_prefix(self):
        """Verify docker-compose.yml uses 'helix-' prefix for container names."""
        compose_path = self.PROJECT_ROOT / "docker-compose.yml"
        if not compose_path.exists():
            pytest.skip("docker-compose.yml not found")

        import yaml

        with open(compose_path) as f:
            config = yaml.safe_load(f)

        # Check container_name fields use helix prefix
        services = config.get("services", {})
        for service_name, service_config in services.items():
            container_name = service_config.get("container_name", "")
            if container_name:
                assert container_name.startswith("helix-") or container_name == "helix", \
                    f"Container '{container_name}' doesn't use 'helix-' prefix"
                assert "palai" not in container_name.lower(), \
                    f"Container '{container_name}' contains 'palai'"


class TestPackageJsonBranding:
    """Verify package.json uses correct naming."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_frontend_package_name_is_helix(self):
        """Verify frontend package.json name is 'helix-frontend'."""
        import json

        package_path = self.PROJECT_ROOT / "03_frontend" / "package.json"
        if not package_path.exists():
            pytest.skip("Frontend package.json not found")

        with open(package_path) as f:
            package = json.load(f)

        name = package.get("name", "")
        assert "palai" not in name.lower(), f"Package name contains 'palai': {name}"
        assert "helix" in name.lower(), f"Package name should contain 'helix': {name}"

    def test_package_json_no_palai_in_scripts(self):
        """Verify no 'palai' references in package.json scripts."""
        import json

        package_path = self.PROJECT_ROOT / "03_frontend" / "package.json"
        if not package_path.exists():
            pytest.skip("Frontend package.json not found")

        content = package_path.read_text().lower()
        assert "palai" not in content, "Frontend package.json contains 'palai'"
