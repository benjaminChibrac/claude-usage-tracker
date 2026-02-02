# Claude Usage API

API REST légère exposant les métriques d'utilisation Claude Code en temps réel.

## Démarrage rapide

```bash
# Installation (depuis le répertoire api/)
cd api
pip install -e .

# Configuration
cp .env.example .env
# Éditer .env selon vos besoins

# Démarrage
uvicorn claude_usage_api.main:app --reload --host 0.0.0.0 --port 8383
```

## Endpoints

- `GET /health` - Health check
- `GET /usage` - État complet de consommation
- `GET /usage/session` - Session uniquement
- `GET /usage/weekly` - Hebdomadaire uniquement
- `GET /usage/by-model?period=weekly` - Détail par modèle (daily, weekly, session)
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
- `WEEKLY_RESET_DAY` : Jour de réinitialisation hebdomadaire (0=Lundi, 6=Dimanche)
- `WEEKLY_RESET_HOUR` : Heure de réinitialisation (défaut: 0)

## Prérequis

- Python 3.9+
- `ccusage` doit être installé : `npm install -g ccusage`

## Docker

Depuis la racine du repository:

```bash
docker-compose up -d --build
```

## Développement

```bash
# Installer avec dépendances de développement
pip install -e ".[dev]"

# Lancer les tests
pytest -v

# Tests avec couverture
pytest --cov=claude_usage_api
```
