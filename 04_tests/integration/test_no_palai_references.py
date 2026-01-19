"""
Integration test to verify no PALAI/PhilRice branding remains in codebase.

This test ensures that Helix is a clean white-label product with no
client-specific branding hardcoded.
"""
import subprocess
from pathlib import Path


def test_no_palai_references_in_backend_code():
    """Test that backend Python code has no PALAI references."""
    backend_dir = Path(__file__).parent.parent.parent / '02_backend'

    # Search for PALAI in Python files (excluding comments)
    result = subprocess.run(
        [
            'grep', '-ri', 'palai',
            '--include=*.py',
            str(backend_dir),
        ],
        capture_output=True,
        text=True,
    )

    # Filter out acceptable references (comments about source)
    lines = result.stdout.strip().split('\n') if result.stdout else []
    violations = [
        line for line in lines
        if line and 'pattern' not in line.lower() and 'extracted from' not in line.lower()
    ]

    assert len(violations) == 0, (
        f"Found PALAI references in backend code:\n" + '\n'.join(violations)
    )


def test_no_philrice_references_in_backend_code():
    """Test that backend Python code has no PhilRice references."""
    backend_dir = Path(__file__).parent.parent.parent / '02_backend'

    result = subprocess.run(
        [
            'grep', '-ri', 'philrice',
            '--include=*.py',
            str(backend_dir),
        ],
        capture_output=True,
        text=True,
    )

    # If grep finds nothing, stdout will be empty
    assert result.stdout == '', (
        f"Found PhilRice references in backend code:\n" + result.stdout
    )


def test_no_palai_in_frontend_title():
    """Test that frontend HTML does not have PALAI in title."""
    index_html = Path(__file__).parent.parent.parent / '03_frontend' / 'index.html'

    content = index_html.read_text()

    assert 'PalAI' not in content, "Found 'PalAI' in index.html"
    assert 'PALAI' not in content, "Found 'PALAI' in index.html"
    assert 'PhilRice' not in content, "Found 'PhilRice' in index.html"


def test_frontend_package_name_is_helix():
    """Test that frontend package.json uses helix name."""
    import json

    package_json = Path(__file__).parent.parent.parent / '03_frontend' / 'package.json'

    with open(package_json, 'r') as f:
        data = json.load(f)

    assert data['name'] == 'helix-frontend', (
        f"package.json name should be 'helix-frontend', got '{data['name']}'"
    )


def test_docker_services_named_helix():
    """Test that docker-compose.yml uses helix-* service names."""
    import yaml

    compose_file = Path(__file__).parent.parent.parent / 'docker-compose.yml'

    with open(compose_file, 'r') as f:
        # Simple parse - just check container names
        content = f.read()

    assert 'helix-backend' in content, "Missing helix-backend container name"
    assert 'helix-frontend' in content, "Missing helix-frontend container name"
    assert 'helix-redis' in content, "Missing helix-redis container name"
    assert 'palai' not in content.lower(), "Found 'palai' in docker-compose.yml"
