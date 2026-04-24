# KantoVision

A full-stack Pokémon companion app featuring a searchable Pokédex, a competitive team builder, and real-time 1v1 battles.

## Features

- **Pokédex** — Browse all 9 generations with search, type filtering, stat breakdowns, type effectiveness charts, and evolution chains
- **Team Builder** — Build 6-Pokémon teams with full EV/IV/move/item/nature/ability customization; save and load teams with an account
- **Battle Simulator** — Real-time 1v1 battles via WebSocket with matchmaking, turn timer, battle log, and reconnect handling
- **AI Scanner** *(demo)* — Upload a Pokémon image for classification (mock inference, real ML coming soon)

## Architecture

```
Vercel (Next.js 14)  →  Railway (FastAPI)  →  Supabase (auth + DB)
```

- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, TanStack Query v5, Supabase auth
- **Backend**: FastAPI, WebSocket battles, Supabase service role for DB access, `uv` for dependency management
- **Database**: Supabase (Postgres) — teams, profiles, battle history

## Quickstart

### Backend

```bash
cd backend
cp .env.example .env          # fill in your Supabase credentials
uv sync
uv run uvicorn app.main:app --reload
# API is at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
cp .env.example .env.local    # fill in your Supabase + API URLs
npm install
npm run dev
# App is at http://localhost:3000
```

## Environment Variables

See [`backend/.env.example`](backend/.env.example) and [`frontend/.env.example`](frontend/.env.example) for the full list.

**Required**:
| Variable | Where | Description |
|----------|-------|-------------|
| `SUPABASE_URL` | backend | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | backend | Service role key (never expose client-side) |
| `SUPABASE_JWT_SECRET` | backend | JWT secret for token verification |
| `NEXT_PUBLIC_SUPABASE_URL` | frontend | Same Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | Anon/public key (safe to expose) |
| `NEXT_PUBLIC_API_URL` | frontend | Backend HTTPS URL in production |
| `NEXT_PUBLIC_API_WS_URL` | frontend | Backend WSS URL in production |

## Deployment

- **Frontend** → [Vercel](https://vercel.com): zero-config for Next.js, set env vars in dashboard
- **Backend** → [Railway](https://railway.app): `Dockerfile` + `railway.toml` already configured; set Root Directory to `backend`, add env vars from `.env.example`

## Running Tests

```bash
cd backend
uv run pytest
```
