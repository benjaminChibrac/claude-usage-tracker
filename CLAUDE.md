# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Claude Usage API** is a FastAPI-based REST service that exposes Claude Code usage metrics by wrapping the `ccusage` CLI tool. It provides real-time tracking of session and weekly consumption with budget limit monitoring across different Claude plans (Pro, Max 5x, Max 20x).

**Key Technologies:**
- Python 3.9+ with FastAPI + Uvicorn
- External dependency: `ccusage` (Node.js CLI installed via npm)
- Pydantic for data validation and settings
- Docker multi-stage build (Node.js + Python)

## Development Commands

### Local Development

```bash
# Install in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run the server locally (development mode with hot reload)
uvicorn claude_usage_api.main:app --reload --host 0.0.0.0 --port 8383

# Run without reload
python -m uvicorn claude_usage_api.main:app --host 0.0.0.0 --port 8383
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run specific test class
pytest tests/test_api.py::TestHealthEndpoint

# Run with verbose output
pytest -v

# Run with coverage (if configured)
pytest --cov=claude_usage_api
```

### Docker

```bash
# Build the image
docker build -t claude-usage-api .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Prerequisites

The `ccusage` CLI must be available:
```bash
npm install -g ccusage
```

## Architecture

### Layered Structure

1. **API Layer** (`main.py`): FastAPI app with 8 REST endpoints, optional API key auth, and lifecycle management
2. **Business Logic** (`usage_service.py`): Wraps `ccusage` CLI via `npx`, parses JSON output, calculates projections
3. **Data Models** (`models.py`): Pydantic schemas for all request/response formats
4. **Configuration** (`config.py`): Settings management with plan-based presets and custom overrides
5. **Caching** (`cache.py`): Simple TTL-based in-memory cache to reduce `ccusage` calls

### Key Design Patterns

**ccusage Integration:**
- All data originates from the external `ccusage` CLI (Node.js tool)
- Commands executed: `blocks --json`, `daily --json`
- Async subprocess execution with 30s timeout
- Graceful fallbacks when ccusage fails (returns empty/inactive data)

**Billing Logic:**
- Session limit: 5-hour window with cost projection based on burn rate
- Weekly limit: Custom reset day/hour (not hardcoded to Sunday), aggregates daily costs
- **Effective calibration**: Uses effective limits instead of plan limits for percentage display accuracy:
  - `session_limit_effective` (4.16 USD) vs plan limit (3.5 USD for Pro)
  - `weekly_limit_effective` (42.65 USD) vs plan limit (35 USD for Pro)
  - These calibrated values match the percentages displayed on claude.ai
- Active session cost added to weekly total only if today's data isn't in `daily` yet

**Model Breakdown:**
- Per-model limits defined in `config.py` for Opus, Sonnet, Haiku
- Tracks input/output tokens separately
- Calculates percentage against each model's specific limit

### Critical Files

- `src/claude_usage_api/usage_service.py`: Core business logic, ccusage parsing, projection calculations
- `src/claude_usage_api/config.py`: Plan presets, model limits, calibration factor
- `src/claude_usage_api/main.py`: FastAPI routes and API key authentication
- `Dockerfile`: Multi-stage build combining Node.js (ccusage) + Python runtime

## Configuration

Create `.env` from `.env.example` and configure:

**Essential:**
- `CLAUDE_PLAN`: One of `pro`, `max_5x`, `max_20x` (determines default limits)
- `HOST_CLAUDE_DIR`: Path to Claude config directory (must be mounted in Docker)

**Optional Overrides:**
- `SESSION_LIMIT_USD` / `WEEKLY_LIMIT_USD`: Override plan defaults
- `CACHE_TTL_SECONDS`: Cache duration (default: 60)
- `WEEKLY_RESET_DAY`: 0=Monday, 6=Sunday (default: 0)
- `WEEKLY_RESET_HOUR`: Hour of day for weekly reset (default: 0)
- `API_KEY`: Enable authentication via `X-API-Key` header

## API Endpoints

- `GET /health` - Health check with ccusage availability
- `GET /usage` - Full usage (session + weekly), cached response
- `GET /usage/session` - Active session metrics only
- `GET /usage/weekly` - Weekly aggregate only
- `GET /usage/by-model?period=weekly` - Per-model breakdown (supports: daily, weekly, session)
- `GET /config` - Current configuration
- `POST /cache/invalidate` - Force cache refresh

All endpoints except `/health` require `X-API-Key` header if `API_KEY` is configured.

## Common Pitfalls

1. **Docker volume mapping**: Ensure `HOST_CLAUDE_DIR` correctly points to the Claude config directory on the host (`~/.claude` on Linux, `~/Library/Application Support/Claude` on macOS)

2. **ccusage availability**: The service degrades gracefully but requires `ccusage` to be installed. Verify with `npx ccusage --version`

3. **Async execution**: All ccusage commands use async subprocess to avoid blocking the event loop

4. **Weekly calculations**: The API supports custom reset days (not just Sunday). Make sure `WEEKLY_RESET_DAY` matches your Claude billing cycle

5. **Calibration factors**: Both `session_limit_effective` and `weekly_limit_effective` in `config.py` are intentionally different from plan limits to match claude.ai percentage display:
   - Session: 4.16 USD (vs 3.5 USD official) - ensures 1.29 USD shows as ~31%
   - Weekly: 42.65 USD (vs 35 USD official) - calibrated for accurate weekly percentage
   - The official limits are still returned in API responses, only percentage calculations use effective limits
