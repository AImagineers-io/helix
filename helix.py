#!/usr/bin/env python3
"""
Helix CLI - Test runner and database seeding tool for Helix project

This CLI tool is designed to run tests locally for troubleshooting and TDD workflows,
and provides database seeding commands for demo and production setup.
All tests run locally even when the app is deployed to production.

Usage:
    python helix.py test              # Run all tests (backend + frontend)
    python helix.py test backend      # Run all backend tests
    python helix.py test frontend     # Run frontend tests
    python helix.py test unit         # Run backend unit tests only
    python helix.py test integration  # Run backend integration tests only
    python helix.py seed demo         # Seed database with demo data
    python helix.py seed prompts      # Seed default prompt templates
    python helix.py seed reset        # Reset database and reseed with demo data
    python helix.py version           # Show version information
    python helix.py health            # Check backend health
    python helix.py --help            # Show help
"""

import sys
import subprocess
import os
import json
from pathlib import Path

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(text):
    """Print a colored header"""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}{text:^60}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{NC}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{NC}")


def print_info(text):
    """Print info message"""
    print(f"{YELLOW}→ {text}{NC}")


def run_command(cmd, cwd=None, timeout=180):
    """
    Run a shell command and return exit code

    Args:
        cmd: Command to run (string or list)
        cwd: Working directory
        timeout: Timeout in seconds

    Returns:
        Exit code (0 = success)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=isinstance(cmd, str),
            timeout=timeout,
            text=True
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out after {timeout}s")
        return 1
    except Exception as e:
        print_error(f"Failed to run command: {e}")
        return 1


def check_venv():
    """Check if Python virtual environment exists"""
    # Check both old and new directory structures
    for backend_dir in [Path("02_backend"), Path("backend")]:
        backend_venv = backend_dir / "venv"
        if backend_venv.exists():
            return str(backend_venv / "bin" / "activate")

    print_error("No Python virtual environment found!")
    print_info("Create one with: cd 02_backend && python -m venv venv")
    return None


def run_backend_tests(test_type="all"):
    """
    Run backend tests

    Args:
        test_type: "all", "unit", or "integration"
    """
    print_header("Running Backend Tests")

    # Check for test directory (04_tests) or legacy backend/tests
    tests_dir = Path("04_tests")
    if not tests_dir.exists():
        tests_dir = Path("backend/tests")
        if not tests_dir.exists():
            print_error("Tests directory not found!")
            print_info("Backend tests will be available once the backend is implemented")
            return 0  # Not a failure, just not implemented yet

    # Determine test path
    if test_type == "unit":
        test_path = "04_tests/unit"
        print_info("Running unit tests only...")
    elif test_type == "integration":
        test_path = "04_tests/integration"
        print_info("Running integration tests only...")
    else:
        test_path = "04_tests/"
        print_info("Running all backend tests...")

    # Run pytest with coverage
    cov_args = "--cov=02_backend --cov-report=term-missing"
    cmd = f"DATABASE_URL=sqlite:///:memory: python3 -m pytest {test_path} -v {cov_args}"

    exit_code = run_command(cmd, timeout=600)

    if exit_code == 0:
        print_success("Backend tests passed!")
    else:
        print_error("Backend tests failed!")

    return exit_code


def run_frontend_tests():
    """Run frontend tests"""
    print_header("Running Frontend Tests")

    # Check for 03_frontend or legacy frontend directory
    frontend_dir = Path("03_frontend")
    if not frontend_dir.exists():
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print_error("Frontend directory not found!")
            print_info("Frontend tests will be available once the frontend is implemented")
            return 0  # Not a failure, just not implemented yet

    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print_info("Installing frontend dependencies...")
        npm_install = run_command("npm install", cwd=str(frontend_dir))
        if npm_install != 0:
            print_error("Failed to install frontend dependencies!")
            return 1

    print_info("Running frontend tests...")
    cmd = "npm test -- --run --coverage"

    # Try with coverage first, fallback to without if it fails
    exit_code = run_command(cmd, cwd=str(frontend_dir), timeout=120)

    # If coverage fails, try without it
    if exit_code != 0:
        print_info("Coverage not available, running without coverage...")
        cmd = "npm test -- --run"
        exit_code = run_command(cmd, cwd=str(frontend_dir), timeout=120)

    if exit_code == 0:
        print_success("Frontend tests passed!")
    else:
        print_error("Frontend tests failed!")

    return exit_code


def run_all_tests():
    """Run all tests (backend + frontend)"""
    print_header("Helix Test Suite - Running All Tests")

    results = {}

    # Check if backend/tests exist
    if Path("04_tests").exists() or Path("backend").exists():
        results['backend'] = run_backend_tests()
    else:
        print_info("Backend not yet implemented, skipping...")
        results['backend'] = 0

    # Check if frontend exists
    if Path("03_frontend").exists() or Path("frontend").exists():
        results['frontend'] = run_frontend_tests()
    else:
        print_info("Frontend not yet implemented, skipping...")
        results['frontend'] = 0

    # Summary
    print_header("Test Results Summary")

    all_passed = True
    for suite, exit_code in results.items():
        if exit_code == 0:
            print_success(f"{suite.capitalize()} tests: PASSED")
        else:
            print_error(f"{suite.capitalize()} tests: FAILED")
            all_passed = False

    print()
    if all_passed:
        print_success("All tests passed!")
        return 0
    else:
        print_error("Some tests failed!")
        return 1


def cmd_version():
    """Show version information"""
    version_file = Path("version.json")

    try:
        with open(version_file, 'r') as f:
            version_info = json.load(f)

        print_header("Helix Version Info")
        print(f"{BLUE}Name:{NC}        {version_info.get('name', 'N/A')}")
        print(f"{BLUE}Version:{NC}     {version_info.get('version', 'N/A')}")
        print(f"{BLUE}Description:{NC} {version_info.get('description', 'N/A')}")
        print(f"{BLUE}Company:{NC}     {version_info.get('company', 'N/A')}")
        print(f"{BLUE}Author:{NC}      {version_info.get('author', 'N/A')}")
        print(f"{BLUE}Email:{NC}       {version_info.get('email', 'N/A')}")
        print()
        return 0
    except Exception as e:
        print_error(f"Failed to read version info: {e}")
        return 1


def cmd_health():
    """Check backend health"""
    print_header("Helix Health Check")

    try:
        import urllib.request
        import urllib.error

        url = "http://localhost:8000/health"

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())

                print_success("Backend is running!")
                print(f"{BLUE}Name:{NC}    {data.get('name', 'N/A')}")
                print(f"{BLUE}Version:{NC} {data.get('version', 'N/A')}")
                print(f"{BLUE}Status:{NC}  {data.get('status', 'N/A')}")
                print()
                return 0
        except urllib.error.URLError:
            print_error("Backend is not running!")
            print_info("Start the backend with: cd backend && venv/bin/uvicorn api.main:app --reload")
            print()
            return 1
    except Exception as e:
        print_error(f"Failed to check health: {e}")
        return 1


def cmd_seed(seed_type="demo"):
    """
    Seed database with demo or default data

    Args:
        seed_type: Type of seeding - "demo", "prompts", or "reset"
    """
    print_header(f"Helix Database Seeding - {seed_type.title()}")

    # Add backend to Python path
    backend_path = Path("02_backend")
    if not backend_path.exists():
        backend_path = Path("backend")

    if not backend_path.exists():
        print_error("Backend directory not found!")
        return 1

    # Add to path for imports
    sys.path.insert(0, str(backend_path))

    try:
        # Import database dependencies
        from database.connection import get_db, engine, Base
        from database.seeds.prompts import seed_default_prompts
        from database.seeds.demo_prompts import seed_demo_prompts
        from sqlalchemy.orm import Session

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # Get database session
        db = next(get_db())

        try:
            if seed_type == "demo":
                print_info("Seeding demo data...")
                seed_demo_prompts(db)
                print_success("Demo data seeded successfully!")

            elif seed_type == "prompts":
                print_info("Seeding default prompts...")
                seed_default_prompts(db)
                print_success("Default prompts seeded successfully!")

            elif seed_type == "reset":
                print_info("Resetting database...")

                # Import models to ensure they're registered
                from database.models import PromptTemplate, PromptVersion

                # Drop all tables
                Base.metadata.drop_all(bind=engine)
                print_info("Dropped all tables")

                # Recreate tables
                Base.metadata.create_all(bind=engine)
                print_info("Recreated all tables")

                # Reseed with demo data
                seed_demo_prompts(db)
                print_success("Database reset and reseeded with demo data!")

            else:
                print_error(f"Unknown seed type: {seed_type}")
                print_info("Valid options: demo, prompts, reset")
                return 1

            print()
            return 0

        finally:
            db.close()

    except ImportError as e:
        print_error(f"Failed to import database modules: {e}")
        print_info("Make sure backend dependencies are installed")
        return 1
    except Exception as e:
        print_error(f"Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_help():
    """Show help message"""
    help_text = f"""
{BLUE}Helix CLI{NC} - Test runner and database seeding tool for Helix project

