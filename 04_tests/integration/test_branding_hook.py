"""Tests for the branding check hook script.

Verifies that the check-branding.sh script correctly:
- Finds prohibited terms in source files
- Ignores allowed exceptions (config references, comments)
- Returns correct exit codes
"""
import subprocess
import tempfile
import os
from pathlib import Path

import pytest


class TestBrandingCheckScript:
    """Tests for scripts/check-branding.sh"""

    @pytest.fixture
    def script_path(self) -> Path:
        """Path to the branding check script."""
        return Path(__file__).parent.parent.parent / "scripts" / "check-branding.sh"

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_script_exists(self, script_path: Path):
        """Test that the branding check script exists."""
        assert script_path.exists(), f"Script not found at {script_path}"

    def test_script_is_executable(self, script_path: Path):
        """Test that the branding check script is executable."""
        assert os.access(script_path, os.X_OK), "Script is not executable"

    def test_clean_file_passes(self, script_path: Path, temp_dir: Path):
        """Test that a file without prohibited terms passes."""
        clean_file = temp_dir / "clean.py"
        clean_file.write_text('print("Hello Helix!")\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Expected pass, got: {result.stderr}"

    def test_file_with_palai_fails(self, script_path: Path, temp_dir: Path):
        """Test that a file containing 'palai' fails the check."""
        bad_file = temp_dir / "bad.py"
        bad_file.write_text('app_name = "PALAI Chatbot"\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Expected failure for 'palai'"
        assert "palai" in result.stdout.lower() or "prohibited" in result.stdout.lower()

    def test_file_with_philrice_fails(self, script_path: Path, temp_dir: Path):
        """Test that a file containing 'philrice' fails the check."""
        bad_file = temp_dir / "bad.py"
        bad_file.write_text('org = "PhilRice"\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Expected failure for 'philrice'"

    def test_case_insensitive_detection(self, script_path: Path, temp_dir: Path):
        """Test that detection is case-insensitive."""
        bad_file = temp_dir / "bad.py"
        bad_file.write_text('name = "PaLaI"\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Expected failure for case-variant 'PaLaI'"

    def test_scans_python_files(self, script_path: Path, temp_dir: Path):
        """Test that Python files are scanned."""
        bad_file = temp_dir / "code.py"
        bad_file.write_text('# PALAI reference\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_scans_typescript_files(self, script_path: Path, temp_dir: Path):
        """Test that TypeScript files are scanned."""
        ts_file = temp_dir / "code.ts"
        ts_file.write_text('const name = "PALAI";\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_scans_tsx_files(self, script_path: Path, temp_dir: Path):
        """Test that TSX files are scanned."""
        tsx_file = temp_dir / "Component.tsx"
        tsx_file.write_text('<div>PALAI</div>\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_scans_json_files(self, script_path: Path, temp_dir: Path):
        """Test that JSON files are scanned."""
        json_file = temp_dir / "config.json"
        json_file.write_text('{"name": "palai-app"}\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_ignores_git_directory(self, script_path: Path, temp_dir: Path):
        """Test that .git directory is ignored."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        git_file = git_dir / "config"
        git_file.write_text('palai-origin\n')

        # Add a clean file so there's something to scan
        clean_file = temp_dir / "clean.py"
        clean_file.write_text('print("clean")\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, ".git directory should be ignored"

    def test_ignores_node_modules(self, script_path: Path, temp_dir: Path):
        """Test that node_modules directory is ignored."""
        nm_dir = temp_dir / "node_modules" / "some-package"
        nm_dir.mkdir(parents=True)
        nm_file = nm_dir / "index.js"
        nm_file.write_text('const palai = true;\n')

        clean_file = temp_dir / "clean.py"
        clean_file.write_text('print("clean")\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "node_modules should be ignored"

    def test_ignores_venv_directory(self, script_path: Path, temp_dir: Path):
        """Test that venv directory is ignored."""
        venv_dir = temp_dir / "venv" / "lib"
        venv_dir.mkdir(parents=True)
        venv_file = venv_dir / "package.py"
        venv_file.write_text('palai = "test"\n')

        clean_file = temp_dir / "clean.py"
        clean_file.write_text('print("clean")\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "venv should be ignored"

    def test_output_shows_offending_files(self, script_path: Path, temp_dir: Path):
        """Test that output shows which files contain violations."""
        bad_file = temp_dir / "offending.py"
        bad_file.write_text('name = "palai"\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert "offending.py" in result.stdout

    def test_multiple_violations_all_reported(self, script_path: Path, temp_dir: Path):
        """Test that multiple violations are all reported."""
        file1 = temp_dir / "file1.py"
        file1.write_text('x = "palai"\n')

        file2 = temp_dir / "file2.py"
        file2.write_text('y = "philrice"\n')

        result = subprocess.run(
            [str(script_path), str(temp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "file1.py" in result.stdout
        assert "file2.py" in result.stdout


class TestPreCommitConfig:
    """Tests for .pre-commit-config.yaml"""

    def test_precommit_config_exists(self):
        """Test that .pre-commit-config.yaml exists."""
        config_path = Path(__file__).parent.parent.parent / ".pre-commit-config.yaml"
        assert config_path.exists(), "Pre-commit config not found"

    def test_precommit_config_has_branding_hook(self):
        """Test that config includes branding check hook."""
        import yaml

        config_path = Path(__file__).parent.parent.parent / ".pre-commit-config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Find local hook for branding check
        hooks = []
        for repo in config.get("repos", []):
            if repo.get("repo") == "local":
                hooks.extend(repo.get("hooks", []))

        hook_ids = [h.get("id") for h in hooks]
        assert "check-branding" in hook_ids, "Branding hook not found in config"
