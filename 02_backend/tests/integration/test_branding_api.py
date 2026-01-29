"""
Integration tests for branding API endpoint.

Tests that the branding API properly implements caching headers
for performance optimization.
"""
import os
import pytest

# Set required environment variables BEFORE importing app
os.environ['APP_NAME'] = 'TestApp'
os.environ['BOT_NAME'] = 'TestBot'
os.environ['DATABASE_URL'] = 'postgresql://localhost/test'

from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    yield TestClient(app)


class TestBrandingAPICache:
    """Test suite for branding API caching."""

    def test_branding_endpoint_returns_cache_control_header(self, client):
        """Test that branding endpoint includes Cache-Control header."""
        # Act
        response = client.get('/branding')

        # Assert
        assert response.status_code == 200
        assert 'Cache-Control' in response.headers
        assert 'public' in response.headers['Cache-Control']
        assert 'max-age' in response.headers['Cache-Control']

    def test_branding_endpoint_cache_max_age_is_3600(self, client):
        """Test that Cache-Control max-age is 3600 seconds (1 hour)."""
        # Act
        response = client.get('/branding')

        # Assert
        assert response.status_code == 200
        cache_control = response.headers.get('Cache-Control', '')
        assert 'max-age=3600' in cache_control

    def test_branding_endpoint_returns_etag_header(self, client):
        """Test that branding endpoint includes ETag header."""
        # Act
        response = client.get('/branding')

        # Assert
        assert response.status_code == 200
        assert 'ETag' in response.headers
        assert len(response.headers['ETag']) > 0

    def test_branding_endpoint_etag_is_consistent(self, client):
        """Test that ETag is consistent for same content."""
        # Act
        response1 = client.get('/branding')
        response2 = client.get('/branding')

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.headers['ETag'] == response2.headers['ETag']

    def test_branding_endpoint_supports_conditional_request(self, client):
        """Test that branding endpoint supports If-None-Match conditional requests."""
        # Arrange: Get initial response with ETag
        initial_response = client.get('/branding')
        etag = initial_response.headers['ETag']

        # Act: Send conditional request with If-None-Match
        response = client.get('/branding', headers={'If-None-Match': etag})

        # Assert: Should return 304 Not Modified
        assert response.status_code == 304

    def test_branding_endpoint_returns_full_response_on_etag_mismatch(self, client):
        """Test that branding endpoint returns full response when ETag doesn't match."""
        # Act: Send conditional request with incorrect ETag
        response = client.get('/branding', headers={'If-None-Match': '"wrong-etag"'})

        # Assert: Should return 200 with full content
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_branding_endpoint_etag_changes_when_config_changes(self, client):
        """Test that ETag changes when branding config changes."""
        # Note: This test is difficult to implement without restarting the app
        # since config is cached. Skipping for now as it would require
        # more complex test infrastructure.
        pytest.skip("Config caching makes this test impractical in current setup")
