"""Integration tests for demo reset job.

Tests that the demo reset script properly clears transient data
while preserving QA pairs and prompt configurations.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock


class TestDemoResetJob:
    """Tests for demo reset job functionality."""

    @pytest.fixture
    def demo_env(self, clean_env):
        """Set up demo environment for tests."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        from core.config import get_settings
        get_settings.cache_clear()
        return clean_env

    def test_reset_returns_summary(self, demo_env):
        """Reset should return a summary of cleared data."""
        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        mock_session.query.return_value.delete.return_value = 10

        job = DemoResetJob(session=mock_session)
        summary = job.run()

        assert 'conversations_cleared' in summary
        assert 'events_cleared' in summary
        assert 'timestamp' in summary
        assert isinstance(summary['conversations_cleared'], int)
        assert isinstance(summary['events_cleared'], int)

    def test_reset_commits_transaction(self, demo_env):
        """Reset should commit the transaction."""
        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        job = DemoResetJob(session=mock_session)
        job.run()

        mock_session.commit.assert_called()

    def test_reset_preserves_qa_pairs(self, demo_env):
        """Reset should NOT delete QA pairs."""
        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        job = DemoResetJob(session=mock_session)

        # QA pairs should not be cleared
        job.run()

        # Get all query calls and check none are for QAPair
        for call in mock_session.query.call_args_list:
            args = call[0]
            for arg in args:
                if hasattr(arg, '__name__'):
                    assert arg.__name__ != 'QAPair', "Should not query QAPair table"

    def test_reset_preserves_prompts(self, demo_env):
        """Reset should NOT delete prompt templates."""
        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        job = DemoResetJob(session=mock_session)

        job.run()

        # Get all query calls and check none are for PromptTemplate
        for call in mock_session.query.call_args_list:
            args = call[0]
            for arg in args:
                if hasattr(arg, '__name__'):
                    assert arg.__name__ != 'PromptTemplate', "Should not query PromptTemplate table"

    def test_reset_rolls_back_on_error(self, demo_env):
        """Reset should rollback on error."""
        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        # Make commit raise an error to simulate transaction failure
        mock_session.commit.side_effect = Exception("Commit Error")

        job = DemoResetJob(session=mock_session)

        with pytest.raises(Exception, match="Commit Error"):
            job.run()

        mock_session.rollback.assert_called()


class TestDemoResetCLI:
    """Tests for demo reset CLI interface."""

    def test_main_function_exists(self, clean_env):
        """Reset script should have a main function."""
        from scripts.reset_demo import main

        assert callable(main)

    def test_dry_run_mode(self, clean_env):
        """Reset should support dry-run mode without deleting."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        from core.config import get_settings
        get_settings.cache_clear()

        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        job = DemoResetJob(session=mock_session, dry_run=True)
        summary = job.run()

        # In dry run, should not call commit
        mock_session.commit.assert_not_called()
        assert summary.get('dry_run') is True

    def test_environment_check_prevents_production_run(self, clean_env):
        """Reset should refuse to run in production environment."""
        clean_env.setenv('ENVIRONMENT', 'production')
        clean_env.setenv('DATABASE_URL', 'postgresql://user:pass@prod-db:5432/helix')

        from core.config import get_settings
        get_settings.cache_clear()

        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        job = DemoResetJob(session=mock_session)

        with pytest.raises(RuntimeError, match="Cannot run demo reset in production"):
            job.run()


class TestDemoResetLogging:
    """Tests for demo reset logging."""

    @pytest.fixture
    def demo_env(self, clean_env):
        """Set up demo environment for tests."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        from core.config import get_settings
        get_settings.cache_clear()
        return clean_env

    def test_logs_reset_start(self, demo_env, caplog):
        """Reset should log when it starts."""
        import logging
        caplog.set_level(logging.INFO)

        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        job = DemoResetJob(session=mock_session)
        job.run()

        assert any('Starting demo reset' in record.message for record in caplog.records)

    def test_logs_completion_summary(self, demo_env, caplog):
        """Reset should log completion summary."""
        import logging
        caplog.set_level(logging.INFO)

        from scripts.reset_demo import DemoResetJob

        mock_session = MagicMock()
        mock_session.query.return_value.delete.return_value = 5
        job = DemoResetJob(session=mock_session)
        job.run()

        assert any('Demo reset complete' in record.message for record in caplog.records)


class TestDemoResetIntegration:
    """Integration tests with actual model clearing."""

    @pytest.fixture
    def demo_env(self, clean_env):
        """Set up demo environment for tests."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        from core.config import get_settings
        get_settings.cache_clear()
        return clean_env

    def test_clear_conversations_with_mock_model(self, demo_env):
        """Test clearing conversations using mocked model."""
        from scripts.reset_demo import DemoResetJob

        # Mock the model import
        with patch.dict('sys.modules', {'database.models': MagicMock()}):
            mock_session = MagicMock()
            mock_session.query.return_value.delete.return_value = 10

            job = DemoResetJob(session=mock_session)
            summary = job.run()

            assert summary['conversations_cleared'] >= 0
            assert summary['events_cleared'] >= 0
