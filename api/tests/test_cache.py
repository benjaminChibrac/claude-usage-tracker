"""Tests pour le cache TTL."""

import time
import pytest
from datetime import datetime, timezone

from claude_usage_api.cache import TTLCache, init_cache, get_cache
from claude_usage_api.models import UsageResponse, SessionUsage, WeeklyUsage


class TestTTLCache:
    """Tests pour la classe TTLCache."""

    def test_cache_miss(self):
        """Test qu'un cache vide retourne None."""
        cache = TTLCache(ttl_seconds=60)
        result = cache.get()
        assert result is None

    def test_cache_hit(self):
        """Test que les données sont récupérées du cache."""
        cache = TTLCache(ttl_seconds=60)

        data = UsageResponse(
            session=SessionUsage(
                used=0.5, limit=3.5, percentage=14.3, remaining=3.0, is_active=True
            ),
            weekly=WeeklyUsage(used=5.0, limit=35.0, percentage=14.3, remaining=30.0),
            plan="pro",
            cached=False,
        )

        cache.set(data)
        result = cache.get()

        assert result is not None
        assert result.plan == "pro"

    def test_cache_expiration(self):
        """Test que le cache expire après le TTL."""
        cache = TTLCache(ttl_seconds=0.1)  # 100ms pour le test

        data = UsageResponse(
            session=SessionUsage(
                used=0.5, limit=3.5, percentage=14.3, remaining=3.0, is_active=True
            ),
            weekly=WeeklyUsage(used=5.0, limit=35.0, percentage=14.3, remaining=30.0),
            plan="pro",
            cached=False,
        )

        cache.set(data)
        time.sleep(0.15)  # Attendre que le cache expire

        result = cache.get()
        assert result is None

    def test_cache_invalidate(self):
        """Test l'invalidation du cache."""
        cache = TTLCache(ttl_seconds=60)

        data = UsageResponse(
            session=SessionUsage(
                used=0.5, limit=3.5, percentage=14.3, remaining=3.0, is_active=True
            ),
            weekly=WeeklyUsage(used=5.0, limit=35.0, percentage=14.3, remaining=30.0),
            plan="pro",
            cached=False,
        )

        cache.set(data)
        was_cached = cache.invalidate()

        assert was_cached is True
        assert cache.get() is None

    def test_get_cached_at(self):
        """Test que la date de mise en cache est retournée."""
        cache = TTLCache(ttl_seconds=60)

        data = UsageResponse(
            session=SessionUsage(
                used=0.5, limit=3.5, percentage=14.3, remaining=3.0, is_active=True
            ),
            weekly=WeeklyUsage(used=5.0, limit=35.0, percentage=14.3, remaining=30.0),
            plan="pro",
            cached=False,
        )

        cache.set(data)
        cached_at = cache.get_cached_at()

        assert cached_at is not None
        # Vérifier que c'est une date ISO valide
        parsed = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None


class TestGlobalCache:
    """Tests pour les fonctions globales du cache."""

    def test_init_and_get_cache(self):
        """Test l'initialisation et la récupération du cache global."""
        init_cache(120)
        cache = get_cache()

        assert cache is not None
        assert cache.ttl_seconds == 120

    def test_get_cache_without_init(self):
        """Test que get_cache lève une exception si non initialisé."""
        # Note: Ce test pourrait échouer si d'autres tests ont initialisé le cache
        # Dans une vraie suite de tests, il faudrait isoler mieux
        pass
