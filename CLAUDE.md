# GTM MiroFish Demo

Intercom-branded fork of MiroFish — a swarm intelligence engine for GTM operations simulation.

## Project Structure

```
├── backend/                   # Flask backend (Python 3.11+)
│   ├── app/
│   │   ├── __init__.py        # App factory, CORS, blueprint registration
│   │   ├── config.py          # Multi-LLM provider config (Claude/OpenAI/Gemini)
│   │   ├── api/               # Flask Blueprints (route handlers)
│   │   │   ├── graph.py       # Knowledge graph endpoints
│   │   │   ├── simulation.py  # Simulation lifecycle & results
│   │   │   ├── report.py      # Report generation
│   │   │   ├── gtm_scenarios.py # GTM scenario templates
│   │   │   └── settings.py    # Connection testing, auth status
│   │   ├── services/          # Business logic layer (11 modules)
│   │   │   ├── graph_builder.py
│   │   │   ├── simulation_runner.py
│   │   │   ├── simulation_manager.py
│   │   │   ├── oasis_profile_generator.py
│   │   │   ├── report_agent.py
│   │   │   └── ...
│   │   ├── utils/
│   │   │   ├── llm_client.py  # All LLM calls go through here
│   │   │   ├── logger.py
│   │   │   ├── retry.py
│   │   │   └── file_parser.py
│   │   └── models/            # Data models (Project, Task)
│   ├── gtm_scenarios/         # Pre-built GTM scenario JSON files
│   ├── gtm_seed_data/         # Anonymized seed data for agents
│   ├── auth/                  # Optional OAuth middleware
│   ├── run.py                 # Server entrypoint
│   ├── Dockerfile
│   └── pyproject.toml         # Python deps (managed by uv)
├── frontend/                  # Vue 3 + Vite + Tailwind CSS v4
│   ├── src/
│   │   ├── main.js            # App bootstrap (Vue + Pinia + Router)
│   │   ├── api/
│   │   │   ├── client.js      # Axios instance (baseURL from VITE_API_URL)
│   │   │   ├── graph.js
│   │   │   ├── simulation.js
│   │   │   ├── report.js
│   │   │   ├── scenarios.js
│   │   │   └── chat.js
│   │   ├── composables/       # Reusable composition functions
│   │   │   ├── useToast.js
│   │   │   ├── useTheme.js
│   │   │   ├── useCountUp.js
│   │   │   ├── useDemoMode.js
│   │   │   ├── useIntercom.js
│   │   │   └── useSimulationPolling.js
│   │   ├── stores/            # Pinia stores (composition-style)
│   │   │   ├── simulation.js
│   │   │   ├── scenarios.js
│   │   │   ├── settings.js
│   │   │   ├── auth.js
│   │   │   └── toast.js
│   │   ├── views/             # Route-level components (lazy-loaded)
│   │   ├── components/
│   │   │   ├── common/        # Base UI (Button, Input, Card, Badge, Modal)
│   │   │   ├── layout/        # AppNav, AppLayout, AppFooter
│   │   │   ├── ui/            # LoadingSpinner, EmptyState, ErrorState
│   │   │   ├── simulation/    # GraphPanel, SimulationPanel, PhaseNav
│   │   │   ├── report/        # ReportCharts
│   │   │   ├── landing/       # HeroSwarm animation
│   │   │   └── demo/          # PresenterToolbar
│   │   ├── assets/
│   │   │   └── brand-tokens.css  # Intercom design tokens
│   │   └── router/index.js
│   ├── Dockerfile
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml         # Local dev (backend:5001, frontend:3000)
├── .env.example               # Environment template
└── CLAUDE.md                  # This file
```

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
cd frontend && pnpm install && pnpm dev
```

## Deployment

- **Railway**: Both services deployed to Railway project `gtm-mirofish-demo`
  - Backend: https://backend-production-e9d7.up.railway.app
  - Frontend: https://frontend-production-86ea.up.railway.app
- Each service has its own `Dockerfile` in its directory
- `docker-compose.yml` at root for local development

---

## Development Rules

### General
- Keep changes focused and minimal — one logical change per commit
- Delete unused code completely; no dead code
- Avoid over-engineering; only build what's needed now
- Every endpoint must work in demo/mock mode when no LLM key is configured
- Never hardcode API keys — use environment variables from `.env`

### Package Managers
- **Frontend**: `pnpm` (e.g., `pnpm install`, `pnpm add <pkg>`)
- **Backend**: `pip` (or `uv add` for pyproject.toml)

### Do NOT Modify
- `PRD.json`
- `.ralphy/progress.txt`, `.ralphy-worktrees/`, `.ralphy-sandboxes/`
- `*.lock`, `pnpm-lock.yaml`
- `node_modules/`, `.git/`, `.env`

---

## Frontend Conventions

### Framework & Style
- **Vue 3 Composition API** with `<script setup>` syntax — no Options API
- **Tailwind CSS v4** for styling via CSS utility classes (CSS-based config — no `tailwind.config.js`)
- **D3.js v7** for all data visualizations (`pnpm add d3`)
- **Intercom brand colors**:
  - Primary blue: `#2068FF`
  - Navy: `#050505`
  - Orange: `#ff5600`
  - Text: `#1a1a1a`
