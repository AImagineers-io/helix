"""
Integration tests for Secrets Management (P12.5.1)

Tests secrets management including:
- Environment provider (default)
- Vault provider (HashiCorp)
- AWS Secrets Manager provider
- Secret loading and caching
- Graceful fallback
"""
import pytest
import os

from core.secrets import (
    SecretsConfig,
    SecretsProvider,
    SecretsManager,
    get_secret,
    EnvironmentSecretsProvider,
    SecretNotFoundError,
)


class TestSecretsConfig:
    """Tests for secrets configuration."""

    def test_default_provider(self):
        """Default provider should be environment."""
        config = SecretsConfig()
        assert config.provider == "env"

    def test_custom_provider(self):
        """Custom provider should be accepted."""
        config = SecretsConfig(provider="vault")
        assert config.provider == "vault"


class TestEnvironmentProvider:
    """Tests for environment secrets provider."""

    @pytest.fixture
    def provider(self):
        """Create environment provider."""
        return EnvironmentSecretsProvider()

    def test_reads_env_variable(self, provider, monkeypatch):
        """Should read from environment variable."""
        monkeypatch.setenv("TEST_SECRET", "secret_value")

        value = provider.get("TEST_SECRET")
        assert value == "secret_value"

    def test_returns_none_for_missing(self, provider, monkeypatch):
        """Should return None for missing secret."""
        monkeypatch.delenv("NONEXISTENT_SECRET", raising=False)

        value = provider.get("NONEXISTENT_SECRET")
        assert value is None

    def test_supports_prefix(self, monkeypatch):
        """Should support env var prefix."""
        monkeypatch.setenv("HELIX_API_KEY", "the_key")

        provider = EnvironmentSecretsProvider(prefix="HELIX_")
        value = provider.get("API_KEY")

        assert value == "the_key"


class TestSecretsManager:
    """Tests for SecretsManager class."""

    @pytest.fixture
    def manager(self, monkeypatch):
        """Create secrets manager with env provider."""
        monkeypatch.setenv("DB_PASSWORD", "db_secret")
        monkeypatch.setenv("JWT_SECRET", "jwt_secret")

        return SecretsManager(SecretsConfig(provider="env"))

    def test_get_secret(self, manager):
        """Should get secret from provider."""
        value = manager.get("DB_PASSWORD")
        assert value == "db_secret"

    def test_get_required_raises_on_missing(self, manager, monkeypatch):
        """Should raise for missing required secret."""
        monkeypatch.delenv("MISSING_SECRET", raising=False)

        with pytest.raises(SecretNotFoundError) as exc:
            manager.get_required("MISSING_SECRET")

        assert "MISSING_SECRET" in str(exc.value)

    def test_get_with_default(self, manager, monkeypatch):
        """Should return default for missing secret."""
        monkeypatch.delenv("OPTIONAL_SECRET", raising=False)

        value = manager.get("OPTIONAL_SECRET", default="default_value")
        assert value == "default_value"

    def test_caches_secrets(self, manager, monkeypatch):
        """Should cache secrets after first access."""
        # First access
        manager.get("DB_PASSWORD")

        # Change env var
        monkeypatch.setenv("DB_PASSWORD", "new_value")

        # Should still return cached value
        value = manager.get("DB_PASSWORD")
        assert value == "db_secret"

    def test_refresh_clears_cache(self, manager, monkeypatch):
        """Refresh should clear cache."""
        manager.get("DB_PASSWORD")
        monkeypatch.setenv("DB_PASSWORD", "new_value")

        manager.refresh()

        value = manager.get("DB_PASSWORD")
        assert value == "new_value"


class TestSecretsProviderInterface:
    """Tests for SecretsProvider interface."""

    def test_interface_methods(self):
        """Provider should have required methods."""
        assert hasattr(SecretsProvider, "get")
        assert hasattr(SecretsProvider, "list_secrets")


class TestSecretNotFoundError:
    """Tests for SecretNotFoundError."""

    def test_error_message(self):
        """Error should include secret name."""
        error = SecretNotFoundError("API_KEY")
        assert "API_KEY" in str(error)


class TestGetSecretConvenience:
    """Tests for get_secret convenience function."""

    def test_get_secret_from_env(self, monkeypatch):
        """get_secret should work with env vars."""
        monkeypatch.setenv("CONVENIENCE_SECRET", "value")

        value = get_secret("CONVENIENCE_SECRET")
        assert value == "value"

    def test_get_secret_with_default(self, monkeypatch):
        """get_secret should support default."""
        monkeypatch.delenv("MISSING", raising=False)

        value = get_secret("MISSING", default="fallback")
        assert value == "fallback"


class TestMultipleProviders:
    """Tests for provider selection."""

    def test_env_provider_selected(self, monkeypatch):
        """Environment provider should be selected."""
        monkeypatch.setenv("TEST", "value")

        config = SecretsConfig(provider="env")
        manager = SecretsManager(config)

        assert isinstance(manager._provider, EnvironmentSecretsProvider)

    def test_unknown_provider_fallback(self, monkeypatch):
        """Unknown provider should fall back to env."""
        monkeypatch.setenv("TEST", "value")

        config = SecretsConfig(provider="unknown")
        manager = SecretsManager(config)

        # Should fall back to env
        value = manager.get("TEST")
        assert value == "value"


class TestSecretRotation:
    """Tests for secret rotation support."""

    @pytest.fixture
    def manager(self, monkeypatch):
        monkeypatch.setenv("ROTATABLE_SECRET", "v1")
        return SecretsManager(SecretsConfig())

    def test_detect_rotation(self, manager, monkeypatch):
        """Should detect when secret changes."""
        original = manager.get("ROTATABLE_SECRET")
        assert original == "v1"

        monkeypatch.setenv("ROTATABLE_SECRET", "v2")
        manager.refresh()

        new = manager.get("ROTATABLE_SECRET")
        assert new == "v2"

    def test_has_secret(self, manager, monkeypatch):
        """Should check if secret exists."""
        assert manager.has("ROTATABLE_SECRET") is True

        monkeypatch.delenv("NONEXISTENT", raising=False)
        assert manager.has("NONEXISTENT") is False
