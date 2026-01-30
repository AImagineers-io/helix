"""Unit tests for environment safety checks.

Tests that demo environments cannot connect to production databases.
Implements boot-time validation to prevent accidental production data access.
"""
import pytest
from unittest.mock import patch


class TestEnvironmentSafety:
    """Tests for environment safety validation."""

    def test_demo_env_with_production_db_pattern_raises_error(self, clean_env):
        """Demo environment should fail if DATABASE_URL matches production pattern."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@prod-db.company.com:5432/helix_prod')

        get_settings.cache_clear()

        with pytest.raises(ValueError, match="Demo environment cannot connect to production"):
            settings = get_settings()
            validate_environment_safety(settings)

    def test_demo_env_with_prod_keyword_in_host_raises_error(self, clean_env):
        """Demo should fail if database host contains 'prod'."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@production-server:5432/helix')

        get_settings.cache_clear()

        with pytest.raises(ValueError, match="Demo environment cannot connect to production"):
            settings = get_settings()
            validate_environment_safety(settings)

    def test_demo_env_with_demo_db_succeeds(self, clean_env):
        """Demo environment with demo database should succeed."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@demo-db.company.com:5432/helix_demo')

        get_settings.cache_clear()

        settings = get_settings()
        # Should not raise
        validate_environment_safety(settings)

    def test_demo_env_with_localhost_succeeds(self, clean_env):
        """Demo environment with localhost database should succeed."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/helix')

        get_settings.cache_clear()

        settings = get_settings()
        # Should not raise
        validate_environment_safety(settings)

    def test_demo_env_with_sqlite_memory_succeeds(self, clean_env):
        """Demo environment with SQLite memory database should succeed."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        get_settings.cache_clear()

        settings = get_settings()
        # Should not raise
        validate_environment_safety(settings)

    def test_production_env_with_production_db_succeeds(self, clean_env):
        """Production environment with production database should succeed."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'production')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@prod-db.company.com:5432/helix_prod')

        get_settings.cache_clear()

        settings = get_settings()
        # Should not raise (production can connect to production)
        validate_environment_safety(settings)

    def test_dev_env_with_any_db_succeeds(self, clean_env):
        """Development environment should accept any database URL."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'development')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@prod-db.company.com:5432/helix_prod')

        get_settings.cache_clear()

        settings = get_settings()
        # Should not raise (dev is not restricted)
        validate_environment_safety(settings)

    def test_no_environment_set_defaults_to_development(self, clean_env):
        """When ENVIRONMENT is not set, should default to development."""
        from core.config import get_settings

        # Don't set ENVIRONMENT
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        get_settings.cache_clear()

        settings = get_settings()
        assert settings.environment == 'development'

    def test_demo_env_with_db_name_prod_raises_error(self, clean_env):
        """Demo should fail if database name contains 'prod'."""
        from core.config import get_settings, validate_environment_safety

        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@demo-db:5432/helix_production')

        get_settings.cache_clear()

        with pytest.raises(ValueError, match="Demo environment cannot connect to production"):
            settings = get_settings()
            validate_environment_safety(settings)


class TestProductionDatabasePatterns:
    """Tests for identifying production database patterns."""

    def test_is_production_db_with_prod_in_host(self, clean_env):
        """Should identify production database by 'prod' in host."""
        from core.config import is_production_database_url

        assert is_production_database_url('postgresql://u:p@prod-db.com:5432/db') is True
        assert is_production_database_url('postgresql://u:p@production-server:5432/db') is True
        assert is_production_database_url('postgresql://u:p@my-prod.aws.com:5432/db') is True

    def test_is_production_db_with_prod_in_dbname(self, clean_env):
        """Should identify production database by 'prod' in database name."""
        from core.config import is_production_database_url

        assert is_production_database_url('postgresql://u:p@localhost:5432/helix_prod') is True
        assert is_production_database_url('postgresql://u:p@localhost:5432/production_db') is True

    def test_is_not_production_db_with_safe_urls(self, clean_env):
        """Should not flag safe database URLs as production."""
        from core.config import is_production_database_url

        assert is_production_database_url('postgresql://u:p@localhost:5432/helix') is False
        assert is_production_database_url('postgresql://u:p@demo-db.com:5432/helix_demo') is False
        assert is_production_database_url('sqlite:///:memory:') is False
        assert is_production_database_url('postgresql://u:p@dev-db:5432/helix_dev') is False
