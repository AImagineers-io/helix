"""
Unit tests for feature flag configuration.

Tests cover:
- ENABLE_VARIETY_PROCESSOR flag
- ENABLE_MESSENGER flag
- ENABLE_ANALYTICS flag
- Default values (all enabled by default)
- Ability to disable features via environment
"""
import pytest
from core.config import Settings, FeatureFlags, get_settings


class TestFeatureFlags:
    """Tests for feature flag configuration."""

    def test_enable_variety_processor_default_true(self, clean_env):
        """Test that ENABLE_VARIETY_PROCESSOR defaults to True."""
        settings = Settings()
        assert settings.features.enable_variety_processor is True

    def test_enable_variety_processor_false_from_env(self, clean_env, monkeypatch):
        """Test that ENABLE_VARIETY_PROCESSOR can be disabled."""
        monkeypatch.setenv('ENABLE_VARIETY_PROCESSOR', 'false')
        settings = Settings()
        assert settings.features.enable_variety_processor is False

    def test_enable_messenger_default_true(self, clean_env):
        """Test that ENABLE_MESSENGER defaults to True."""
        settings = Settings()
        assert settings.features.enable_messenger is True

    def test_enable_messenger_false_from_env(self, clean_env, monkeypatch):
        """Test that ENABLE_MESSENGER can be disabled."""
        monkeypatch.setenv('ENABLE_MESSENGER', 'false')
        settings = Settings()
        assert settings.features.enable_messenger is False

    def test_enable_analytics_default_true(self, clean_env):
        """Test that ENABLE_ANALYTICS defaults to True."""
        settings = Settings()
        assert settings.features.enable_analytics is True

    def test_enable_analytics_false_from_env(self, clean_env, monkeypatch):
        """Test that ENABLE_ANALYTICS can be disabled."""
        monkeypatch.setenv('ENABLE_ANALYTICS', 'false')
        settings = Settings()
        assert settings.features.enable_analytics is False


class TestFeatureFlagsModel:
    """Tests for FeatureFlags as a separate model."""

    def test_feature_flags_to_dict(self, clean_env, monkeypatch):
        """Test that feature flags can be serialized to dict."""
        monkeypatch.setenv('ENABLE_MESSENGER', 'false')
        settings = Settings()
        flags_dict = settings.features.model_dump()

        assert flags_dict['enable_variety_processor'] is True
        assert flags_dict['enable_messenger'] is False
        assert flags_dict['enable_analytics'] is True

    def test_feature_flags_has_all_required_fields(self, clean_env):
        """Test that FeatureFlags exposes all required fields."""
        settings = Settings()
        features = settings.features

        assert hasattr(features, 'enable_variety_processor')
        assert hasattr(features, 'enable_messenger')
        assert hasattr(features, 'enable_analytics')

    def test_is_feature_enabled_method(self, clean_env, monkeypatch):
        """Test helper method to check if a feature is enabled."""
        monkeypatch.setenv('ENABLE_ANALYTICS', 'false')
        settings = Settings()

        assert settings.features.is_enabled('variety_processor') is True
        assert settings.features.is_enabled('messenger') is True
        assert settings.features.is_enabled('analytics') is False

    def test_is_feature_enabled_unknown_feature_returns_false(self, clean_env):
        """Test that checking unknown feature returns False."""
        settings = Settings()
        assert settings.features.is_enabled('unknown_feature') is False
