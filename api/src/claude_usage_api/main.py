"""Application FastAPI principale pour Claude Usage API."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse

from claude_usage_api.cache import get_cache, init_cache
from claude_usage_api.config import get_settings
from claude_usage_api.models import (
    CacheInvalidateResponse,
    ConfigResponse,
    HealthResponse,
    ModelBreakdownResponse,
    SessionUsage,
    UsageResponse,
    WeeklyUsage,
)
from claude_usage_api.usage_service import (
    check_ccusage_available,
    get_full_usage,
    get_session_usage,
    get_usage_by_model,
    get_weekly_usage,
)


# Vérification de l'API key
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Vérifie l'API key si configurée."""
    settings = get_settings()
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Startup
    settings = get_settings()
    init_cache(settings.cache_ttl_seconds)
    yield
    # Shutdown


app = FastAPI(
    title="Claude Usage API",
    description="API REST pour les métriques d'utilisation Claude Code",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check de l'API."""
    return HealthResponse(
        status="ok",
        ccusage_available=check_ccusage_available(),
    )


@app.get("/usage", response_model=UsageResponse)
async def get_usage(
    _: None = Depends(verify_api_key),
) -> UsageResponse:
    """Retourne l'état complet de consommation (session + weekly)."""
    cache = get_cache()

    # Vérification du cache
    cached_data = cache.get()
    if cached_data:
        cached_data.cached = True
        cached_data.cached_at = cache.get_cached_at()
        return cached_data

    # Récupération des données fraîches
    usage_data = await get_full_usage()

    # Mise en cache
    cache.set(usage_data)

    return usage_data


@app.get("/usage/session", response_model=SessionUsage)
async def get_session(
    _: None = Depends(verify_api_key),
) -> SessionUsage:
    """Retourne uniquement les données de session."""
    session_usage, _ = await get_session_usage()
    return session_usage


@app.get("/usage/weekly", response_model=WeeklyUsage)
async def get_weekly(
    _: None = Depends(verify_api_key),
) -> WeeklyUsage:
    """Retourne uniquement les données hebdomadaires."""
    return await get_weekly_usage()


@app.get("/usage/by-model", response_model=ModelBreakdownResponse)
async def get_model_breakdown(
    period: str = "weekly",
    _: None = Depends(verify_api_key),
) -> ModelBreakdownResponse:
    """Retourne le breakdown par modèle avec pourcentages spécifiques.

    Périodes disponibles: daily, weekly, session
    """
    return await get_usage_by_model(period)


@app.get("/config", response_model=ConfigResponse)
async def get_config(
    _: None = Depends(verify_api_key),
) -> ConfigResponse:
    """Retourne la configuration actuelle."""
    settings = get_settings()
    return ConfigResponse(
        plan=settings.claude_plan,
        session_limit_usd=settings.get_session_limit(),
        weekly_limit_usd=settings.get_weekly_limit(),
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


@app.post("/cache/invalidate", response_model=CacheInvalidateResponse)
async def invalidate_cache(
    _: None = Depends(verify_api_key),
) -> CacheInvalidateResponse:
    """Force le rafraîchissement du cache."""
    cache = get_cache()
    was_invalidated = cache.invalidate()

    return CacheInvalidateResponse(
        invalidated=was_invalidated,
        next_refresh="immediate",
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Gestionnaire d'exceptions global."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )
