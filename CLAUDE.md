# GTM MiroFish Demo

Intercom-branded fork of MiroFish — a swarm intelligence engine for GTM operations simulation.

## Project Structure

- `backend/` — MiroFish Flask backend (forked, minimally patched)
  - `app/config.py` — Multi-LLM provider configuration (Claude/OpenAI/Gemini)
  - `app/api/gtm_scenarios.py` — GTM scenario template API
  - `gtm_scenarios/` — Pre-built GTM simulation scenario JSON files
  - `gtm_seed_data/` — Anonymized GTM data for agent persona generation
  - `auth/` — Optional OAuth middleware (Google/Okta)
- `frontend/` — Complete Vue 3 + Vite + Tailwind rebuild with Intercom branding
  - 7 views: Landing, Scenario Builder, Knowledge Graph, Simulation, Report, Chat, Settings
  - Intercom design tokens (#2068FF blue, #050505 navy)

## Quick Start

```bash
cp .env.example .env
# Edit .env with your LLM_API_KEY and ZEP_API_KEY
docker compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:5001
```

## Development

### Backend
```bash
cd backend && uv sync && uv run python run.py
```

### Frontend
```bash
cd frontend && npm install && npm run dev
```

## Key Decisions

- **Multi-LLM**: Set `LLM_PROVIDER=anthropic|openai|gemini` in .env — auto-configures base URL and model
- **Auth**: Set `AUTH_ENABLED=true` for production — enforces @intercom.io email via Google/Okta OAuth
- **Scenarios**: 4 pre-built GTM scenarios in `backend/gtm_scenarios/`
- **Branding**: Intercom design tokens in `frontend/tailwind.config.js` and `frontend/src/assets/brand-tokens.css`

## API Endpoints

### MiroFish Core (unchanged)
- `POST /api/graph/build` — Build knowledge graph from seed text
- `POST /api/simulation/start` — Start OASIS simulation
- `GET /api/simulation/status` — Check simulation progress
- `POST /api/report/generate` — Generate predictive report
- `POST /api/chat` — Chat with simulated world

### GTM Extensions (new)
- `GET /api/gtm/scenarios` — List GTM scenario templates
- `GET /api/gtm/scenarios/:id` — Get scenario with seed data
- `GET /api/gtm/seed-data/:type` — Get seed data by type
