# Architecture Documentation

GTM MiroFish Demo — a swarm intelligence engine for GTM operations simulation, forked from MiroFish and branded for Intercom.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                         │
│  Vite 8 · Tailwind CSS 4 · D3.js v7 · Pinia · Vue Router      │
│  Port 3000                                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ /api/* (Vite proxy in dev,
                             │        VITE_API_URL in prod)
┌────────────────────────────▼────────────────────────────────────┐
│                       Backend (Flask 3.0)                        │
│  Blueprints · LLM Client · Task Manager · Simulation Engine     │
│  Port 5001                                                      │
├──────────┬──────────────┬───────────────┬───────────────────────┤
│  Zep     │  LLM APIs    │  OASIS/CAMEL  │  File System          │
│  Cloud   │  (Anthropic  │  (subprocess) │  (uploads/, logs/,    │
│  (graph  │   OpenAI     │               │   gtm_scenarios/,     │
│  memory) │   Gemini)    │               │   gtm_seed_data/)     │
└──────────┴──────────────┴───────────────┴───────────────────────┘
```

**Two-service architecture** deployed as independent containers:
- **Frontend** — Vue 3 SPA served by `serve` in production, Vite dev server locally
- **Backend** — Flask application with async task processing and OASIS subprocess management

## Backend Architecture

### Entry Points

| File | Purpose |
|------|---------|
| `backend/run.py` | Production entry — validates config, calls `create_app()`, runs Flask |
| `backend/demo_app.py` | Lightweight demo entry (86 KB) — self-contained mock backend for presentations |

### App Factory (`app/__init__.py`)

Creates the Flask app with:
1. Config loading from `Config` class
2. Logger initialization (rotating file + console)
3. Blueprint registration (5 blueprints)
4. CORS for all `/api/*` routes
5. Request/response logging middleware
6. Simulation process cleanup on shutdown

### Blueprints

```
/api/graph/*        → app/api/graph.py           Knowledge graph CRUD + async build
/api/simulation/*   → app/api/simulation.py       Entity extraction, profiles, OASIS orchestration
/api/report/*       → app/api/report.py           Report generation via ReACT agent
/api/gtm/*          → app/api/gtm_scenarios.py    Pre-built scenario templates + unified simulate
/api/settings/*     → app/api/settings.py         LLM/Zep connection testing, auth status
```

### Services Layer (`app/services/`)

Core business logic, kept separate from route handlers:

| Service | Responsibility |
|---------|---------------|
| `graph_builder.py` | Uploads text chunks to Zep, polls until graph is built |
| `ontology_generator.py` | Uses LLM to derive entity/edge types from seed text |
| `simulation_manager.py` | Orchestrates entity extraction → profile gen → config gen → OASIS start |
| `simulation_runner.py` | Spawns OASIS subprocess, monitors state, collects action logs via IPC |
| `simulation_config_generator.py` | LLM-generated simulation parameters (timing, agent activity, events) |
| `oasis_profile_generator.py` | Converts Zep graph entities into OASIS agent profiles |
| `simulation_ipc.py` | File-based IPC with OASIS subprocess (commands/ and responses/ dirs) |
| `report_agent.py` | ReACT agent that queries Zep graph with tools, writes multi-section report |
| `zep_tools.py` | Search/retrieval tools for the report agent (InsightForge, PanoramaSearch, etc.) |
| `zep_entity_reader.py` | Paginated entity fetching from Zep graph with filtering |
| `zep_graph_memory_updater.py` | Writes simulation results back to Zep graph |
| `text_processor.py` | Text chunking, preprocessing, stats |

### Models (`app/models/`)

In-memory dataclass models with singleton managers:

- **Project** — tracks graph build lifecycle: `CREATED → ONTOLOGY_GENERATED → GRAPH_BUILDING → GRAPH_COMPLETED`
- **Task** — async task tracking: `PENDING → PROCESSING → COMPLETED/FAILED` with 0-100% progress

Both use file-based persistence in `uploads/` — no SQL database.

### LLM Client (`app/utils/llm_client.py`)

Unified LLM abstraction using the OpenAI SDK with base URL routing:

```
LLM_PROVIDER=anthropic  →  base_url: api.anthropic.com/v1/      model: claude-sonnet-4-20250514
LLM_PROVIDER=openai     →  base_url: api.openai.com/v1/          model: gpt-4o
LLM_PROVIDER=gemini     →  base_url: generativelanguage.../v1beta/openai/  model: gemini-2.5-flash
```

Key methods:
- `chat(messages, temperature, max_tokens)` → text response
- `chat_json(messages)` → parsed JSON (strips markdown fences, validates)

Provider config resolved in `app/config.py` via `get_llm_config()`.

### Configuration (`app/config.py`)

Environment-driven via `python-dotenv`:

| Category | Variables |
|----------|-----------|
| **LLM** | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME` |
| **Zep** | `ZEP_API_KEY` |
| **Auth** | `AUTH_ENABLED`, `AUTH_PROVIDER`, `AUTH_ALLOWED_DOMAIN`, OAuth client IDs/secrets |
| **Server** | `PORT`, `FLASK_DEBUG`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `LOG_FILE` |
| **OASIS** | `OASIS_DEFAULT_MAX_ROUNDS`, `OASIS_SIMULATION_DATA_DIR` |
| **Report** | `REPORT_AGENT_MAX_TOOL_CALLS`, `REPORT_AGENT_TEMPERATURE` |

### Auth (`auth/oauth_middleware.py`)

Optional decorator-based auth:
- `require_auth` — checks `AUTH_ENABLED`, validates `session['user']`
- `validate_email_domain` — enforces `@intercom.io` emails
- Supports Google OAuth and Okta SSO (skeleton)

## Frontend Architecture

### App Structure

```
src/
├── main.js                    App bootstrap (Vue + Pinia + Router)
├── App.vue                    Root: AppLayout wrapper + router-view with transitions
├── style.css                  Global styles + Tailwind v4 + brand token import
├── router/index.js            11 routes, lazy-loaded views
├── api/                       Axios-based API client modules
├── stores/                    Pinia state management
├── composables/               Reusable reactive logic
├── components/                UI component library
├── views/                     Page-level components
└── assets/brand-tokens.css    Intercom design tokens
```

### Views

| Route | View | Purpose |
|-------|------|---------|
| `/` | `LandingView` | Hero with D3 swarm animation + scenario cards |
| `/scenarios/:id` | `ScenarioBuilderView` | Seed text, persona, industry config form |
| `/workspace/:taskId` | `SimulationWorkspaceView` | Two-tab workspace: graph viz + simulation metrics |
| `/report/:taskId` | `ReportView` | Multi-chapter markdown report with D3 charts |
| `/chat/:taskId` | `ChatView` | Chat with report agent (tool call visualization) |
| `/simulations` | `SimulationsView` | Session history dashboard (localStorage-backed) |
| `/settings` | `SettingsView` | LLM provider, API keys, theme, defaults |
| `/workspace/:taskId/agent/:agentId` | `AgentProfileView` | Individual agent persona details |

### Pinia Stores

| Store | Key State |
|-------|-----------|
| `useSimulationStore` | `status`, `simulationId`, `graphTaskId`, `progress`, `metrics`, `sessionRuns` |
| `useScenariosStore` | `scenarios[]`, `detailCache{}`, lazy-fetched from `/api/gtm/scenarios` |
| `useSettingsStore` | `provider`, `apiKey`, `zepKey`, `connectionStatus` — auto-persisted to localStorage |
| `useAuthStore` | `user`, `token`, `isAuthenticated` |
| `useToastStore` | Toast notification stack |

### Composables

| Composable | Purpose |
|------------|---------|
| `useSimulationPolling` | Orchestrates graph + simulation polling at 2-5s intervals; provides reactive `graphStatus`, `runStatus`, `recentActions`, `timeline`; falls back to demo mode on network error |
| `useTheme` | Dark/light mode with system detection, route-specific defaults (dark landing, light elsewhere), localStorage persistence |
| `useToast` | Global toast notification stack with auto-dismiss |
| `useCountUp` | requestAnimationFrame number animation for metrics display |
| `useIntercom` | Optional Intercom widget integration (deferred script load) |
| `useDemoMode` | Feature flag from `VITE_DEMO_MODE` env var |

### API Client (`api/client.js`)

Axios instance with:
- Base URL from `VITE_API_URL` (default `/api`)
- Response interceptor normalizing success/error shapes
- Modular exports: `graphApi`, `simulationApi`, `reportApi`, `chatApi`

### Component Library

```
components/
├── layout/      AppLayout, AppNav, AppFooter
├── common/      AppButton, AppInput, AppCard, AppBadge, AppModal, StatusIndicator
├── ui/          ToastContainer, LoadingSpinner, ShimmerCard, EmptyState, ErrorState, ConfirmDialog
├── simulation/  GraphPanel (D3 force graph), SimulationPanel, SentimentTimeline (D3 line/bar)
├── report/      ReportCharts (D3 bar charts per chapter)
├── landing/     HeroSwarm (D3 particle animation)
└── demo/        PresenterToolbar
```

### D3.js Visualizations

| Component | Chart Type | Data Source |
|-----------|-----------|-------------|
| `HeroSwarm` | Animated particle swarm | Procedural (decoration) |
| `GraphPanel` | Force-directed graph | `/api/graph/task/:id` → nodes/edges |
| `SentimentTimeline` | Line + stacked bar | Simulation actions (sentiment scored) |
| `ReportCharts` | Horizontal bar charts | Report section data per chapter |

### Design System

Intercom brand tokens defined in `assets/brand-tokens.css`:

| Token | Value | Usage |
|-------|-------|-------|
| Primary Blue | `#2068FF` | Buttons, links, active states |
| Navy | `#050505` | Dark backgrounds, header |
| Fin Orange | `#ff5600` | Persona accents, highlights |
| Accent Purple | `#AA00FF` | Relationship indicators |

Dark mode: `.dark` class on `<html>` triggers CSS variable overrides (background `#0a0a1a`, surface `#1a1a2e`).

## Data Flow

### End-to-End Simulation Pipeline

```
1. Scenario Selection          GET /api/gtm/scenarios
   User picks a pre-built        ↓
   scenario or writes seed    ScenarioBuilderView form
   text                          ↓

2. Graph Build                POST /api/gtm/simulate
   Seed text → ontology          ↓ returns task_id
   → Zep graph build          Poll GET /api/graph/task/:id (2s interval)
   (async, ~30-120s)             ↓ graph_id on completion

3. Entity Extraction          GET /api/simulation/entities/:graph_id
   Pull filtered entities        ↓
   from Zep graph             SimulationWorkspaceView → GraphPanel (D3)

4. Simulation Prepare         POST /api/simulation/prepare/:graph_id
   Generate OASIS agent          ↓
   profiles + config          LLM generates personas, timing, events

5. Simulation Start           POST /api/simulation/start
   Spawn OASIS subprocess        ↓ returns simulation_id
   (Twitter/Reddit agents)    Poll GET /api/simulation/status/:id (3s interval)
                                 ↓

6. Simulation Running         Actions collected via file-based IPC
   Agents post, like,            ↓
   reply, follow              SimulationPanel + SentimentTimeline (D3)

7. Simulation Complete        Status → COMPLETED
                                 ↓

8. Report Generation          POST /api/report/generate
   ReACT agent queries Zep       ↓ returns task_id + report_id
   graph with search tools    Poll GET /api/report/generate/status/:id (5s interval)
                                 ↓

9. Report Display             GET /api/report/:id
   Multi-chapter markdown        ↓
   + D3 charts                ReportView → ReportCharts (D3)

10. Interactive Chat          POST /api/report/chat
    Follow-up questions          ↓
    answered by report agent  ChatView (streaming tool call visualization)
```

### State Management Flow

```
API responses
    ↓
Pinia stores (simulation, scenarios, settings)
    ↓
Composables (useSimulationPolling fetches + updates stores)
    ↓
provide/inject (SimulationWorkspaceView provides polling context)
    ↓
Components (GraphPanel, SimulationPanel consume via inject)
```

## Simulation Engine

### OASIS Integration

The simulation uses [OASIS](https://github.com/camel-ai/oasis) (built on CAMEL-AI) to run multi-agent social media simulations:

1. **Profile Generation** — Zep graph entities → LLM-enriched personas → OASIS agent profiles (Twitter/Reddit format)
2. **Config Generation** — LLM analyzes scenario + entities → timing, activity levels, events, platform-specific action probabilities
3. **Subprocess Execution** — `SimulationRunner` spawns OASIS as a subprocess
4. **IPC** — File-based command/response protocol (`commands/` and `responses/` directories) for real-time action collection and agent interviews

### Agent Actions

Each round produces `AgentAction` records:

```
round_num, timestamp, platform (twitter/reddit),
agent_id, agent_name, action_type, action_args, result, success
```

Action types: `CREATE_POST`, `LIKE_POST`, `REPOST`, `FOLLOW`, `DO_NOTHING`, `QUOTE_POST` (Twitter); `CREATE_POST`, `CREATE_COMMENT`, `UPVOTE`, `DOWNVOTE` (Reddit).

### Report Agent (ReACT Pattern)

Multi-round reasoning agent with Zep search tools:

| Tool | Strategy |
|------|----------|
| `InsightForge` | Deep hybrid search (text + graph), multi-dimensional analysis |
| `PanoramaSearch` | Breadth-first search including expired content |
| `QuickSearch` | Simple keyword/entity lookup |
| `Interview` | Direct agent interaction during simulation |
| `NodeInfo` | Single node retrieval by UUID |

Workflow: Plan outline → For each section: Think → Reflect → Write → Compile final report.

## Deployment

### Docker

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend/Dockerfile
    ports: ["${BACKEND_PORT:-5001}:5001"]
    volumes: [sim_data:/app/uploads]
    healthcheck: GET /api/health (5s interval, 3 retries)

  frontend:
    build: ./frontend/Dockerfile
    args: [VITE_API_URL=http://backend:5001/api]
    ports: ["${FRONTEND_PORT:-3000}:3000"]
    depends_on: backend (healthy)
```

- **Backend Dockerfile** — `python:3.11-slim`, installs Flask + LLM SDKs, runs `demo_app.py`
- **Frontend Dockerfile** — Multi-stage: `node:20-slim` builds with pnpm, runtime serves `dist/` with `serve -s` (SPA mode)
- Named volume `sim_data` persists uploads across restarts

### Railway

Both services deployed to Railway project `gtm-mirofish-demo`:
- Backend: `https://backend-production-e9d7.up.railway.app`
- Frontend: `https://frontend-production-86ea.up.railway.app`
- No explicit Railway config files — auto-detected from Dockerfiles

### Demo Mode

When `VITE_DEMO_MODE=true` or no LLM key is configured:
- Frontend generates synthetic agent actions and timeline data
- Backend keyword-matches instead of calling LLM APIs
- All visualizations work with deterministic fallback data

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **OpenAI SDK for all providers** | Single client wraps Anthropic/OpenAI/Gemini via base URL routing — no provider-specific code in business logic |
| **File-based IPC** | OASIS runs as a subprocess; filesystem commands/responses avoid socket complexity and survive process restarts |
| **In-memory state + file persistence** | No database dependency — `TaskManager` and `ProjectManager` use dicts + JSON files in `uploads/` |
| **provide/inject for polling** | `SimulationWorkspaceView` provides polling composable to child components, avoiding prop drilling through tab structure |
| **localStorage for session history** | Simulation runs persist across browser sessions without backend state; max 50 runs with auto-cleanup |
| **Lazy-loaded routes** | All views except Landing are lazy-loaded for fast initial page load |
| **Demo mode fallback** | Network errors trigger `isDemoFallback` in polling composable, ensuring the app always has something to show |
| **Zep Cloud for graph memory** | Temporal knowledge graph with built-in RAG — entities and relationships extracted from seed text without custom graph DB |

## Dependencies

### Backend
| Package | Purpose |
|---------|---------|
| `flask`, `flask-cors` | Web framework + CORS |
| `openai` | LLM API client (all providers) |
| `anthropic` | Optional direct Anthropic client |
| `zep-cloud` | Knowledge graph + RAG |
| `camel-ai`, `camel-oasis` | Multi-agent simulation framework |
| `PyMuPDF` | PDF text extraction |
| `python-dotenv` | Environment variable loading |
| `pydantic` | Data validation |

### Frontend
| Package | Purpose |
|---------|---------|
| `vue` (3.5), `vue-router`, `pinia` | UI framework + routing + state |
| `d3` (7.9) | Data visualizations |
| `axios` | HTTP client |
| `marked` | Markdown rendering |
| `@tailwindcss/vite` | Tailwind CSS v4 build plugin |
