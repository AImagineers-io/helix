"""Third-party reference audit tests (P4.1a).

Verifies that all third-party references use correct 'helix' branding:
- Package names in package.json
- Docker image names/tags
- Git remote URLs (documented)
- CI/CD variable references
"""
import subprocess
from pathlib import Path

import pytest


class TestPackageJsonReferences:
    """Verify package.json files use correct naming."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_frontend_package_name(self):
        """Frontend package.json should be named 'helix-frontend'."""
        import json

        package_path = self.PROJECT_ROOT / "03_frontend" / "package.json"
        with open(package_path) as f:
            package = json.load(f)

        assert package.get("name") == "helix-frontend", \
            f"Expected 'helix-frontend', got '{package.get('name')}'"

    def test_no_palai_dependencies(self):
        """No dependencies should contain 'palai' in name."""
        import json

        package_path = self.PROJECT_ROOT / "03_frontend" / "package.json"
        with open(package_path) as f:
            package = json.load(f)

        all_deps = {}
        all_deps.update(package.get("dependencies", {}))
        all_deps.update(package.get("devDependencies", {}))

        for dep_name in all_deps:
            assert "palai" not in dep_name.lower(), \
                f"Dependency '{dep_name}' contains 'palai'"


class TestDockerImageReferences:
    """Verify Docker configuration uses 'helix' image names."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_docker_compose_image_names(self):
        """Docker compose should use 'helix-*' image names."""
        import yaml

        compose_path = self.PROJECT_ROOT / "docker-compose.yml"
        if not compose_path.exists():
            pytest.skip("docker-compose.yml not found")

        with open(compose_path) as f:
            config = yaml.safe_load(f)

        services = config.get("services", {})
        for service_name, service_config in services.items():
            image = service_config.get("image", "")
            if image:
                assert "palai" not in image.lower(), \
                    f"Service '{service_name}' image contains 'palai': {image}"

    def test_dockerfile_no_palai_references(self):
        """Dockerfiles should not contain 'palai' references."""
        dockerfiles = [
            self.PROJECT_ROOT / "Dockerfile",
            self.PROJECT_ROOT / "02_backend" / "Dockerfile",
            self.PROJECT_ROOT / "03_frontend" / "Dockerfile",
            self.PROJECT_ROOT / "05_deployment" / "Dockerfile",
        ]

        for dockerfile in dockerfiles:
            if dockerfile.exists():
                content = dockerfile.read_text().lower()
                assert "palai" not in content, \
                    f"{dockerfile} contains 'palai'"


class TestGitRemoteDocumentation:
    """Verify git remote handling is documented."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_git_remote_not_palai(self):
        """Current git remotes should not point to 'palai' repos."""
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=self.PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip("Not a git repository or git not available")

        remotes = result.stdout.lower()
        # Note: Historical references in .git/config are acceptable,
        # but active remotes should not point to 'palai' URLs
        lines = [line for line in remotes.split("\n") if "fetch" in line]

        for line in lines:
            if "palai" in line and "aimagineers" in line:
                pytest.fail(
                    f"Git remote points to 'palai' repository: {line}\n"
                    "Consider updating with: git remote set-url origin <new-url>"
                )


class TestCIConfigReferences:
    """Verify CI/CD configuration uses correct naming."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_gitlab_ci_no_palai_variables(self):
        """GitLab CI should not reference 'palai' in variable names."""
        ci_path = self.PROJECT_ROOT / ".gitlab-ci.yml"
        if not ci_path.exists():
            pytest.skip(".gitlab-ci.yml not found")

        content = ci_path.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check variable definitions and references
            if "palai" in line.lower():
                # Allow comments explaining migration
                if line.strip().startswith("#"):
                    continue
                pytest.fail(
                    f".gitlab-ci.yml line {i} contains 'palai': {line.strip()}"
                )

    def test_github_workflows_no_palai(self):
        """GitHub workflows should not reference 'palai'."""
        workflows_dir = self.PROJECT_ROOT / ".github" / "workflows"
        if not workflows_dir.exists():
            pytest.skip("No GitHub workflows directory")

        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text().lower()
            assert "palai" not in content, \
                f"{workflow_file.name} contains 'palai'"


class TestEnvironmentVariableDocumentation:
    """Verify environment variable documentation is updated."""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    def test_env_example_no_palai(self):
        """Example env files should not contain 'palai' values."""
        env_examples = [
            self.PROJECT_ROOT / ".env.example",
            self.PROJECT_ROOT / "02_backend" / ".env.example",
            self.PROJECT_ROOT / "03_frontend" / ".env.example",
        ]

        for env_file in env_examples:
            if env_file.exists():
                content = env_file.read_text().lower()
                assert "palai" not in content, \
                    f"{env_file} contains 'palai' in example values"
