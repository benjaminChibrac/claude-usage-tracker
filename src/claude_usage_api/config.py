"""Configuration de l'API Claude Usage."""

from functools import lru_cache
from typing import Dict, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# Presets des limites par plan
PLAN_LIMITS: Dict[str, Dict[str, float]] = {
    "pro": {"session": 3.5, "weekly": 35.0},
    "max_5x": {"session": 17.5, "weekly": 175.0},
    "max_20x": {"session": 70.0, "weekly": 700.0},
}


class Settings(BaseSettings):
    """Configuration de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Plan Claude
    claude_plan: str = "pro"

    # Limites personnalisées (override les presets)
    session_limit_usd: Optional[float] = None
    weekly_limit_usd: Optional[float] = None

    # Cache
    cache_ttl_seconds: int = 60

    # Reset hebdomadaire (jour: 0=lundi, 5=samedi, 6=dimanche)
    weekly_reset_day: int = 0  # Par défaut lundi (comportement standard)
    weekly_reset_hour: int = 0  # Par défaut minuit

    # Limites par modèle (calibrées pour matcher l'affichage Claude.ai)
    # Avec 8.53$ utilisé et 20% affiché -> limite effective ~42.65$
    model_opus_limit: float = 12.8  # ~30% de 42.65$
    model_sonnet_limit: float = 17.1  # ~40% de 42.65$
    model_haiku_limit: float = 12.8  # ~30% de 42.65$

    # Limite globale effective pour le calcul du %
    weekly_limit_effective: float = 42.65

    # Auth
    api_key: Optional[str] = None

    # Serveur
    host: str = "0.0.0.0"
    port: int = 8383

    def get_session_limit(self) -> float:
        """Retourne la limite de session en USD."""
        if self.session_limit_usd is not None:
            return self.session_limit_usd
        return PLAN_LIMITS.get(self.claude_plan, PLAN_LIMITS["pro"])["session"]

    def get_weekly_limit(self) -> float:
        """Retourne la limite hebdomadaire en USD."""
        if self.weekly_limit_usd is not None:
            return self.weekly_limit_usd
        return PLAN_LIMITS.get(self.claude_plan, PLAN_LIMITS["pro"])["weekly"]


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance singleton des settings."""
    return Settings()
