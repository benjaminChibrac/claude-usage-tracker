"""Service d'appel à ccusage et parsing des données."""

import asyncio
import json
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from claude_usage_api.config import get_settings
from claude_usage_api.models import (
    ModelBreakdownResponse,
    ModelUsage,
    SessionProjection,
    SessionUsage,
    UsageResponse,
    WeeklyUsage,
)


class CCUsageError(Exception):
    """Exception levée en cas d'erreur avec ccusage."""

    pass


async def run_ccusage_command(args: List[str]) -> Dict[str, Any]:
    """Exécute une commande ccusage et retourne le JSON parsé."""
    cmd = ["npx", "ccusage"] + args

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0,
        )

        if process.returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace")
            raise CCUsageError(
                f"ccusage failed with code {process.returncode}: {stderr_text}"
            )

        stdout_text = stdout.decode("utf-8", errors="replace")
        return json.loads(stdout_text)

    except asyncio.TimeoutError:
        raise CCUsageError("ccusage command timed out after 30s")
    except json.JSONDecodeError as e:
        raise CCUsageError(f"Failed to parse ccusage output: {e}")
    except FileNotFoundError:
        raise CCUsageError("npx not found. Is Node.js installed?")


def parse_session_blocks(data: Dict[str, Any]) -> Tuple[Optional[Dict], float]:
    """Extrait le bloc de session actif et calcule le coût total."""
    blocks = data.get("blocks", [])

    active_block = None
    total_cost = 0.0

    for block in blocks:
        # Skip les gaps
        if block.get("isGap", False):
            continue

        cost = block.get("costUSD", 0.0)
        total_cost += cost

        # Un bloc actif a isActive = true
        if block.get("isActive", False):
            active_block = block

    return active_block, total_cost


def calculate_projection(
    used: float,
    started_at: datetime,
    session_limit: float,
) -> Optional[SessionProjection]:
    """Calcule la projection de coût pour la session complète."""
    now = datetime.now(timezone.utc)
    elapsed = now - started_at
    elapsed_hours = elapsed.total_seconds() / 3600

    if elapsed_hours < 0.1:  # Éviter division par zéro pour les sessions très récentes
        return None

    burn_rate = used / elapsed_hours  # $/heure

    # Projection sur 5 heures (durée standard d'une session)
    projected_total = burn_rate * 5.0

    return SessionProjection(
        total_cost=round(projected_total, 2),
        burn_rate_per_hour=round(burn_rate, 2),
    )


def parse_iso_datetime(iso_str: Optional[str]) -> Optional[datetime]:
    """Parse une date ISO string en datetime."""
    if not iso_str:
        return None

    try:
        # Gère les formats avec ou sans timezone
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        return datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return None


async def get_session_usage() -> Tuple[SessionUsage, float]:
    """Récupère les métriques de session via ccusage blocks."""
    settings = get_settings()

    try:
        data = await run_ccusage_command(["blocks", "--json"])
    except CCUsageError:
        # Fallback: retourne une session inactive
        return SessionUsage(
            used=0.0,
            limit=settings.get_session_limit(),
            percentage=0.0,
            remaining=settings.get_session_limit(),
            is_active=False,
            started_at=None,
            ends_at=None,
            projection=None,
        ), 0.0

    active_block, total_cost = parse_session_blocks(data)
    session_limit = settings.get_session_limit()

    if active_block is None:
        # Pas de session active
        return SessionUsage(
            used=0.0,
            limit=session_limit,
            percentage=0.0,
            remaining=session_limit,
            is_active=False,
            started_at=None,
            ends_at=None,
            projection=None,
        ), total_cost

    # Session active
    used = active_block.get("costUSD", 0.0)
    # Utiliser la limite effective pour le calcul du % (comme pour weekly)
    session_limit_effective = settings.session_limit_effective
    percentage = (used / session_limit_effective * 100) if session_limit_effective > 0 else 0.0
    remaining = max(0.0, session_limit - used)

    started_at_str = active_block.get("startTime")
    started_at = parse_iso_datetime(started_at_str)

    # Calcul de la fin estimée (5h après le début)
    ends_at_str = None
    if started_at:
        ends_at = started_at + timedelta(hours=5)
        ends_at_str = ends_at.isoformat()

    # Projection
    projection = None
    if started_at:
        projection = calculate_projection(used, started_at, session_limit)

    return SessionUsage(
        used=round(used, 2),
        limit=session_limit,
        percentage=round(percentage, 2),
        remaining=round(remaining, 2),
        is_active=True,
        started_at=started_at_str,
        ends_at=ends_at_str,
        projection=projection,
    ), total_cost