{YELLOW}Purpose:{NC}
  This tool runs tests locally for troubleshooting and TDD workflows,
  and provides database seeding commands for demo and production setup.
  Tests run on your local machine even when the app is deployed to production.

{YELLOW}Usage:{NC}
  python helix.py test              # Run all tests (backend + frontend)
  python helix.py test backend      # Run all backend tests
  python helix.py test frontend     # Run frontend tests only
  python helix.py test unit         # Run backend unit tests only
  python helix.py test integration  # Run backend integration tests only
  python helix.py seed demo         # Seed database with demo data
  python helix.py seed prompts      # Seed default prompt templates
  python helix.py seed reset        # Reset database and reseed with demo data
  python helix.py version           # Show version information
  python helix.py health            # Check backend health
  python helix.py --help            # Show this help message

{YELLOW}Examples:{NC}
  python helix.py test                    # Full test suite
  python helix.py test backend            # Quick backend check
  python helix.py test unit               # Fast unit tests only
  python helix.py test integration        # Integration tests only
  python helix.py seed demo               # Seed demo data for testing
  python helix.py seed reset              # Clear and reseed database
  python helix.py version                 # Version info
  python helix.py health                  # Health check

{YELLOW}Requirements:{NC}
  - Python virtual environment (backend/venv/)
  - Node.js and npm for frontend tests
  - All dependencies installed
  - DATABASE_URL environment variable for seeding

