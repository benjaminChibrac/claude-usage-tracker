# Claude Usage API

API REST légère exposant les métriques d'utilisation Claude Code en temps réel.

## Démarrage rapide

```bash
# Installation
cd /srv/dev-disk-by-uuid-f89e7c5f-bec7-477f-b5ca-85ffc4645dd1/RPI_DATA/claude-usage
pip install -e .

# Configuration
cp .env.example .env
# Éditer .env selon vos besoins

# Démarrage
uvicorn claude_usage_api.main:app --reload
```

## Endpoints

- `GET /health` - Health check
- `GET /usage` - État complet de consommation
- `GET /usage/session` - Session uniquement
- `GET /usage/weekly` - Hebdomadaire uniquement
- `GET /config` - Configuration actuelle
- `POST /cache/invalidate` - Forcer le rafraîchissement du cache

## Configuration

Variables d'environnement (.env):
- `CLAUDE_PLAN` : Plan Claude (pro, max_5x, max_20x)
- `SESSION_LIMIT_USD` : Limite de session en USD (optionnel)
- `WEEKLY_LIMIT_USD` : Limite hebdomadaire en USD (optionnel)
- `CACHE_TTL_SECONDS` : TTL du cache en secondes (défaut: 60)
- `API_KEY` : Clé API pour authentification (optionnel)
- `HOST` / `PORT` : Configuration serveur

## Prérequis

- `ccusage` doit être installé : `npm install -g ccusage`
