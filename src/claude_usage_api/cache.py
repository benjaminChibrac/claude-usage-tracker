"""Cache TTL en mémoire pour l'API Claude Usage."""

import time
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from claude_usage_api.models import UsageResponse


class TTLCache:
    """Cache simple en mémoire avec TTL (Time To Live)."""

    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._cache: Optional[Tuple[UsageResponse, float]] = None

    def get(self) -> Optional[UsageResponse]:
        """Récupère les données du cache si elles sont encore valides."""
        if self._cache is None:
            return None

        data, timestamp = self._cache
        if time.time() - timestamp > self.ttl_seconds:
            # Cache expiré
            self._cache = None
            return None

        # Met à jour le flag cached
        return data

    def set(self, data: UsageResponse) -> None:
        """Stocke les données dans le cache."""
        self._cache = (data, time.time())

    def invalidate(self) -> bool:
        """Invalide le cache."""
        was_cached = self._cache is not None
        self._cache = None
        return was_cached

    def get_cached_at(self) -> Optional[str]:
        """Retourne la date de mise en cache au format ISO."""
        if self._cache is None:
            return None

        _, timestamp = self._cache
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.isoformat()


# Instance globale du cache (sera initialisée avec les settings)
_cache_instance: Optional[TTLCache] = None


def init_cache(ttl_seconds: int) -> None:
    """Initialise le cache global."""
    global _cache_instance
    _cache_instance = TTLCache(ttl_seconds)


def get_cache() -> TTLCache:
    """Retourne l'instance du cache."""
    if _cache_instance is None:
        raise RuntimeError("Cache not initialized. Call init_cache() first.")
    return _cache_instance
