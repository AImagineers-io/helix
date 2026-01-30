"""Database content audit tests (P4.2a).

Verifies that database content (QA pairs, prompts, automations)
doesn't contain client-specific branding terms.

Note: This test requires a database connection and scans existing content.
For new deployments, this ensures no prohibited terms slip through seeding.
"""
import pytest


class TestQAPairContent:
    """Audit QA pair content for prohibited terms."""

    PROHIBITED_TERMS = ["palai", "philrice"]

    @pytest.fixture
    def qa_pairs(self, db_session):
        """Get all QA pairs from database."""
        from database.models import QAPair

        return db_session.query(QAPair).all()

    def test_no_palai_in_qa_questions(self, qa_pairs):
        """QA pair questions should not contain 'palai'."""
        violations = []
        for qa in qa_pairs:
            if "palai" in qa.question.lower():
                violations.append(f"QA #{qa.id}: {qa.question[:50]}...")

        if violations:
            pytest.fail(
                f"Found 'palai' in {len(violations)} QA pair question(s):\n" +
                "\n".join(f"  - {v}" for v in violations[:10])
            )

    def test_no_palai_in_qa_answers(self, qa_pairs):
        """QA pair answers should not contain 'palai'."""
        violations = []
        for qa in qa_pairs:
            if "palai" in qa.answer.lower():
                violations.append(f"QA #{qa.id}: {qa.answer[:50]}...")

        if violations:
            pytest.fail(
                f"Found 'palai' in {len(violations)} QA pair answer(s):\n" +
                "\n".join(f"  - {v}" for v in violations[:10])
            )

    def test_no_philrice_in_qa_content(self, qa_pairs):
        """QA pairs should not contain 'philrice'."""
        violations = []
        for qa in qa_pairs:
            content = f"{qa.question} {qa.answer}".lower()
            if "philrice" in content:
                violations.append(f"QA #{qa.id}")

        if violations:
            pytest.fail(
                f"Found 'philrice' in {len(violations)} QA pair(s): {violations[:10]}"
            )


class TestPromptContent:
    """Audit prompt template content for prohibited terms."""

    @pytest.fixture
    def prompt_versions(self, db_session):
        """Get all prompt versions from database."""
        from database.models import PromptVersion

        return db_session.query(PromptVersion).all()

    def test_no_palai_in_prompts(self, prompt_versions):
        """Prompt templates should not contain 'palai'."""
        violations = []
        for pv in prompt_versions:
            if "palai" in pv.content.lower():
                violations.append(f"Prompt #{pv.template_id} v{pv.version_number}")

        if violations:
            pytest.fail(
                f"Found 'palai' in {len(violations)} prompt version(s): {violations[:10]}"
            )

    def test_no_philrice_in_prompts(self, prompt_versions):
        """Prompt templates should not contain 'philrice'."""
        violations = []
        for pv in prompt_versions:
            if "philrice" in pv.content.lower():
                violations.append(f"Prompt #{pv.template_id} v{pv.version_number}")

        if violations:
            pytest.fail(
                f"Found 'philrice' in {len(violations)} prompt version(s): {violations[:10]}"
            )


class TestConversationContent:
    """Audit conversation content for prohibited terms."""

    @pytest.fixture
    def conversations(self, db_session):
        """Get recent conversations from database."""
        from database.models import Conversation

        # Only check recent conversations (last 1000)
        return db_session.query(Conversation).order_by(
            Conversation.created_at.desc()
        ).limit(1000).all()

    def test_no_palai_in_bot_messages(self, conversations):
        """Bot messages in conversations should not contain 'palai'."""
        # Note: This test may have false positives if users mention 'palai'.
        # We only check bot/assistant messages, not user messages.
        violations = []
        for conv in conversations:
            if hasattr(conv, 'messages'):
                for msg in conv.messages:
                    if msg.role in ('assistant', 'bot') and "palai" in msg.content.lower():
                        violations.append(f"Conv #{conv.id}")
                        break

        if violations:
            pytest.fail(
                f"Found 'palai' in {len(violations)} conversation bot message(s)"
            )


class TestLocalAutomationContent:
    """Audit local automation content for prohibited terms."""

    @pytest.fixture
    def local_automations(self, db_session):
        """Get all local automations from database."""
        try:
            from database.models import LocalAutomation
            return db_session.query(LocalAutomation).all()
        except (ImportError, AttributeError):
            # Model doesn't exist
            return []

    def test_no_palai_in_automations(self, local_automations):
        """Local automations should not contain 'palai'."""
        if not local_automations:
            pytest.skip("No LocalAutomation model or no records")

        violations = []
        for auto in local_automations:
            content = str(auto.__dict__).lower()
            if "palai" in content:
                violations.append(f"Automation #{auto.id}")

        if violations:
            pytest.fail(
                f"Found 'palai' in {len(violations)} automation(s): {violations[:10]}"
            )


class TestDatabaseAuditReport:
    """Generate audit report of database content."""

    def test_generate_audit_report(self, db_session, tmp_path):
        """Generate a report of all database content containing prohibited terms."""
        # This test generates a report file for manual review
        report_lines = ["# Database Content Audit Report\n"]
        report_lines.append("## Prohibited Terms: palai, philrice\n")

        # Check QA Pairs
        try:
            from database.models import QAPair
            qa_pairs = db_session.query(QAPair).all()
            qa_violations = []
            for qa in qa_pairs:
                content = f"{qa.question} {qa.answer}".lower()
                if "palai" in content or "philrice" in content:
                    qa_violations.append(qa.id)

            report_lines.append(f"\n### QA Pairs: {len(qa_violations)} violations\n")
            for qid in qa_violations[:20]:
                report_lines.append(f"- QA #{qid}\n")
            if len(qa_violations) > 20:
                report_lines.append(f"- ... and {len(qa_violations) - 20} more\n")
        except Exception as e:
            report_lines.append(f"\n### QA Pairs: Error - {e}\n")

        # Check Prompts
        try:
            from database.models import PromptVersion
            prompts = db_session.query(PromptVersion).all()
            prompt_violations = []
            for p in prompts:
                if "palai" in p.content.lower() or "philrice" in p.content.lower():
                    prompt_violations.append(p.id)

            report_lines.append(f"\n### Prompts: {len(prompt_violations)} violations\n")
            for pid in prompt_violations[:20]:
                report_lines.append(f"- Prompt Version #{pid}\n")
        except Exception as e:
            report_lines.append(f"\n### Prompts: Error - {e}\n")

        # Write report (for CI artifacts)
        report_path = tmp_path / "db_audit_report.md"
        report_path.write_text("".join(report_lines))

        # Test passes - report is informational
        # Actual violations are caught by other tests
        assert report_path.exists()
