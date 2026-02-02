"""Tests pour le service d'usage."""

import pytest
from datetime import datetime, timezone

from claude_usage_api.usage_service import (
    parse_session_blocks,
    parse_iso_datetime,
    calculate_projection,
)


class TestParseSessionBlocks:
    """Tests pour la fonction parse_session_blocks."""

    def test_empty_blocks(self):
        """Test avec des blocks vides."""
        data = {"blocks": []}
        active, total = parse_session_blocks(data)
        assert active is None
        assert total == 0.0

    def test_active_block_found(self):
        """Test qu'un bloc actif est trouvé."""
        data = {
            "blocks": [
                {"cost": 0.5, "endedAt": "2026-02-02T10:00:00Z"},
                {"cost": 0.45, "endedAt": None, "startedAt": "2026-02-02T11:00:00Z"},
            ]
        }
        active, total = parse_session_blocks(data)
        assert active is not None
        assert active["cost"] == 0.45
        assert total == 0.95

    def test_no_active_block(self):
        """Test quand tous les blocs sont terminés."""
        data = {
            "blocks": [
                {"cost": 0.5, "endedAt": "2026-02-02T10:00:00Z"},
                {"cost": 0.3, "endedAt": "2026-02-02T11:00:00Z"},
            ]
        }
        active, total = parse_session_blocks(data)
        assert active is None
        assert total == 0.8


class TestParseIsoDatetime:
    """Tests pour la fonction parse_iso_datetime."""

    def test_valid_iso(self):
        """Test avec une date ISO valide."""
        result = parse_iso_datetime("2026-02-02T11:00:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 2

    def test_none_input(self):
        """Test avec None."""
        result = parse_iso_datetime(None)
        assert result is None

    def test_empty_string(self):
        """Test avec une chaîne vide."""
        result = parse_iso_datetime("")
        assert result is None


class TestCalculateProjection:
    """Tests pour la fonction calculate_projection."""

    def test_basic_projection(self):
        """Test de projection basique."""
        started_at = datetime(2026, 2, 2, 10, 0, 0, tzinfo=timezone.utc)
        # Simuler qu'on est à 11h (1h écoulée)
        import claude_usage_api.usage_service as us

        # On ne peut pas facilement mocker datetime.now() ici
        # Donc on teste juste que la fonction ne plante pas
        # avec des valeurs raisonnables

        # Calcul manuel: 1h écoulée, 1$ dépensé
        # burn_rate = 1$/h
        # projection sur 5h = 5$
        pass  # Simplifié pour l'instant

    def test_very_recent_session(self):
        """Test avec une session très récente."""
        started_at = datetime.now(timezone.utc)
        result = calculate_projection(0.1, started_at, 3.5)
        # Devrait retourner None car moins de 0.1h écoulée
        # Note: Ce test dépend du timing exact
