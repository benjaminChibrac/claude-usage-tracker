"""Modèles Pydantic pour l'API Claude Usage."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionProjection(BaseModel):
    """Projection de coût pour la session."""

    total_cost: float = Field(..., description="Coût total projeté de la session")
    burn_rate_per_hour: float = Field(..., description="Taux de consommation par heure")


class SessionUsage(BaseModel):
    """Métriques de session actuelle."""

    used: float = Field(..., description="Coût utilisé en USD")
    limit: float = Field(..., description="Limite de session en USD")
    percentage: float = Field(..., description="Pourcentage de consommation")
    remaining: float = Field(..., description="Budget restant en USD")
    is_active: bool = Field(..., description="Session active")
    started_at: Optional[str] = Field(None, description="Date de début de session")
    ends_at: Optional[str] = Field(None, description="Date de fin estimée de session")
    projection: Optional[SessionProjection] = Field(
        None, description="Projection de coût"
    )


class WeeklyUsage(BaseModel):
    """Métriques hebdomadaires."""

    used: float = Field(..., description="Coût utilisé cette semaine en USD")
    limit: float = Field(..., description="Limite hebdomadaire en USD")
    percentage: float = Field(..., description="Pourcentage de consommation")
    remaining: float = Field(..., description="Budget restant en USD")
    week_start: Optional[str] = Field(None, description="Date de début de semaine")


class UsageResponse(BaseModel):
    """Réponse complète de l'endpoint /usage."""

    session: SessionUsage
    weekly: WeeklyUsage
    plan: str = Field(..., description="Plan Claude (pro, max_5x, max_20x)")
    cached: bool = Field(False, description="Données en cache")
    cached_at: Optional[str] = Field(None, description="Date de mise en cache")


class HealthResponse(BaseModel):
    """Réponse de l'endpoint health check."""

    status: str = Field("ok", description="État du service")
    ccusage_available: bool = Field(..., description="ccusage est disponible")


class CacheInvalidateResponse(BaseModel):
    """Réponse de l'endpoint d'invalidation du cache."""

    invalidated: bool = Field(True, description="Cache invalidé avec succès")
    next_refresh: str = Field("immediate", description="Prochain rafraîchissement")


class ConfigResponse(BaseModel):
    """Réponse de l'endpoint de configuration."""

    plan: str = Field(..., description="Plan configuré")
    session_limit_usd: float = Field(..., description="Limite de session")
    weekly_limit_usd: float = Field(..., description="Limite hebdomadaire")
    cache_ttl_seconds: int = Field(..., description="TTL du cache")


class ModelUsage(BaseModel):
    """Métriques par modèle."""

    model_name: str = Field(..., description="Nom du modèle")
    used: float = Field(..., description="Coût utilisé en USD")
    limit: float = Field(..., description="Limite pour ce modèle en USD")
    percentage: float = Field(..., description="Pourcentage de consommation")
    remaining: float = Field(..., description="Budget restant en USD")
    input_tokens: int = Field(0, description="Tokens d'entrée")
    output_tokens: int = Field(0, description="Tokens de sortie")


class ModelBreakdownResponse(BaseModel):
    """Réponse avec breakdown par modèle."""

    models: list[ModelUsage] = Field(..., description="Liste des modèles utilisés")
    total_used: float = Field(..., description="Coût total utilisé")
    total_limit: float = Field(..., description="Limite totale")
    total_percentage: float = Field(..., description="Pourcentage global")
    period: str = Field(..., description="Période (daily, weekly, session)")
    start_date: Optional[str] = Field(None, description="Date de début")