{YELLOW}Notes:{NC}
  - Tests run locally regardless of deployment environment
  - Use this for TDD and troubleshooting
  - Backend tests use in-memory SQLite (DATABASE_URL=sqlite:///:memory:)
  - Coverage reports included by default
  - Seed commands modify the actual database (use with caution in production)
  - Exit code 0 = success, 1 = failure (CI/CD compatible)
"""
    print(help_text)


def main():
    """Main entry point"""
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        show_help()
        return 0

    # Handle commands
    command = args[0]

    if command == 'version':
        return cmd_version()
    elif command == 'health':
        return cmd_health()
    elif command == 'seed':
        # Determine seed type
        seed_type = args[1] if len(args) > 1 else 'demo'

        if seed_type in ['demo', 'prompts', 'reset']:
            return cmd_seed(seed_type)
        else:
            print_error(f"Unknown seed type: {seed_type}")
            print_info("Valid options: demo, prompts, reset")
            return 1
    elif command == 'test':
        # Determine test type
        test_type = args[1] if len(args) > 1 else 'all'

        if test_type == 'all':
            return run_all_tests()
        elif test_type == 'backend':
            return run_backend_tests('all')
        elif test_type == 'frontend':
            return run_frontend_tests()
        elif test_type == 'unit':
            return run_backend_tests('unit')
        elif test_type == 'integration':
            return run_backend_tests('integration')
        else:
            print_error(f"Unknown test type: {test_type}")
            print_info("Valid options: all, backend, frontend, unit, integration")
            return 1
    else:
        print_error(f"Unknown command: {command}")
        print_info("Run 'python helix.py --help' for usage")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test run interrupted by user{NC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
