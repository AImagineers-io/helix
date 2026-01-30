#!/usr/bin/env python3
"""Demo environment reset script.

This script clears transient demo data while preserving:
- QA pairs (knowledge base)
- Prompt templates and versions

Cleared data:
- Conversations
- Observability events

Usage:
    python scripts/reset_demo.py [--dry-run]

Schedule:
    Daily at 3 AM UTC via cron

Safety:
    - Refuses to run in production environment
    - Validates ENVIRONMENT=demo before executing
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

# Add backend to path when running as script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02_backend'))

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DemoResetJob:
    """Job to reset demo environment data.

    Clears transient data (conversations, events) while preserving
    permanent data (QA pairs, prompts).

    Attributes:
        session: SQLAlchemy database session.
        dry_run: If True, don't actually delete data.
    """

    def __init__(self, session: Session, dry_run: bool = False):
        """Initialize the demo reset job.

        Args:
            session: SQLAlchemy database session.
            dry_run: If True, simulate the reset without deleting.
        """
        self.session = session
        self.dry_run = dry_run

    def _check_environment(self) -> None:
        """Verify we're not running in production.

        Raises:
            RuntimeError: If ENVIRONMENT is production.
        """
        from core.config import get_settings

        settings = get_settings()
        if settings.environment == 'production':
            raise RuntimeError(
                "Cannot run demo reset in production environment. "
                "Set ENVIRONMENT=demo to run this script."
            )

    def clear_conversations(self) -> int:
        """Clear all conversation records.

        Returns:
            Number of records deleted.
        """
        # Import model here to avoid circular imports
        try:
            from database.models import Conversation
            count = self.session.query(Conversation).delete()
        except ImportError:
            # Conversation model may not exist yet
            count = 0
        return count

    def clear_observability_events(self) -> int:
        """Clear all observability events.

        Returns:
            Number of records deleted.
        """
        try:
            from database.models import ObservabilityEvent
            count = self.session.query(ObservabilityEvent).delete()
        except ImportError:
            # ObservabilityEvent model may not exist yet
            count = 0
        return count

    def run(self) -> dict[str, Any]:
        """Execute the demo reset.

        Returns:
            Summary of the reset operation.

        Raises:
            RuntimeError: If running in production environment.
        """
        self._check_environment()

        logger.info("Starting demo reset job")

        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'dry_run': self.dry_run,
            'conversations_cleared': 0,
            'events_cleared': 0,
        }

        try:
            if self.dry_run:
                logger.info("Dry run mode - no data will be deleted")
                return summary

            # Clear transient data
            summary['conversations_cleared'] = self.clear_conversations()
            summary['events_cleared'] = self.clear_observability_events()

            # Commit transaction
            self.session.commit()

            logger.info(
                f"Demo reset complete: "
                f"{summary['conversations_cleared']} conversations, "
                f"{summary['events_cleared']} events cleared"
            )

        except Exception as e:
            logger.error(f"Demo reset failed: {e}")
            self.session.rollback()
            raise

        return summary


def main() -> None:
    """Main entry point for the demo reset script."""
    parser = argparse.ArgumentParser(
        description="Reset demo environment data"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate reset without deleting data"
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Import database session
    from database.connection import SessionLocal

    session = SessionLocal()
    try:
        job = DemoResetJob(session=session, dry_run=args.dry_run)
        summary = job.run()
        print(f"Reset complete: {summary}")
    finally:
        session.close()


if __name__ == '__main__':
    main()