def get_current_week_start(reset_day: int, reset_hour: int) -> datetime:
    """Calcule le début de la semaine courante basé sur le jour de reset."""
    now = datetime.now(timezone.utc)
    current_weekday = now.weekday()  # 0=lundi, 5=samedi, 6=dimanche

    # Calculer combien de jours on doit remonter pour atteindre le dernier reset
    days_since_reset = (current_weekday - reset_day) % 7

    # Date du dernier reset
    week_start = now - timedelta(days=days_since_reset)
    week_start = week_start.replace(hour=reset_hour, minute=0, second=0, microsecond=0)

    # Si on est avant l'heure de reset aujourd'hui, remonter d'une semaine de plus
    if now < week_start:
        week_start = week_start - timedelta(days=7)

    return week_start


async def get_weekly_usage() -> WeeklyUsage:
    """Récupère les métriques hebdomadaires via ccusage daily + session active."""
    settings = get_settings()

    try:
        # Récupérer daily ET blocks en parallèle
        data, blocks_data = await asyncio.gather(
            run_ccusage_command(["daily", "--json"]),
            run_ccusage_command(["blocks", "--json"])
        )
    except CCUsageError:
        # Fallback: retourne des données vides
        return WeeklyUsage(
            used=0.0,
            limit=settings.get_weekly_limit(),
            percentage=0.0,
            remaining=settings.get_weekly_limit(),
            week_start=None,
        )

    daily_entries = data.get("daily", [])
    # Utiliser la limite effective calibrée (42.65$) au lieu de la limite standard (35$)
    weekly_limit = settings.weekly_limit_effective

    # Calculer le début de la semaine courante selon la config
    week_start = get_current_week_start(
        settings.weekly_reset_day, settings.weekly_reset_hour
    )
    week_end = week_start + timedelta(days=7)

    # Agréger les coûts des jours dans la période de facturation
    total_cost = 0.0
    today = datetime.now(timezone.utc).date()
    today_date = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    today_included = False

    for entry in daily_entries:
        date_str = entry.get("date")
        if not date_str:
            continue

        try:
            entry_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            entry_date_only = entry_date.date()

            # Vérifier si ce jour est dans notre période de facturation
            # Comparer uniquement les dates (sans les heures)
            if week_start.date() <= entry_date_only < week_end.date():
                total_cost += entry.get("totalCost", 0.0)
                # Vérifier si aujourd'hui est déjà dans les données daily
                if entry_date_only == today:
                    today_included = True
        except (ValueError, TypeError):
            continue

    # Si aujourd'hui n'est pas encore dans daily, ajouter le coût de la session active
    if not today_included and week_start.date() <= today < week_end.date():
        active_block, _ = parse_session_blocks(blocks_data)
        if active_block:
            session_cost = active_block.get("costUSD", 0.0)
            total_cost += session_cost

    percentage = (total_cost / weekly_limit * 100) if weekly_limit > 0 else 0.0
    remaining = max(0.0, weekly_limit - total_cost)

    return WeeklyUsage(
        used=round(total_cost, 2),
        limit=weekly_limit,
        percentage=round(percentage, 2),
        remaining=round(remaining, 2),
        week_start=week_start.strftime("%Y-%m-%d"),
    )


async def get_full_usage() -> UsageResponse:
    """Récupère l'état complet de consommation."""
    settings = get_settings()

    # Récupération parallèle des données
    (session_usage, _), weekly_usage = await asyncio.gather(
        get_session_usage(),
        get_weekly_usage()
    )

    return UsageResponse(
        session=session_usage,
        weekly=weekly_usage,
        plan=settings.claude_plan,
        cached=False,
        cached_at=None,
    )