- Design tokens defined in `frontend/src/assets/brand-tokens.css` as CSS custom properties
- Dark mode support via `.dark` class selector

### Code Organization
- **Reuse composables** from `frontend/src/composables/` — check there before creating new ones
- **Reuse the API client** at `frontend/src/api/client.js` — axios instance with `VITE_API_URL` base
- **Add new API modules** alongside existing ones in `frontend/src/api/`
- **Follow Pinia store patterns** in `frontend/src/stores/` — use `defineStore()` with composition-style
- **Components go in** `frontend/src/components/` grouped by feature:
  - `common/` — reusable base UI elements
  - `layout/` — app shell components
  - `ui/` — feedback & state components
  - `simulation/`, `report/`, etc. — feature-specific
- **Views are lazy-loaded** in `frontend/src/router/index.js`
- **localStorage** is used for client-side session persistence (simulation run history)

### API Client Pattern
```js
// frontend/src/api/client.js exports a configured axios instance
import apiClient from './client'

// Use it in API modules:
export const fetchSomething = (id) => apiClient.get(`/api/something/${id}`)
```

---

## Backend Conventions

### Framework & Patterns
- **Flask** with Blueprints for API route organization
- **Service layer** in `backend/app/services/` for business logic
- **All LLM calls** go through `backend/app/utils/llm_client.py` — never call LLM APIs directly
- Must support all three LLM providers: **Anthropic, OpenAI, Gemini**

### Code Organization
- **New route handlers** → `backend/app/api/` as Flask Blueprints
- **New business logic** → `backend/app/services/`
- **New utilities** → `backend/app/utils/`
- **New routes follow pattern**: `@bp.route('/api/v1/...')`
- Register new blueprints in `backend/app/__init__.py`

### Route Pattern (existing)
```python
# Existing routes use /api/<feature>/...
# Example from gtm_scenarios.py:
bp = Blueprint('gtm', __name__)

@bp.route('/api/gtm/scenarios')
def list_scenarios():
    ...
```

### Error Response Convention
```python
# Success:
return jsonify({"success": True, "data": result})

# Error:
return jsonify({"success": False, "error": "message"}), 400
```

### Multi-LLM Configuration
Set `LLM_PROVIDER` in `.env` to switch providers:
- `anthropic` → Claude (default)
- `openai` → GPT models
- `gemini` → Google Gemini

`config.py` auto-resolves `base_url` and `model_name` from the provider. Override with `LLM_BASE_URL` and `LLM_MODEL_NAME` if needed.

---

## Key Architecture Decisions

- **Multi-LLM**: OpenAI SDK used as the universal client — Anthropic and Gemini work via OpenAI-compatible base URLs
- **Knowledge Graph**: Zep Cloud stores the graph memory; entities read via `zep_entity_reader.py`
- **Simulation**: OASIS framework (built on CAMEL AI) runs agent simulations in a subprocess via `simulation_runner.py`
- **Auth**: Optional OAuth (Google/Okta) gated by `AUTH_ENABLED=true`; enforces `@intercom.io` domain
- **Scenarios**: 4 pre-built GTM scenarios in `backend/gtm_scenarios/` with seed data in `backend/gtm_seed_data/`
- **Branding**: Intercom design tokens in `frontend/src/assets/brand-tokens.css` (Tailwind CSS v4 — no tailwind.config.js)
- **Dockerfiles**: Per-service Dockerfiles in `backend/` and `frontend/` (used by both Railway and docker-compose)
- **Demo mode**: System works without LLM keys — endpoints return mock/demo data when no key is configured

## API Endpoints

### MiroFish Core
- `POST /api/graph/build` — Build knowledge graph from seed text
- `GET /api/graph/project/<id>` — Get project details
- `GET /api/graph/project/list` — List all projects
- `POST /api/simulation/start` — Start OASIS simulation
- `GET /api/simulation/<id>/run-status` — Check simulation progress
- `POST /api/report/generate` — Generate predictive report
- `POST /api/report/chat` — Chat with simulated world

### GTM Extensions
- `GET /api/gtm/scenarios` — List GTM scenario templates
- `GET /api/gtm/scenarios/:id` — Get scenario with seed data
- `GET /api/gtm/scenarios/:id/seed-text` — Get scenario seed text
- `GET /api/gtm/seed-data/:type` — Get seed data by type

### Utility
- `GET /health` — Health check
- `GET /api/settings/test-connection` — Test LLM/Zep connectivity
