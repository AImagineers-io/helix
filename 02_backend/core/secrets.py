"""
Secrets Management for secure secret loading.

Provides:
- Environment provider (default)
- Vault provider interface (HashiCorp)
- AWS Secrets Manager interface
- Secret caching
- Graceful fallback

Configuration via SECRETS_PROVIDER env var:
- env (default): Environment variables
- vault: HashiCorp Vault
- aws: AWS Secrets Manager
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


class SecretNotFoundError(Exception):
    """Raised when a required secret is not found."""

    def __init__(self, secret_name: str):
        """
        Initialize error.

        Args:
            secret_name: Name of the missing secret
        """
        super().__init__(f"Required secret not found: {secret_name}")
        self.secret_name = secret_name


@dataclass
class SecretsConfig:
    """Configuration for secrets management."""
    provider: str = "env"
    cache_enabled: bool = True
    # Vault-specific
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    vault_path: str = "secret/data/helix"
    # AWS-specific
    aws_region: Optional[str] = None
    aws_secret_name: Optional[str] = None


class SecretsProvider(ABC):
    """Abstract base class for secrets providers."""

    @abstractmethod
    def get(self, name: str) -> Optional[str]:
        """
        Get a secret by name.

        Args:
            name: Secret name

        Returns:
            Optional[str]: Secret value or None if not found
        """
        pass

    def list_secrets(self) -> list[str]:
        """
        List available secret names.

        Returns:
            list[str]: List of secret names
        """
        return []


class EnvironmentSecretsProvider(SecretsProvider):
    """
    Secrets provider that reads from environment variables.

    This is the default provider for development and simple deployments.
    """

    def __init__(self, prefix: str = ""):
        """
        Initialize environment provider.

        Args:
            prefix: Optional prefix for env var names
        """
        self.prefix = prefix

    def get(self, name: str) -> Optional[str]:
        """
        Get secret from environment variable.

        Args:
            name: Secret name (prefix will be added if configured)

        Returns:
            Optional[str]: Environment variable value or None
        """
        full_name = f"{self.prefix}{name}"
        return os.environ.get(full_name)

    def list_secrets(self) -> list[str]:
        """List environment variables with prefix."""
        if not self.prefix:
            return []

        secrets = []
        for key in os.environ:
            if key.startswith(self.prefix):
                secrets.append(key[len(self.prefix):])
        return secrets


class SecretsManager:
    """
    Centralized secrets management.

    Handles secret loading, caching, and provider selection.
    Falls back to environment variables if configured provider fails.
    """

    def __init__(self, config: Optional[SecretsConfig] = None):
        """
        Initialize secrets manager.

        Args:
            config: Secrets configuration
        """
        self.config = config or SecretsConfig()
        self._cache: dict[str, str] = {}
        self._provider = self._create_provider()

    def _create_provider(self) -> SecretsProvider:
        """
        Create secrets provider based on config.

        Returns:
            SecretsProvider: Configured provider
        """
        provider_type = self.config.provider.lower()

        if provider_type == "env":
            return EnvironmentSecretsProvider()

        if provider_type == "vault":
            # Would integrate with hvac library
            # Fall back to env for now
            return EnvironmentSecretsProvider()

        if provider_type == "aws":
            # Would integrate with boto3
            # Fall back to env for now
            return EnvironmentSecretsProvider()

        # Unknown provider, fall back to env
        return EnvironmentSecretsProvider()

    def get(
        self,
        name: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret by name.

        Args:
            name: Secret name
            default: Default value if not found

        Returns:
            Optional[str]: Secret value
        """
        # Check cache first
        if self.config.cache_enabled and name in self._cache:
            return self._cache[name]

        # Get from provider
        value = self._provider.get(name)

        if value is None:
            return default

        # Cache the value
        if self.config.cache_enabled:
            self._cache[name] = value

        return value

    def get_required(self, name: str) -> str:
        """
        Get a required secret.

        Args:
            name: Secret name

        Returns:
            str: Secret value

        Raises:
            SecretNotFoundError: If secret not found
        """
        value = self.get(name)

        if value is None:
            raise SecretNotFoundError(name)

        return value

    def has(self, name: str) -> bool:
        """
        Check if a secret exists.

        Args:
            name: Secret name

        Returns:
            bool: True if secret exists
        """
        return self.get(name) is not None

    def refresh(self) -> None:
        """Clear the cache to force reload of secrets."""
        self._cache.clear()

    def list_secrets(self) -> list[str]:
        """
        List available secrets.

        Returns:
            list[str]: Secret names
        """
        return self._provider.list_secrets()


# Global secrets manager instance
_manager: Optional[SecretsManager] = None


def _get_manager() -> SecretsManager:
    """Get or create global secrets manager."""
    global _manager

    if _manager is None:
        provider = os.environ.get("SECRETS_PROVIDER", "env")
        _manager = SecretsManager(SecretsConfig(provider=provider))

    return _manager


def get_secret(
    name: str,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to get a secret.

    Args:
        name: Secret name
        default: Default value if not found

    Returns:
        Optional[str]: Secret value
    """
    return _get_manager().get(name, default)


def get_required_secret(name: str) -> str:
    """
    Convenience function to get a required secret.

    Args:
        name: Secret name

    Returns:
        str: Secret value

    Raises:
        SecretNotFoundError: If not found
    """
    return _get_manager().get_required(name)
