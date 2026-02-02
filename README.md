# Claude Usage Tracker - Monorepo

This repository contains:
- **api/** - FastAPI service for Claude usage metrics
- **custom_components/** - Home Assistant custom integration (HACS-compatible)

## Quick Start

### API

See [api/README.md](api/README.md) for detailed API documentation.

```bash
cd api
pip install -e .
uvicorn claude_usage_api.main:app --reload --port 8383
```

### Home Assistant Integration

See [custom_components/claude_usage/README.md](custom_components/claude_usage/README.md) for installation instructions.

## Docker Deployment

From the repository root:

```bash
# Configure environment
cp api/.env.example api/.env
# Edit api/.env according to your needs

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Prerequisites

- Python 3.9+
- `ccusage` CLI tool: `npm install -g ccusage`
- Docker & Docker Compose (for containerized deployment)
