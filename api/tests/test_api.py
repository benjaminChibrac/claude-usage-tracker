"""Tests d'intégration pour l'API."""

import pytest
from fastapi.testclient import TestClient

from claude_usage_api.cache import init_cache
from claude_usage_api.main import app


@pytest.fixture
def client():
    """Fixture pour le client de test."""
    init_cache(60)  # Initialiser le cache
    return TestClient(app)


class TestHealthEndpoint:
    """Tests pour l'endpoint /health."""

    def test_health_check(self, client):
        """Test que le health check retourne 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "ccusage_available" in data


class TestConfigEndpoint:
    """Tests pour l'endpoint /config."""

    def test_get_config(self, client):
        """Test que la config est retournée."""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "session_limit_usd" in data
        assert "weekly_limit_usd" in data
        assert "cache_ttl_seconds" in data


class TestUsageEndpoints:
    """Tests pour les endpoints d'usage."""

    def test_get_session(self, client):
        """Test que les données de session sont retournées."""
        response = client.get("/usage/session")
        assert response.status_code == 200
        data = response.json()
        assert "used" in data
        assert "limit" in data
        assert "percentage" in data
        assert "is_active" in data

    def test_get_weekly(self, client):
        """Test que les données weekly sont retournées."""
        response = client.get("/usage/weekly")
        assert response.status_code == 200
        data = response.json()
        assert "used" in data
        assert "limit" in data
        assert "percentage" in data

    def test_get_full_usage(self, client):
        """Test que l'usage complet est retourné."""
        response = client.get("/usage")
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "weekly" in data
        assert "plan" in data
        assert "cached" in data


class TestCacheEndpoint:
    """Tests pour l'endpoint de cache."""

    def test_invalidate_cache(self, client):
        """Test l'invalidation du cache."""
        response = client.post("/cache/invalidate")
        assert response.status_code == 200
        data = response.json()
        assert data["invalidated"] is True
        assert data["next_refresh"] == "immediate"
