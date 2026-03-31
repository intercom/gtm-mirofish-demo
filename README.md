# MiroFish for GTM — Swarm Intelligence Demo

> Predict campaign outcomes before they happen. Simulate how prospects react to your outbound, signals, and pricing changes.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node 18+](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)

An Intercom-branded fork of [MiroFish](https://github.com/666ghj/MiroFish) — an open-source swarm intelligence engine (40K+ GitHub stars) — customized for Intercom's GTM Systems team. Pre-test automated outbound campaigns, validate sales signals, simulate pricing changes, and optimize personalization before they hit real prospects.

---

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Screenshots](#screenshots)
- [Features](#features)
- [Quick Start](#quick-start)
- [Running Your First Simulation](#running-your-first-simulation)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [GTM Scenarios](#gtm-scenarios)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

---

## The Problem

Intercom's GTM operations face a fundamental challenge: **we can't predict how our outbound messaging, pricing changes, and campaign strategies will land before we execute them.**

| Challenge | Impact |
|-----------|--------|
| Data trust is critically low | Reps spend 5-30 minutes per account validating data |
| 56K incorrect website records | Enrichment accuracy only 25-32% |
| Signal adoption collapsed | 11% unactioned at launch to 76% now |
| No campaign staging environment | Every campaign is a production deployment |
| Churn prediction: 87% recall, 16% precision | Model predicts who, not how to prevent |

## The Solution

MiroFish creates **digital sandboxes** populated with AI agents that simulate real social behavior. Instead of asking "what happened last time?" it answers **"what would happen if we did this?"**

```
Your Scenario (email copy, signals, pricing)
    -> Knowledge Graph Construction (Zep GraphRAG)
        -> Agent Population (hundreds of AI personas)
            -> Social Simulation (Twitter + Reddit, 23 action types)
                -> Predictive Report (evidence-based analysis)
                    -> Interactive Chat (Q&A with simulated world)
```

---

## Screenshots

### Landing Page
Scenario cards with "How It Works" section and key stats.

![Landing Page](docs/screenshots/landing.png)

### Scenario Builder
Configure agent populations, industries, and simulation parameters before launching a run.

![Scenario Builder](docs/screenshots/scenario-builder.png)

### Simulation Workspace
Unified tabbed workspace with Knowledge Graph (D3.js force-directed graph with entity type coloring, zoom/pan, and click-to-inspect), live simulation progress, and network analysis.

![Workspace](docs/screenshots/workspace.png)

### Agent Profile
Individual agent persona detail with belief system, personality traits, relationship graph, and interview capability.

![Agent Profile](docs/screenshots/agent-profile.png)

### Report Explorer
Multi-chapter evidence-based predictive report with section navigation, chart visualizations, and export options.

![Report](docs/screenshots/report.png)

### Chat with Simulation
Conversational interface for querying the simulated world. Ask about simulation findings, persona engagement, messaging effectiveness, and recommended next steps.

![Chat](docs/screenshots/chat.png)

### Simulation History
Persistent simulation history with search, filter, and status tracking across all past runs.

![Simulations](docs/screenshots/simulations.png)

### Settings
Configure LLM provider (Claude, GPT-4o, or Gemini), theme preference, and API keys. In demo mode, API keys are not required.

![Settings](docs/screenshots/settings.png)

---

## Features

### Core Simulation
- **4 Pre-Built GTM Scenarios** — Outbound campaign pre-testing (hero), signal validation, pricing simulation, personalization optimization
- **Scenario Marketplace** — Browse, filter, and discover simulation templates with guided walkthroughs
- **Multi-LLM Support** — Claude (Anthropic), OpenAI (GPT-4o), Google Gemini — switchable in settings
- **Async Task System** — All long-running operations (graph build, simulation, report gen) return task IDs for progress polling
- **Report Agent** — AI-powered report generation with section-by-section streaming, tool-call logging, and report wizard for custom reports
- **Agent Interviews** — Chat with individual simulated agents or batch-interview entire populations

### Analytics & Intelligence
- **GTM Dashboard** — Executive KPI dashboard with revenue pipeline, deal velocity, health scorecards, and customizable widget grid
- **Dashboard Builder** — Drag-and-drop custom dashboard creation with 9 widget types (KPI cards, line/bar/donut charts, funnels, gauges, tables, text)
- **Analytics Suite** — Cohort analysis, segment performance, anomaly detection, and AI-powered insight generation
- **Simulation Comparison** — Side-by-side A/B scenario comparison with radar charts, timeline overlays, and statistical tables
- **Simulation Replay** — Step-through playback of completed simulations with timeline scrubbing

### Visualization
- **D3.js Chart Library** — 11 chart types: bar, line, donut, radar, sunburst, chord diagram, stream graph, parallel coordinates, bullet, calendar heatmap, and small multiples
- **Knowledge Graphs** — Force-directed graph visualization with entity type coloring, zoom/pan, click-to-inspect, and 3D rendering
- **Network Analysis** — Community detection, interaction graphs, and organizational chart views
- **Charts Gallery** — Interactive showcase of all available D3 visualization components

### Agent System
- **Agent Creation Wizard** — Multi-step wizard for building custom agent personas (basic info, expertise, personality traits, preview)
- **Belief System Tracker** — Monitor how agent beliefs evolve during simulation rounds
- **Agent Personality Dynamics** — Big Five personality model with trait evolution over time
- **Coalition Detection** — Identify emergent agent groups and alliances during simulations

### GTM Operations
- **CPQ Module** — Configure-Price-Quote with product catalog, discount analysis, and quote management
- **Revenue Pipeline** — Revenue tracking, deal management, and pipeline stage visualization
- **Campaign Management** — Campaign generation with ROI comparison, cost modeling, and attribution analysis
- **Salesforce Integration** — SFDC data sync with reconciliation and pipeline synchronization

### Platform
- **27 Interactive Views** — Full application with landing, scenarios, workspace, agents, analytics, dashboards, reports, comparison, replay, charts gallery, API docs, and more
- **60+ Composables** — Reusable Vue composition functions for animations, caching, keyboard shortcuts, offline mode, service workers, WebSocket, SSE, and more
- **Command Palette** — Keyboard-driven navigation (`Cmd+K`) with searchable actions
- **Intercom Branding** — Full Intercom design language with brand colors (#2068FF blue, #050505 navy, #ff5600 Fin orange), typography, and logo
- **Real GTM Seed Data** — Anonymized data from Intercom's actual GTM models (accounts, signals, templates, personas)
- **Optional Auth** — Google OAuth / Okta SSO with @intercom.io email enforcement (toggle via `.env`, disabled by default)
- **Docker Deployment** — Single `docker compose up` for local development
- **Interactive API Docs** — Built-in API documentation view at `/api-docs`

---

## Quick Start

### Prerequisites

- **Docker** (recommended) or:
  - Python 3.11+ (with [uv](https://docs.astral.sh/uv/) or plain venv + pip)
  - Node 18+ with [pnpm](https://pnpm.io/)
- **API Keys:**
  - An LLM API key (Anthropic, OpenAI, or Google)
  - A [Zep Cloud](https://app.getzep.com/) API key (free tier sufficient for PoC)

### Docker (Recommended)

```bash
git clone https://github.com/intercom/gtm-mirofish-demo.git
cd gtm-mirofish-demo
cp .env.example .env
# Edit .env — set LLM_API_KEY and ZEP_API_KEY at minimum
docker compose up -d
```

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5001
- **Health check:** http://localhost:5001/api/health

> **Note:** The Docker build uses `demo_app.py` — a lightweight mock backend that serves realistic pre-built data without the heavy camel-ai/PyTorch stack (~150 MB image vs ~5.8 GB). The frontend is built with `VITE_DEMO_MODE=true` by default. For real LLM-powered simulations, use the [Manual Development](#manual-development) setup below.
>
> The Docker health check uses Python `urllib` (not `curl`) because the backend image is `python:3.11-slim`.

### Manual Development

```bash
# 1. Clone and configure
git clone https://github.com/intercom/gtm-mirofish-demo.git
cd gtm-mirofish-demo
cp .env.example .env
# Edit .env — set LLM_API_KEY and ZEP_API_KEY at minimum

# 2. Create required upload directories
mkdir -p backend/uploads/simulations backend/uploads/projects backend/uploads/reports

# 3. Backend (terminal 1) — choose ONE of the approaches below:

# Option A: Using uv (if installed)
cd backend
uv sync
uv run python run.py

# Option B: Using venv + pip
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py

# Backend runs on http://localhost:5001

# 4. Frontend (terminal 2)
cd frontend
pnpm install
VITE_DEMO_MODE=false pnpm dev
# Frontend runs on http://localhost:3000
```

> **Proxy:** The Vite dev server automatically proxies all `/api/*` requests to the Flask backend at `http://localhost:5001`, so the frontend and backend work together without CORS issues.
>
> **Demo mode:** Set `VITE_DEMO_MODE=false` (shown above) when running locally so the frontend calls the real backend for simulations instead of using mock data. The `frontend/.env.example` already defaults to `false`.
>
> **Port conflict:** If port 3000 is taken, use `VITE_DEMO_MODE=false pnpm dev --port 3001`.

### Verify Installation

```bash
# Check backend health
curl http://localhost:5001/health
# Expected: {"status":"ok","service":"MiroFish Backend"}

# List available GTM scenarios
curl http://localhost:5001/api/gtm/scenarios
```

---

## Running Your First Simulation

1. **Pick a scenario** — Open http://localhost:3000 and choose one of the four pre-built GTM scenarios from the landing page (Outbound Campaign, Signal Validation, Pricing Change, or Personalization). You can also select **Custom** to upload your own seed text.

2. **Configure the run** — Adjust personas, industries, and agent count on the Scenario Builder page. The defaults are tuned for a quick demo run.

3. **Hit "Run Simulation"** — This kicks off a three-stage pipeline:
   - **Ontology generation** — the LLM extracts entity types and relationships from the seed text
   - **Graph build** — chunks are sent to Zep Cloud to construct a knowledge graph
   - **Simulation** — OASIS spawns AI agents that interact on simulated Twitter/Reddit (23 action types)

4. **Watch progress** — The Workspace view shows real-time progress across the Graph and Simulation tabs. Each stage updates its progress bar as tasks complete.

5. **Explore results** — Once the simulation completes:
   - **Generate a report** — click "Generate Report" to produce an evidence-based predictive analysis (the Report Agent searches the graph + simulation data)
   - **Chat** — use the Chat view to ask questions about the simulated world or interview individual agents

---

## Troubleshooting

### Port conflicts

- **Port 5001 in use** (common on macOS — AirPlay Receiver uses 5001): Disable AirPlay Receiver in System Settings > General > AirDrop & Handoff, or change `BACKEND_PORT` in `.env`.
- **Port 3000 in use**: Run `pnpm dev --port 3001` or change `FRONTEND_PORT` in `.env` for Docker.

### Missing uploads directories

If the backend crashes with a `FileNotFoundError` related to uploads, create the directories:

```bash
mkdir -p backend/uploads/simulations backend/uploads/projects backend/uploads/reports
```

### API key validation errors on startup

The backend validates `LLM_API_KEY` and `ZEP_API_KEY` on startup. If either is missing or set to the placeholder value from `.env.example`, it exits with an error. Double-check your `.env` file has real keys:

```
LLM_API_KEY=sk-ant-...    # not "your-api-key-here"
ZEP_API_KEY=z_...          # not "your-zep-api-key-here"
```

### `ERR_NAME_NOT_RESOLVED` when using Docker frontend directly

The Docker Compose frontend is built with `VITE_API_URL=http://backend:5001/api` — this is the Docker-internal hostname. If you open the frontend container's URL in your browser and see network errors referencing `backend:5001`, that is because `backend` is only resolvable inside the Docker network, not from your host machine.

The Docker frontend uses `serve` to host the static build, and API calls are baked in at build time pointing to the internal Docker hostname. This works correctly within the Docker network (frontend container -> backend container), but the browser runs on the host. For local development with hot-reload, use the [Manual Development](#manual-development) setup where Vite's dev proxy handles `/api` routing to `localhost:5001`.

---

## Configuration

All configuration is via the `.env` file. Copy [.env.example](.env.example) to get started.

### LLM Provider

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `anthropic` | LLM provider: `anthropic`, `openai`, or `gemini` |
| `LLM_API_KEY` | Yes | — | API key for the chosen provider |
| `LLM_BASE_URL` | No | Auto-configured | Override the provider's default base URL |
| `LLM_MODEL_NAME` | No | Auto-configured | Override the provider's default model |

Setting `LLM_PROVIDER` auto-configures the base URL and model:

| Provider | Base URL | Default Model |
|----------|----------|---------------|
| `anthropic` | `https://api.anthropic.com/v1/` | `claude-sonnet-4-20250514` |
| `openai` | `https://api.openai.com/v1/` | `gpt-4o` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` |

### Knowledge Graph

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ZEP_API_KEY` | Yes | — | [Zep Cloud](https://app.getzep.com/) API key (free tier sufficient for PoC) |

### Authentication (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_ENABLED` | No | `false` | Enable OAuth login gate |
| `AUTH_PROVIDER` | No | `google` | OAuth provider: `google` or `okta` |
| `AUTH_ALLOWED_DOMAIN` | No | `intercom.io` | Restrict login to this email domain |
| `GOOGLE_CLIENT_ID` | No | — | Google OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | No | — | Google OAuth 2.0 client secret |
| `OKTA_ISSUER` | No | — | Okta SSO issuer URL |
| `OKTA_CLIENT_ID` | No | — | Okta client ID |

### Accelerated LLM (Optional)

For parallel processing with a secondary LLM provider:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_BOOST_API_KEY` | No | — | Separate LLM key for parallel processing |
| `LLM_BOOST_BASE_URL` | No | — | Base URL for boost provider |
| `LLM_BOOST_MODEL_NAME` | No | — | Model name for boost provider |

### Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_PORT` | No | `5001` | Flask backend port |
| `FRONTEND_PORT` | No | `3000` | Vite dev server port |
| `FLASK_DEBUG` | No | `true` | Enable Flask debug mode |
| `SECRET_KEY` | No | `change-me-in-production` | Flask session secret key |

---

## Architecture

```
                    +--------------------------------------------------+
                    |                Frontend (Vue 3)                    |
                    |  Vite + Tailwind + Pinia + D3.js + Vue Router     |
                    |  27 views, 60+ composables, 40 stores            |
                    |  Port 3000                                        |
                    +--+-----+-----+-----+-----+-----+-----+-----+----+
                       |     |     |     |     |     |     |     |
                  /api/graph |  /api/sim | /api/report | /api/gtm |
                       | /api/agents | /api/analytics | /api/campaigns
                       |     |     |     |     |     |     |     |
                    +--v-----v-----v-----v-----v-----v-----v-----v----+
                    |              Backend (Flask)                      |
                    |  49 API modules, 70+ services                    |
                    |  OASIS Simulation + Zep GraphRAG + GTM Ops       |
                    |  Port 5001                                       |
                    +----+----------+----------+----------+-----------+
                         |          |          |          |
                   +-----v----+ +--v------+ +-v-------+ +v----------+
                   | Zep Cloud| | LLM API | | GTM Seed| | In-Memory |
                   | (GraphRAG| | Claude/ | | Data    | | Cache &   |
                   |  Memory) | | GPT/Gem | | (JSON)  | | Sessions  |
                   +----------+ +---------+ +---------+ +-----------+
```

### Data Flow

```
1. UPLOAD        User selects scenario or uploads custom seed text
                       |
2. GRAPH BUILD   Text -> chunks -> Zep Cloud -> knowledge graph
                       |
3. SIMULATE      Graph entities -> OASIS agent personas
                 Agents interact on simulated Twitter/Reddit (23 action types)
                       |
4. REPORT        Report Agent searches graph + simulation data
                 Generates evidence-based predictive analysis
                       |
5. INTERVIEW     User chats with individual agents or the Report Agent
```

### Request Flow

All long-running operations follow the same async pattern:

```
Client                         Server
  |-- POST /api/*/start -------->|  (returns task_id immediately)
  |                              |  [background thread starts]
  |-- GET /api/*/status -------->|  (poll for progress)
  |<-------- {progress: 45%} ----|
  |-- GET /api/*/status -------->|
  |<-------- {status: complete} -|
  |-- GET /api/*/result -------->|  (fetch completed data)
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Vue 3.5 + Vite 8 + Tailwind CSS 4 + Pinia 3 + Vue Router 4 |
| Visualization | D3.js v7 (force-directed knowledge graphs) |
| Markdown | Marked 17 (report rendering) |
| HTTP Client | Axios 1.13 |
| Backend | Flask 3.0+ (Python 3.11+) |
| Simulation | OASIS (camel-oasis 0.2.5) — up to 1M agents |
| AI Framework | CAMEL-AI 0.2.78 (multi-agent orchestration) |
| Memory | Zep Cloud 3.13 (temporal knowledge graphs) |
| LLM | Any OpenAI-compatible API (via openai SDK) |
| File Processing | PyMuPDF (PDF), charset-normalizer (encoding) |
| Validation | Pydantic 2.0+ |
| Auth | Google OAuth / Okta SSO (optional) |
| Package Mgmt | uv (Python), pnpm (Node) |
| Deploy | Docker Compose |

---

## GTM Scenarios

Four pre-built scenarios ship in `backend/gtm_scenarios/`. Each includes seed text, agent persona definitions, simulation configuration, and expected output types.

### 1. Outbound Campaign Pre-Testing (Hero)

Simulate how AI-generated outbound emails land with synthetic prospect populations.

- **Agent count:** 200 personas (VP of Support, CX Director, IT Leader, Head of Operations)
- **Seeds:** Email copy, target segment description, firmographic data
- **Tests:** 4 subject line variants
- **Key outputs:** Engagement prediction by persona, subject line effectiveness, objection mapping by industry, optimal cadence

### 2. Sales Signal Validation

Test whether sales signals actually predict buying behavior.

- **Agent count:** 500 personas across 5 decision-making roles
- **Seeds:** 8 signal definitions from Intercom's DBT models
- **Signals tested:** Product Usage Surge, Competitor Research, Feature Exploration, Contract Approaching, Expansion Indicator, Champion Change, Technographic Match, Third-Party Intent
- **Key outputs:** Signal-to-buying correlation, false positive rates, recommended signal priority ranking

### 3. Pricing Change Simulation

Predict customer reactions to P5 pricing migration.

- **Agent count:** 500 customer personas (SMB / Mid-Market / Enterprise)
- **Seeds:** 4 pricing scenarios and customer segment mix
- **Tests:** 4 pricing scenarios
- **Key outputs:** Churn probability by segment, public sentiment risk, competitive switch likelihood, optimal migration strategy

### 4. Personalization Optimization

Rank email personalization variants by simulated engagement.

- **Agent count:** 200 personas
- **Seeds:** 10 message variants across dimensions (tone, length, personalization depth, CTA style)
- **Key outputs:** Variant ranking by segment, most impactful personalization dimensions, segment-specific recommendations

### Seed Data

Anonymized GTM data is provided in `backend/gtm_seed_data/`:

| File | Contents |
|------|----------|
| `account_profiles.json` | 4 company profiles with segment, industry, ARR, health score, churn risk |
| `persona_templates.json` | 4 buyer personas with role, priorities, objections, communication style |
| `signal_definitions.json` | 8 sales signal types with accuracy and adoption metrics |
| `email_templates.json` | 3 outbound email templates (ROI pitch, case study, competitive displacement) |

---

## Development Guide

### Project Structure

```
gtm-mirofish-demo/
├── backend/                    # Flask backend (MiroFish fork)
│   ├── app/
│   │   ├── __init__.py         # Flask app factory, blueprint registration
│   │   ├── config.py           # Multi-LLM provider configuration
│   │   ├── api/                # 49 Flask Blueprint modules
│   │   │   ├── graph.py        # Knowledge graph CRUD + build routes
│   │   │   ├── simulation.py   # OASIS simulation lifecycle routes
│   │   │   ├── report.py       # Report generation + chat routes
│   │   │   ├── settings.py     # Settings and config routes
│   │   │   ├── gtm_scenarios.py # GTM scenario template API
│   │   │   ├── agents.py       # Agent CRUD and management
│   │   │   ├── analytics.py    # Analytics and metrics endpoints
│   │   │   ├── auth.py         # Authentication routes
│   │   │   ├── beliefs.py      # Agent belief system tracking
│   │   │   ├── campaigns.py    # Campaign management
│   │   │   ├── comparison.py   # Simulation comparison
│   │   │   ├── cpq.py          # Configure-Price-Quote
│   │   │   ├── deals.py        # Deal management
│   │   │   ├── gtm_dashboard.py # GTM dashboard data
│   │   │   ├── insights.py     # AI-powered insights
│   │   │   ├── memory.py       # Agent memory management
│   │   │   ├── metrics.py      # Metrics collection
│   │   │   ├── pipeline.py     # Sales pipeline data
│   │   │   ├── revenue.py      # Revenue tracking
│   │   │   ├── salesforce.py   # SFDC integration
│   │   │   └── ...             # 25+ additional modules
│   │   ├── models/             # Project + task persistence
│   │   ├── services/           # 70+ business logic modules
│   │   │   ├── graph_builder.py
│   │   │   ├── simulation_runner.py
│   │   │   ├── simulation_manager.py
│   │   │   ├── report_agent.py
│   │   │   ├── agent_factory.py      # Agent creation and management
│   │   │   ├── belief_tracker.py     # Agent belief evolution
│   │   │   ├── coalition_detector.py # Emergent group detection
│   │   │   ├── debate_engine.py      # Agent debate orchestration
│   │   │   ├── insight_generator.py  # AI insight generation
│   │   │   ├── whatif_engine.py      # What-if scenario analysis
│   │   │   ├── anomaly_detector.py   # Anomaly detection
│   │   │   ├── sentiment_dynamics.py # Sentiment evolution tracking
│   │   │   └── ...
│   │   └── utils/
│   │       ├── llm_client.py   # Multi-provider LLM abstraction
│   │       ├── file_parser.py  # PDF/MD/TXT file processing
│   │       ├── logger.py       # Logging configuration
│   │       ├── retry.py        # Retry logic decorator
│   │       ├── pagination.py   # API pagination utilities
│   │       ├── responses.py    # Standardized response helpers
│   │       ├── decorators.py   # Route decorators
│   │       ├── degradation.py  # Graceful degradation utilities
│   │       └── zep_paging.py   # Zep pagination utilities
│   ├── auth/                   # OAuth middleware (Google/Okta)
│   ├── gtm_scenarios/          # Pre-built scenario JSON files
│   ├── gtm_seed_data/          # Anonymized GTM data
│   ├── scripts/                # Utility scripts for direct simulation
│   ├── demo_app.py             # Lightweight mock server for Docker/demos
│   ├── run.py                  # Backend entry point
│   └── pyproject.toml          # Python dependencies (uv)
├── frontend/                   # Vue 3 frontend
│   ├── src/
│   │   ├── api/                # 45 API modules built on shared Axios client
│   │   │   ├── client.js       # Axios base client with error normalization
│   │   │   ├── graph.js        # Knowledge graph API calls
│   │   │   ├── simulation.js   # Simulation lifecycle API calls
│   │   │   ├── report.js       # Report generation API calls
│   │   │   ├── scenarios.js    # GTM scenario API calls
│   │   │   ├── chat.js         # Chat/interview API calls
│   │   │   ├── agents.js       # Agent management
│   │   │   ├── analytics.js    # Analytics data
│   │   │   ├── campaigns.js    # Campaign management
│   │   │   ├── comparison.js   # Simulation comparison
│   │   │   ├── dashboards.js   # Dashboard configuration
│   │   │   ├── pipeline.js     # Sales pipeline
│   │   │   ├── revenue.js      # Revenue data
│   │   │   └── ...             # 30+ additional modules
│   │   ├── assets/
│   │   │   └── brand-tokens.css # Intercom design tokens (CSS variables)
│   │   ├── components/         # Feature-grouped Vue components
│   │   │   ├── agents/         # Agent creation wizard (4 step components)
│   │   │   ├── analytics/      # Anomaly dashboard, cohort analysis, AI analyst
│   │   │   ├── campaigns/      # Attribution, cost modeling, ROI comparison
│   │   │   ├── charts/         # 11 D3.js chart components
│   │   │   ├── common/         # 25+ reusable UI primitives
│   │   │   ├── comparison/     # A/B scenario builder, radar, timeline
│   │   │   ├── cpq/            # Product catalog, quotes, discounts
│   │   │   ├── dashboard/      # GTM dashboard layout + 9 widget types
│   │   │   ├── demo/           # PresenterToolbar (demo mode)
│   │   │   ├── graph/          # Agent knowledge graph, community view
│   │   │   ├── insights/       # AI analyst, insight cards
│   │   │   ├── landing/        # HeroSwarm animation
│   │   │   ├── layout/         # AppLayout, AppNav, AppFooter, MobileNav
│   │   │   ├── navigation/     # Navigation mini-map
│   │   │   ├── orders/         # Billing overview
│   │   │   ├── report/         # Report charts and visualization
│   │   │   ├── simulation/     # GraphPanel, SimulationPanel, PhaseNav
│   │   │   └── ui/             # ConfirmDialog, EmptyState, LoadingSpinner
│   │   ├── composables/        # 60+ Vue composition functions
│   │   ├── stores/             # 40 Pinia state management modules
│   │   ├── views/              # 27 route-level page components
│   │   └── router/             # Vue Router configuration
│   ├── package.json
│   └── vite.config.js          # Proxy /api -> backend:5001
├── docs/
│   ├── adr/                    # Architecture Decision Records (11 ADRs)
│   ├── scenarios/              # GTM scenario documentation (4 guides)
│   ├── screenshots/            # Application screenshots (8 images)
│   ├── slides/                 # Demo deck and presentation materials
│   ├── architecture.md         # Detailed architecture documentation
│   ├── deployment.md           # Deployment guide
│   ├── demo-script.md          # Demo walkthrough script
│   └── troubleshooting.md      # Extended troubleshooting guide
├── docker-compose.yml          # Two-service Docker setup
└── .env.example                # All environment variables
```

### Frontend Development

The frontend is a complete Vue 3 rebuild with Intercom branding.

```bash
cd frontend
pnpm install
pnpm dev          # Dev server on http://localhost:3000
pnpm build        # Production build to dist/
pnpm preview      # Preview production build
```

The Vite dev server proxies all `/api` requests to `http://localhost:5001` (configurable via `BACKEND_URL` env var).

**Conventions:**
- All components use Composition API with `<script setup>`
- Tailwind CSS v4 via `@tailwindcss/vite` plugin — no `tailwind.config.js`; design tokens live in `src/assets/brand-tokens.css` as CSS variables
- API requests go through modules in `src/api/` which build on the shared Axios client in `src/api/client.js`
- State management via Pinia stores in `src/stores/`
- Reusable logic via composables in `src/composables/`
- Routing via Vue Router with lazy-loaded views for code splitting

**Composables** (`src/composables/`):

60+ reusable composition functions, grouped by category:

| Category | Key Composables | Purpose |
|----------|----------------|---------|
| **Core** | `useDemoMode`, `useDemoPreset`, `useTheme`, `useToast`, `useSession` | App-wide state (demo mode, theming, notifications, sessions) |
| **Simulation** | `useSimulationPolling`, `useSimulationSSE`, `useSimulationStream`, `useSimulationState`, `useSimulationCache`, `useReplay` | Simulation lifecycle, real-time updates, caching, and playback |
| **Data** | `useApiCache`, `useReportCache`, `useSimulationCache`, `useComparisonData`, `usePagination`, `useSortableTable` | API caching, pagination, data comparison |
| **UI/UX** | `useCountUp`, `useChartEntrance`, `useFlowAnimation`, `useMicroInteractions`, `useStaggerAnimation`, `useParallax`, `useFormAnimations` | Animations, transitions, micro-interactions |
| **Navigation** | `useCommandPalette`, `useKeyboardShortcuts`, `useNavigationShortcuts`, `useBreadcrumbs`, `usePageTransition` | Keyboard navigation, command palette, breadcrumbs |
| **Dashboard** | `useDashboardLayout`, `useDragAndDrop`, `useActivityFeed`, `useMetricsCollector` | Dashboard grid, drag-and-drop, activity feeds |
| **Reports** | `useReportCache`, `useReportShortcuts`, `useReportTheme` | Report navigation, theming, and keyboard shortcuts |
| **Visualization** | `useForceGraph3D`, `useD3PerfMonitor`, `useMobileChart`, `useTimelineScrubber`, `useTimelineSync` | 3D graph rendering, D3 performance, timeline controls |
| **Platform** | `useAuth`, `usePermissions`, `useLocale`, `useLanguage`, `useOnboardingTour` | Auth, permissions, i18n, onboarding |
| **Resilience** | `useOfflineMode`, `useOnlineStatus`, `useServiceWorker`, `useServiceHealth`, `useServiceStatus`, `usePwaInstall` | Offline support, service workers, PWA install |
| **Real-time** | `useWebSocket`, `useSimulationSSE`, `usePullToRefresh`, `useResourcePreload`, `useLazyLoad` | WebSocket, SSE, lazy loading, resource preloading |

**Pinia Stores** (`src/stores/`):

40 state management modules, grouped by domain:

| Domain | Stores | Purpose |
|--------|--------|---------|
| **Core** | `auth`, `settings`, `session`, `toast`, `notifications`, `navigation` | Authentication, app config, notifications |
| **Simulation** | `simulation`, `scenarios`, `graph`, `agents`, `personas`, `beliefs`, `personality`, `relationships`, `coalition` | Simulation lifecycle, agent state, social dynamics |
| **GTM Ops** | `pipeline`, `revenue`, `salesforce`, `cpq`, `orders`, `reconciliation`, `attribution`, `dataPipeline` | Sales pipeline, revenue, SFDC, CPQ |
| **Analytics** | `metrics`, `insights`, `dashboards`, `aggregation` | Metrics, AI insights, dashboard config |
| **Content** | `report`, `reportBuilder`, `templates`, `whatif` | Reports, templates, what-if scenarios |
| **Platform** | `users`, `locale`, `theme`, `themes`, `tutorial`, `activity`, `memoryTransfer` | User management, i18n, theming, activity |

**API Client** (`src/api/`):

The frontend uses a modular API layer built on Axios with 45 domain-specific modules. `client.js` creates a shared instance with `baseURL` from `VITE_API_URL` (defaults to `/api`) and a response interceptor that normalizes errors to `{ message, status, data }`. Modules cover graph, simulation, report, scenarios, chat, agents, analytics, campaigns, comparison, cpq, dashboards, deals, insights, memory, metrics, pipeline, revenue, salesforce, and more.

**Frontend Views:**

| Route | View | Purpose |
|-------|------|---------|
| `/` | LandingView | Scenario cards, "How It Works" section |
| `/scenarios` | ScenariosView | Scenario list and filtering |
| `/scenarios/:id` | ScenarioBuilderView | Configure and launch a simulation |
| `/scenarios/:id/walkthrough` | ScenarioWalkthroughView | Guided scenario walkthrough |
| `/marketplace` | ScenarioMarketplaceView | Browse and discover scenario templates |
| `/workspace/:taskId` | SimulationWorkspaceView | Unified tabbed workspace (Graph + Simulation + Network) |
| `/workspace/:taskId/agent/:agentId` | AgentProfileView | Individual agent persona detail and interview |
| `/agents` | AgentsView | Agent management and creation |
| `/simulations` | SimulationsView | Persistent simulation history with search/filter |
| `/replay/:taskId` | ReplayView | Step-through simulation replay with timeline |
| `/comparison` | ComparisonView | Side-by-side simulation comparison |
| `/compare` | CompareView | A/B scenario comparison builder |
| `/report/:taskId` | ReportView | Multi-chapter report explorer |
| `/report/new` | ReportWizardView | Guided report creation wizard |
| `/chat/:taskId` | ChatView | Q&A with simulated world |
| `/knowledge-graph/:graphId?` | KnowledgeGraphView | Standalone knowledge graph explorer |
| `/network/:taskId` | — | Redirects to `/workspace/:taskId?tab=network` |
| `/dashboard` | GtmDashboardView | Executive GTM dashboard with KPIs |
| `/dashboard-builder` | DashboardBuilderView | Drag-and-drop custom dashboard creation |
| `/analytics` | AnalyticsView | Cohort analysis, segments, anomaly detection |
| `/visualizations` | VisualizationsView | D3 visualization gallery |
| `/charts` | ChartsGalleryView | Interactive chart component showcase |
| `/org-chart` | OrgChartView | Organizational chart view |
| `/api-docs` | ApiDocsView | Interactive API documentation |
| `/settings` | SettingsView | LLM provider, API keys, theme |
| `/login` | LoginView | OAuth login page |
| `/permission-denied` | PermissionDeniedView | Access denied error page |

> **Redirects:** `/graph/:taskId` and `/simulation/:taskId` load the workspace with the appropriate tab. `/network/:taskId` redirects to the workspace network tab. All routes use lazy loading for code splitting.

**Intercom Design Tokens:**
- Primary blue: `#2068FF`
- Navy: `#050505`
- Fin orange: `#ff5600`
- Accent purple: `#A0F`
- Success green: `#090`
- Font: system-ui stack (Segoe UI, Roboto, Helvetica, Arial)

### Backend Development

The backend has grown from a minimal MiroFish fork into a comprehensive GTM operations platform with 49 API modules and 70+ services.

```bash
cd backend
uv sync             # Install dependencies
uv run python run.py # Start on http://localhost:5001
```

The backend validates `LLM_API_KEY` and `ZEP_API_KEY` on startup. If either is missing, it exits with an error.

**Conventions:**
- Core MiroFish services in `app/services/` (graph_builder, simulation_runner, simulation_manager, oasis_*, zep_*) are **read-only** — do not modify
- New API routes go in `app/api/` as Flask Blueprints, registered in `app/__init__.py`
- All LLM calls go through `app/utils/llm_client.py` (multi-provider abstraction)
- Configuration is resolved via `app/config.py` from `.env`
- All routes return JSON with `{success: bool, data: ..., error: ...}` shape
- Async operations return a `task_id` for polling via `/api/graph/task/<task_id>`
- Standardized response helpers available in `app/utils/responses.py`
- Route decorators for auth/permissions in `app/utils/decorators.py`

### Running with Docker

```bash
# Build and start both services
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build

# Stop
docker compose down
```

The Docker setup uses a named volume for `backend/uploads` to persist simulation data across container restarts.

### Running Tests

```bash
# Backend
cd backend
uv run pytest

# Frontend
cd frontend
pnpm test          # If test runner is configured
```

---

## Deployment

This project is designed to run locally or in any Docker-compatible environment. See [Quick Start](#quick-start) for setup instructions.

For detailed deployment documentation, see [docs/deployment.md](docs/deployment.md).

---

## Documentation

Additional documentation lives in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | Detailed architecture documentation |
| [Deployment](docs/deployment.md) | Production deployment guide |
| [Demo Script](docs/demo-script.md) | Step-by-step demo walkthrough |
| [Troubleshooting](docs/troubleshooting.md) | Extended troubleshooting guide |
| [ADRs](docs/adr/) | Architecture Decision Records (11 records) |
| [Scenarios](docs/scenarios/) | Per-scenario deep-dive documentation |
| [Slides](docs/slides/) | Presentation materials |

---

## API Reference

All endpoints are prefixed with `/api`. The backend registers 49 blueprint modules organized into functional groups. Below are the core APIs — the full endpoint list is available at `/api-docs` in the running application.

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Returns `{status: "ok", service: "MiroFish Backend"}` |

### Graph (`/api/graph`)

Project and knowledge graph management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/graph/ontology/generate` | Upload files (PDF/MD/TXT) and generate entity/edge ontology |
| POST | `/api/graph/build` | Start async knowledge graph build from a project |
| GET | `/api/graph/project/<project_id>` | Get project details |
| GET | `/api/graph/project/list` | List all projects |
| DELETE | `/api/graph/project/<project_id>` | Delete a project |
| POST | `/api/graph/project/<project_id>/reset` | Reset project state for rebuild |
| GET | `/api/graph/task/<task_id>` | Get async task status and progress |
| GET | `/api/graph/tasks` | List all tasks |
| GET | `/api/graph/data/<graph_id>` | Get graph nodes and edges |
| DELETE | `/api/graph/delete/<graph_id>` | Delete a Zep graph |

### Simulation (`/api/simulation`)

Simulation lifecycle, agent management, and interview system.

**Lifecycle:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulation/create` | Create a new simulation |
| POST | `/api/simulation/prepare` | Prepare simulation environment (async, LLM generates config) |
| POST | `/api/simulation/prepare/status` | Check preparation task progress |
| POST | `/api/simulation/start` | Start running the simulation |
| POST | `/api/simulation/stop` | Stop a running simulation |
| GET | `/api/simulation/<simulation_id>` | Get simulation state |
| GET | `/api/simulation/list` | List all simulations |
| GET | `/api/simulation/history` | Get simulation history with project details |

**Entities & Profiles:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/simulation/entities/<graph_id>` | Get all entities from a graph |
| GET | `/api/simulation/entities/<graph_id>/<entity_uuid>` | Get single entity detail |
| GET | `/api/simulation/entities/<graph_id>/by-type/<type>` | Get entities filtered by type |
| POST | `/api/simulation/generate-profiles` | Generate OASIS agent profiles from graph |
| GET | `/api/simulation/<sim_id>/profiles` | Get simulation agent profiles |
| GET | `/api/simulation/<sim_id>/profiles/realtime` | Realtime profile generation progress |
| GET | `/api/simulation/<sim_id>/config` | Get LLM-generated simulation config |
| GET | `/api/simulation/<sim_id>/config/realtime` | Realtime config generation progress |
| GET | `/api/simulation/<sim_id>/config/download` | Download simulation config file |
| GET | `/api/simulation/script/<name>/download` | Download simulation run script |

**Runtime & Data:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/simulation/<sim_id>/run-status` | Realtime simulation run status |
| GET | `/api/simulation/<sim_id>/run-status/detail` | Detailed run status with all actions |
| GET | `/api/simulation/<sim_id>/actions` | Agent action history |
| GET | `/api/simulation/<sim_id>/timeline` | Round-by-round timeline |
| GET | `/api/simulation/<sim_id>/agent-stats` | Per-agent statistics |
| GET | `/api/simulation/<sim_id>/posts` | Simulated posts (Twitter/Reddit) |
| GET | `/api/simulation/<sim_id>/comments` | Simulated comments (Reddit) |

**Interviews:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulation/interview` | Interview a single agent |
| POST | `/api/simulation/interview/batch` | Batch interview multiple agents |
| POST | `/api/simulation/interview/all` | Interview all agents with same question |
| POST | `/api/simulation/interview/history` | Get interview history |
| POST | `/api/simulation/env-status` | Check if simulation env is alive |
| POST | `/api/simulation/close-env` | Gracefully close simulation env |

### Report (`/api/report`)

Report generation, retrieval, and analysis chat.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/report/generate` | Generate predictive report (async) |
| POST | `/api/report/generate/status` | Check report generation progress |
| GET | `/api/report/<report_id>` | Get completed report |
| GET | `/api/report/by-simulation/<sim_id>` | Get report by simulation ID |
| GET | `/api/report/list` | List all reports |
| GET | `/api/report/<report_id>/download` | Download report as Markdown |
| DELETE | `/api/report/<report_id>` | Delete a report |
| POST | `/api/report/chat` | Chat with Report Agent (Q&A with simulated world) |
| GET | `/api/report/check/<sim_id>` | Check if simulation has a report |
| GET | `/api/report/<report_id>/progress` | Realtime report generation progress |
| GET | `/api/report/<report_id>/sections` | Get generated sections (incremental) |
| GET | `/api/report/<report_id>/section/<index>` | Get single section content |
| GET | `/api/report/<report_id>/agent-log` | Report Agent execution log |
| GET | `/api/report/<report_id>/agent-log/stream` | Full agent log (one-shot) |
| GET | `/api/report/<report_id>/console-log` | Console output log |
| GET | `/api/report/<report_id>/console-log/stream` | Full console log (one-shot) |
| POST | `/api/report/tools/search` | Graph search tool (debug) |
| POST | `/api/report/tools/statistics` | Graph statistics tool (debug) |

### GTM Extensions (`/api/gtm`)

Pre-built GTM scenario templates and seed data.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gtm/scenarios` | List all GTM scenario templates |
| GET | `/api/gtm/scenarios/<scenario_id>` | Get scenario with full configuration |
| GET | `/api/gtm/scenarios/<scenario_id>/seed-text` | Get ready-to-use seed text for graph building |
| GET | `/api/gtm/seed-data/<data_type>` | Get seed data by type (`account_profiles`, `signal_definitions`, `email_templates`, `persona_templates`) |

### Agents (`/api/v1/agents`)

Agent lifecycle management and intelligence.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents` | List all custom agents |
| POST | `/api/v1/agents` | Create a new agent |
| GET | `/api/v1/agents/<agent_id>` | Get agent details |
| PUT | `/api/v1/agents/<agent_id>` | Update agent configuration |
| DELETE | `/api/v1/agents/<agent_id>` | Delete an agent |

### Analytics & Insights (`/api/v1/analytics`, `/api/v1/insights`)

Analytics dashboards, metrics, and AI-powered insights.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/overview` | Analytics overview dashboard data |
| GET | `/api/v1/analytics/cohorts` | Cohort analysis data |
| GET | `/api/v1/analytics/segments` | Segment performance data |
| GET | `/api/v1/insights` | AI-generated insights |
| GET | `/api/v1/metrics` | Collected metrics data |
| GET | `/api/v1/attribution` | Campaign attribution analysis |

### GTM Dashboard (`/api/v1/gtm-dashboard`)

Executive GTM dashboard with pipeline and revenue data.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/gtm-dashboard/overview` | Dashboard overview with KPIs |
| GET | `/api/v1/gtm-dashboard/pipeline` | Revenue pipeline data |
| GET | `/api/v1/gtm-dashboard/deals` | Deal management data |

### Comparison (`/api/v1/comparison`)

Side-by-side simulation comparison.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/comparison/compare` | Compare two or more simulations |
| GET | `/api/v1/comparison/<comparison_id>` | Get comparison results |

### Additional API Groups

The backend includes 30+ additional API modules. Key groups:

| API Group | Prefix | Purpose |
|-----------|--------|---------|
| Beliefs | `/api/v1/beliefs` | Agent belief system tracking and evolution |
| Campaigns | `/api/v1/campaigns` | Campaign management and generation |
| CPQ | `/api/v1/cpq` | Configure-Price-Quote (products, quotes, discounts) |
| Deals | `/api/v1/deals` | Deal lifecycle management |
| Memory | `/api/v1/memory` | Agent memory management and transfer |
| Personality | `/api/v1/personality` | Agent personality dynamics (Big Five model) |
| Pipeline | `/api/v1/pipeline` | Sales pipeline data and sync |
| Revenue | `/api/v1/revenue` | Revenue tracking and forecasting |
| Salesforce | `/api/v1/salesforce` | SFDC data integration |
| Sessions | `/api/v1/sessions` | User session management |
| Team | `/api/v1/team` | Team management |
| Templates | `/api/v1/templates` | Scenario and report templates |
| Users | `/api/v1/users` | User management and roles |
| Audit Log | `/api/v1/audit` | Audit trail for actions |
| Batch | `/api/v1/batch` | Batch operation execution |
| Cache | `/api/v1/cache` | Cache management |
| Data Pipeline | `/api/v1/data-pipeline` | Data pipeline status and sync |
| Predictions | `/api/v1/predictions` | Predictive model outputs |
| Report Builder | `/api/v1/report-builder` | Custom report builder |
| Debate | `/api/v1/debate` | Agent debate orchestration |
| Decisions | `/api/v1/decisions` | Decision tracking and explainability |

---

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the [Development Guide](#development-guide) to set up your environment
4. Make your changes

### Guidelines

- **Core MiroFish services are read-only** — `backend/app/services/` modules for graph_builder, simulation_runner, simulation_manager, and oasis_* should not be modified
- **Frontend uses Composition API** — All Vue components must use `<script setup>` syntax
- **Use Intercom brand tokens** — Reference `frontend/src/assets/brand-tokens.css` for colors and spacing (primary blue `#2068FF`, navy `#050505`, fin orange `#ff5600`, accent purple `#A0F`)
- **Use pnpm** for frontend package management (not npm or yarn)
- **Use uv** for backend package management
- **API responses** follow the `{success: bool, data: ..., error: ...}` convention
- **API routes** — All frontend API requests use the `/api` prefix, which Vite proxies to the Flask backend
- **ADRs** — Record significant architecture decisions in `docs/adr/` following the existing format
- Keep commits focused — one logical change per commit

### Submitting Changes

1. Ensure your code follows existing patterns and conventions
2. Test your changes locally (both Docker and manual setups)
3. Submit a pull request with a clear description of what changed and why

---

## License

AGPL-3.0 — inherited from [MiroFish](https://github.com/666ghj/MiroFish). See [LICENSE](LICENSE).

---

## Credits

- **[MiroFish](https://github.com/666ghj/MiroFish)** by Shanda Group — the swarm intelligence engine powering this demo
- **[OASIS](https://github.com/camel-ai/oasis)** — social simulation framework (up to 1M agents)
- **[Zep Cloud](https://www.getzep.com/)** — temporal knowledge graph memory
- **Intercom GTM Systems Team** — Spenser Wellen, Spencer Cross, Bil Erdenekhuyag