def check_ccusage_available() -> bool:
    """Vérifie si ccusage est disponible sur le système."""
    try:
        result = subprocess.run(
            ["npx", "ccusage", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def get_usage_by_model(period: str = "weekly") -> ModelBreakdownResponse:
    """Calcule l'usage par modèle avec pourcentages spécifiques."""
    settings = get_settings()

    try:
        if period == "session":
            # Pour la session, on utilise les données blocks
            data = await run_ccusage_command(["blocks", "--json"])
            blocks = data.get("blocks", [])

            # Agréger les coûts par modèle pour les blocs de la session actuelle
            model_costs: Dict[str, Dict[str, Any]] = {}
            for block in blocks:
                if block.get("isGap", False):
                    continue
                # Si c'est la session active ou si on veut toute la journée
                for model_breakdown in block.get("modelBreakdowns", []):
                    model_name = model_breakdown["modelName"]
                    if model_name not in model_costs:
                        model_costs[model_name] = {
                            "cost": 0.0,
                            "inputTokens": 0,
                            "outputTokens": 0,
                        }
                    model_costs[model_name]["cost"] += model_breakdown.get("cost", 0.0)
                    model_costs[model_name]["inputTokens"] += model_breakdown.get(
                        "inputTokens", 0
                    )
                    model_costs[model_name]["outputTokens"] += model_breakdown.get(
                        "outputTokens", 0
                    )

            week_start = None

        else:
            # Pour daily/weekly, on utilise les données daily
            data = await run_ccusage_command(["daily", "--json"])
            daily_entries = data.get("daily", [])

            # Calculer la période
            if period == "weekly":
                week_start = get_current_week_start(
                    settings.weekly_reset_day, settings.weekly_reset_hour
                )
                week_end = week_start + timedelta(days=7)
            else:
                week_start = None
                week_end = None

            # Agréger les coûts par modèle
            model_costs: Dict[str, Dict[str, Any]] = {}
            for entry in daily_entries:
                date_str = entry.get("date")
                if not date_str:
                    continue

                try:
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )

                    # Vérifier si ce jour est dans la période
                    if period == "weekly":
                        if not (
                            week_start.date() <= entry_date.date() < week_end.date()
                        ):
                            continue

                    for model_breakdown in entry.get("modelBreakdowns", []):
                        model_name = model_breakdown["modelName"]
                        if model_name not in model_costs:
                            model_costs[model_name] = {
                                "cost": 0.0,
                                "inputTokens": 0,
                                "outputTokens": 0,
                            }
                        model_costs[model_name]["cost"] += model_breakdown.get(
                            "cost", 0.0
                        )
                        model_costs[model_name]["inputTokens"] += model_breakdown.get(
                            "inputTokens", 0
                        )
                        model_costs[model_name]["outputTokens"] += model_breakdown.get(
                            "outputTokens", 0
                        )
                except (ValueError, TypeError):
                    continue

    except CCUsageError as e:
        raise e

    # Calculer les métriques par modèle
    models_usage = []
    total_used = 0.0
    total_limit = 0.0

    # Construire le dictionnaire des limites par modèle depuis les settings
    model_limits = {
        "claude-opus-4-5-20251101": settings.model_opus_limit,
        "claude-sonnet-4-5-20250929": settings.model_sonnet_limit,
        "claude-haiku-4-5-20251001": settings.model_haiku_limit,
    }

    for model_name, data in model_costs.items():
        used = data["cost"]
        limit = model_limits.get(
            model_name,
            settings.get_weekly_limit()
            if period in ["daily", "weekly"]
            else settings.get_session_limit(),
        )
        percentage = (used / limit * 100) if limit > 0 else 0.0
        remaining = max(0.0, limit - used)

        models_usage.append(
            ModelUsage(
                model_name=model_name,
                used=round(used, 2),
                limit=limit,
                percentage=round(percentage, 2),
                remaining=round(remaining, 2),
                input_tokens=data["inputTokens"],
                output_tokens=data["outputTokens"],
            )
        )

        total_used += used
        total_limit += limit

    # Trier par pourcentage décroissant
    models_usage.sort(key=lambda x: x.percentage, reverse=True)

    total_percentage = (total_used / total_limit * 100) if total_limit > 0 else 0.0

    return ModelBreakdownResponse(
        models=models_usage,
        total_used=round(total_used, 2),
        total_limit=total_limit,
        total_percentage=round(total_percentage, 2),
        period=period,
        start_date=week_start.strftime("%Y-%m-%d") if week_start else None,
    )
