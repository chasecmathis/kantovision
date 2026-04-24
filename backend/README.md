# KantoVision API

FastAPI backend powering KantoVision — handles Pokémon data, team persistence, profiles, and real-time WebSocket battles.

## Setup

```bash
cp .env.example .env   # fill in Supabase credentials
uv sync
uv run uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service role key — grants full DB access, never expose publicly |
| `SUPABASE_JWT_SECRET` | Used to verify Supabase JWTs on every authenticated request |
| `FRONTEND_URL` | Allowed CORS origin (e.g. `http://localhost:3000` or your Vercel URL) |
| `ALLOWED_ORIGINS` | Comma-separated list for CORS (e.g. `https://kantovision.vercel.app`) |
| `JSON_LOGS` | Set `true` in production for structured logs (Railway log viewer) |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `MOVE_TIMEOUT_SECONDS` | Seconds before a battle turn auto-resolves (default: 60) |
| `WS_GRACE_PERIOD_SECONDS` | Seconds to hold a battle slot after disconnect (default: 30) |
| `MAX_TEAMS_PER_USER` | Maximum saved teams per user (default: 10) |
| `WS_RATE_LIMIT_PER_SECOND` | WebSocket messages per second per connection (default: 10) |

## Running Tests

```bash
uv run pytest
```

The test suite uses stub env vars from `tests/conftest.py` — no real Supabase credentials needed.

```bash
# Lint
uv run ruff check app/
```

## Data Ingest

The Pokémon data (moves, species, stats, etc.) is loaded from PokéAPI via the ingest script. Run this once against a fresh Supabase database:

```bash
uv run python scripts/ingest_pokemon.py
```

This populates the `pokemon`, `moves`, `abilities`, `items`, and `evolution_chains` tables.

## Deployment (Railway)

The `railway.toml` and `Dockerfile` are production-ready:
1. Create a Railway project and link your GitHub repo
2. Set **Root Directory** to `backend` in the service settings
3. Add all variables from `.env.example` in the Railway Variables tab
4. Set `JSON_LOGS=true` and `ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app`
5. Deploy — Railway builds from the `Dockerfile`

Health check is at `GET /health`.
