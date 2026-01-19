"""Integration tests for Analytics API.

Tests the analytics summary endpoint that provides dashboard data:
- QA pair statistics
- Conversation counts
- Cost summary
"""
import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, get_db
from api.main import create_app
from api.auth import verify_api_key
from core.config import Settings


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_settings():
    """Create test settings with API key."""
    return Settings(api_key="test-api-key")


@pytest.fixture
def client(db_session, test_settings):
    """Create test client with database override."""
    app = create_app(test_settings)

    # Override get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override API key verification
    def override_verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
        from fastapi import HTTPException
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key required")
        if x_api_key != "test-api-key":
            raise HTTPException(status_code=401, detail="Invalid API key")
        return x_api_key

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    return TestClient(app)


@pytest.fixture
def api_key_header():
    """API key header for authentication."""
    return {"X-API-Key": "test-api-key"}


class TestAnalyticsSummaryEndpoint:
    """Tests for GET /analytics/summary endpoint."""

    def test_analytics_summary_returns_200(self, client, api_key_header):
        """Test that /analytics/summary endpoint returns 200 OK."""
        response = client.get("/analytics/summary", headers=api_key_header)
        assert response.status_code == 200

    def test_analytics_summary_requires_authentication(self, client):
        """Test that /analytics/summary requires API key."""
        response = client.get("/analytics/summary")
        assert response.status_code == 401

    def test_analytics_summary_returns_json_with_stats(self, client, api_key_header):
        """Test that /analytics/summary returns JSON with expected structure."""
        response = client.get("/analytics/summary", headers=api_key_header)
        data = response.json()

        # Check top-level structure
        assert "qa_stats" in data
        assert "conversation_stats" in data
        assert "cost_summary" in data

    def test_analytics_summary_qa_stats_structure(self, client, api_key_header):
        """Test QA statistics structure."""
        response = client.get("/analytics/summary", headers=api_key_header)
        data = response.json()

        qa_stats = data["qa_stats"]
        assert "total" in qa_stats
        assert "active" in qa_stats
        assert "draft" in qa_stats
        assert "pending" in qa_stats

        # All should be integers
        assert isinstance(qa_stats["total"], int)
        assert isinstance(qa_stats["active"], int)
        assert isinstance(qa_stats["draft"], int)
        assert isinstance(qa_stats["pending"], int)

    def test_analytics_summary_conversation_stats_structure(
        self, client, api_key_header
    ):
        """Test conversation statistics structure."""
        response = client.get("/analytics/summary", headers=api_key_header)
        data = response.json()

        conv_stats = data["conversation_stats"]
        assert "today" in conv_stats
        assert "this_week" in conv_stats
        assert "this_month" in conv_stats

        # All should be integers
        assert isinstance(conv_stats["today"], int)
        assert isinstance(conv_stats["this_week"], int)
        assert isinstance(conv_stats["this_month"], int)

    def test_analytics_summary_cost_summary_structure(self, client, api_key_header):
        """Test cost summary structure."""
        response = client.get("/analytics/summary", headers=api_key_header)
        data = response.json()

        cost_summary = data["cost_summary"]
        assert "current_month" in cost_summary
        assert "projected_month_end" in cost_summary
        assert "by_provider" in cost_summary

        # Amounts should be floats
        assert isinstance(cost_summary["current_month"], (int, float))
        assert isinstance(cost_summary["projected_month_end"], (int, float))

        # Provider breakdown should be a dict
        assert isinstance(cost_summary["by_provider"], dict)

    def test_analytics_summary_provider_breakdown(self, client, api_key_header):
        """Test provider cost breakdown structure."""
        response = client.get("/analytics/summary", headers=api_key_header)
        data = response.json()

        by_provider = data["cost_summary"]["by_provider"]

        # Should have OpenAI and Anthropic keys
        assert "openai" in by_provider
        assert "anthropic" in by_provider

        # Values should be floats
        assert isinstance(by_provider["openai"], (int, float))
        assert isinstance(by_provider["anthropic"], (int, float))

    def test_analytics_summary_default_values_when_no_data(
        self, client, api_key_header
    ):
        """Test that endpoint returns zeros when no data exists."""
        response = client.get("/analytics/summary", headers=api_key_header)
        data = response.json()

        # With empty database, all counts should be 0
        assert data["qa_stats"]["total"] == 0
        assert data["conversation_stats"]["today"] == 0
        assert data["cost_summary"]["current_month"] == 0.0
