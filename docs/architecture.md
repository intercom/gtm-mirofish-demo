# Architecture Documentation

GTM MiroFish Demo — a swarm intelligence engine for GTM operations simulation, forked from MiroFish and branded for Intercom.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                         │
│  Vite · Tailwind CSS v4 · D3.js v7 · Pinia · Vue Router · i18n│
│  Port 3000                                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ /api/* (Vite proxy in dev,
                             │        VITE_API_URL in prod)
┌────────────────────────────▼────────────────────────────────────┐
│                       Backend (Flask 3.x)                       │
│  48 Blueprints · 76 Services · LLM Client · Task Manager       │
│  Port 5001                                                      │
├──────────┬──────────────┬───────────────┬───────────────────────┤
│  Zep     │  LLM APIs    │  OASIS/CAMEL  │  File System          │
│  Cloud   │  (Anthropic  │  (subprocess) │  (uploads/, logs/,    │
│  (graph  │   OpenAI     │               │   gtm_scenarios/,     │
│  memory) │   Gemini)    │               │   gtm_seed_data/)     │
└──────────┴──────────────┴───────────────┴───────────────────────┘
         ▲                                       ▲
         │              Nginx (production)        │
         └────────────── reverse proxy ───────────┘
```

**Two-service architecture** deployed as independent containers with an optional Nginx reverse proxy for production:
- **Frontend** — Vue 3 SPA served by `serve` in production, Vite dev server locally
- **Backend** — Flask application with async task processing, OASIS subprocess management, and comprehensive middleware stack

## Backend Architecture

### Entry Points

| File | Purpose |
|------|---------|
| `backend/run.py` | Production entry — validates config, calls `create_app()`, runs Flask |
| `backend/demo_app.py` | Lightweight demo entry — self-contained mock backend for presentations |

### App Factory (`app/__init__.py`)

Creates the Flask app with:
1. Config loading from environment-aware `Config` class
2. Logger initialization (rotating file + console)
3. CORS for `/api/*` and `/auth/*` routes (configurable origins)
4. GZIP compression (`flask-compress`)
5. CSRF protection (`flask-wtf`) with SPA-friendly cookie + header pattern
6. Auth middleware (JWT-based, loads `g.user` when `AUTH_ENABLED=true`)
7. Graceful degradation middleware (circuit breaker for LLM/Zep)
8. Security headers on all responses
9. Rate limiting middleware
10. Request/response logging middleware
11. Health metrics tracking (per-request latency + error rate)
12. Simulation process cleanup on shutdown
13. 48 Blueprint registrations (see below)
14. Centralized error handlers

### Blueprints

The backend exposes a modular API surface organized into 48 Flask Blueprints:

#### Core Simulation Pipeline

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/graph` | `graph_bp` | Knowledge graph CRUD + async build |
| `/api/v1/simulation` | `simulation_bp` | Simulation lifecycle, entity extraction, profiles |
| `/api/v1/report` | `report_bp` | Report generation via ReACT agent |
| `/api/v1/memory` | `memory_transfer_bp` | Cross-simulation memory transfer |

#### GTM Extensions

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/gtm` | `gtm_bp` | Pre-built scenario templates + unified simulate |
| `/api/v1/gtm/dashboard` | `gtm_dashboard_bp` | GTM executive dashboard data |
| `/api/v1/gtm/templates` | `templates_bp` | Scenario template CRUD |
| `/api/v1/gtm/aggregation` | `aggregation_bp` | Scenario result aggregation |
| `/api/v1/gtm/attribution` | `attribution_bp` | Attribution analysis across scenarios |
| `/api/v1/gtm/campaigns` | `campaigns_bp` | Campaign ROI comparison, efficiency metrics |

#### Agent Intelligence

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/agents` | `agents_bp` | Agent wizard creation, preview, OASIS factory |
| `/api/v1/agent-prompts` | `agent_prompts_bp` | Memory-augmented prompt building |
| `/api/v1/beliefs` | `beliefs_bp` | Agent belief system tracking |
| `/api/v1/personas` | `personas_bp` | Persona generation |
| `/api/v1/personality` | `personality_bp` | Personality dynamics tracking |
| `/api/v1/team` | `team_bp` | Team composition API |
| `/api/v1/debate` | `debate_bp` | Agent debate orchestration |

#### Analytics & Insights

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/analytics` | `analytics_bp` | Cohort analysis, segment performance, anomaly detection |
| `/api/v1/insights` | `insights_bp` | LLM-powered GTM insights |
| `/api/v1/metrics` | `metrics_bp` | OASIS simulation metrics |
| `/api/v1/comparison` | `comparison_bp` | Comparative chart overlays |
| `/api/v1/branches` | `branches_bp` | Branch comparison & insights |
| `/api/v1/decisions` | `decisions_bp` | Decision explanation (LLM-powered) |
| `/api/v1/predictions` | `predictions_bp` | Predictive analytics |

#### Memory & Knowledge

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/memory` | `memory_bp` | Memory search |
| `/api/v1/memory/config` | `memory_config_bp` | Memory configuration |
| `/api/v1/memory/agent` | `agent_memory_bp` | Agent memory abstraction |
| `/api/v1/temporal-memory` | `temporal_memory_bp` | Zep-backed time-travel memory |

#### Revenue & Pipeline

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/deals` | `deals_bp` | Dashboard ticker (deals) |
| `/api/v1/pipeline` | `pipeline_bp` | Pipeline funnel widgets |
| `/api/v1/revenue` | `revenue_bp` | Revenue analytics |
| `/api/v1/orders` | `orders_bp` | Order-to-Cash flow |
| `/api/v1/cpq` | `cpq_bp` | Configure Price Quote |
| `/api/v1/cost-model` | `cost_model_bp` | Campaign cost modeling |
| `/api/v1/reconciliation` | `reconciliation_bp` | Three-way MRR reconciliation |
| `/api/v1/salesforce` | `salesforce_bp` | Salesforce CRM demo data |

#### Infrastructure & Operations

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/health` | `health_bp` | Detailed health checks + service degradation |
| `/api/v1/services` | `services_bp` | Unified service availability checker |
| `/api/v1/data-pipeline` | `data_pipeline_bp` | Connector health, sync status |
| `/api/v1/settings` | `settings_bp` | Connection testing, auth status |
| `/api/v1/cache` | `cache_bp` | Simulation result cache (offline replay) |
| `/api/v1/batch` | `batch_bp` | Multi-request batching |
| `/api/v1/report-builder` | `report_builder_bp` | Report templates + generated reports |

#### Auth & User Management

| Prefix | Blueprint | Purpose |
|--------|-----------|---------|
| `/api/v1/auth` | `auth_bp` | Login, logout, token validation |
| `/auth` | `oauth_bp` | OAuth flow (Google/Okta) |
| `/api/v1/api-keys` | `api_keys_bp` | API key management |
| `/api/v1/sessions` | `sessions_bp` | Session management |
| `/api/v1/users` | `users_bp` | User management |
| `/api/v1/audit` | `audit_bp` | Audit log write |
| `/api/v1/audit-log` | `audit_log_bp` | Audit log viewer |
| `/api/v1/errors` | `errors_bp` | Frontend error tracking |

### Middleware Stack

Middleware executes in registration order on every request:

```
Request
  ↓ Auth middleware (JWT decode → g.user)
  ↓ Graceful degradation (circuit breaker health check)
  ↓ Security headers (XSS, clickjacking, HSTS, CSP)
  ↓ Rate limiter (token bucket per IP, stricter for LLM routes)
  ↓ Request logging (method, path, duration, status)
  ↓ Health metrics tracking (latency + error rate)
  ↓ CSRF token cookie refresh
  ↓ Blueprint route handler
Response
```

| Module | Purpose |
|--------|---------|
| `middleware/security_headers.py` | X-Content-Type-Options, X-Frame-Options, HSTS, CSP, Permissions-Policy |
| `middleware/rate_limit.py` | Token bucket rate limiting (default: 60/min, LLM: 10/min) |
| `middleware/request_logging.py` | Structured request/response logging with timing |
| `middleware/error_handler.py` | Centralized error handlers for 400/404/500 + unhandled exceptions |
| `utils/degradation.py` | Circuit-breaker for LLM/Zep with `@graceful_degradation` decorator |
| `auth/middleware.py` | JWT decode, `require_auth` / `require_role` decorators |

### Services Layer (`app/services/`)

76 service modules organized by domain. Core business logic is separated from route handlers.

#### Simulation Core

| Service | Responsibility |
|---------|---------------|
| `simulation_runner.py` | Spawns OASIS subprocess, monitors state via IPC, collects action logs |
| `simulation_manager.py` | Orchestrates: entity extraction → profile gen → config gen → OASIS start |
| `simulation_engine.py` | Core simulation execution logic |
| `simulation_config_generator.py` | LLM-generated simulation parameters (timing, agent activity, events) |
| `simulation_ipc.py` | File-based IPC with OASIS subprocess (commands/ and responses/ dirs) |
| `simulation_registry.py` | Registry of running/completed simulations |
| `simulation_cache.py` | Caches simulation results for offline replay |
| `oasis_orchestrator.py` | High-level OASIS coordination |
| `oasis_environment.py` | OASIS runtime environment setup |
| `oasis_interaction.py` | Agent-agent interaction patterns |
| `oasis_metrics.py` | OASIS-specific metric collection |
| `oasis_demo.py` | Synthetic agent generation when OASIS unavailable |
| `oasis_profile_generator.py` | Converts Zep graph entities into OASIS agent profiles |

#### Knowledge Graph & Memory

| Service | Responsibility |
|---------|---------------|
| `graph_builder.py` | Uploads text chunks to Zep, polls until graph is built |
| `zep_client.py` | Zep Cloud client singleton with lazy initialization |
| `zep_entity_reader.py` | Paginated entity fetching from Zep graph with filtering |
| `zep_entity_extractor.py` | Entity extraction from text |
| `zep_graph_memory.py` | Zep graph memory read operations |
| `zep_graph_memory_updater.py` | Writes simulation results back to Zep graph |
| `zep_temporal_memory.py` | Time-travel memory queries |
| `zep_tools.py` | Search/retrieval tools (InsightForge, PanoramaSearch, etc.) |
| `memory_consolidation.py` | Cross-session memory consolidation |
| `memory_search.py` | Semantic memory search |
| `memory_transfer.py` | Memory transfer between simulations |

#### Report & Analysis

| Service | Responsibility |
|---------|---------------|
| `report_agent.py` | ReACT agent: queries Zep graph with tools, writes multi-section report |
| `report_agent_engine.py` | Report agent execution engine |
| `report_tools.py` | Tool definitions for report agent |
| `report_templates.py` | Report layout and section templates |
| `report_exporter.py` | Export reports to various formats |

#### Agent Intelligence

| Service | Responsibility |
|---------|---------------|
| `agent_factory.py` | Creates simulation agents from personas |
| `agent_intelligence.py` | Agent reasoning and decision-making |
| `agent_memory.py` | Per-agent memory management |
| `agent_prompts.py` | Memory-augmented prompt construction |
| `belief_tracker.py` | Tracks agent belief evolution across rounds |
| `personality_dynamics.py` | Models personality changes over time |
| `persona_service.py` | LLM persona generation |
| `persona_from_graph.py` | Derives personas from knowledge graph entities |
| `behavior_predictor.py` | Predicts future agent behavior |
| `reasoning_parser.py` | Parses structured agent reasoning output |

#### Analytics & Detection

| Service | Responsibility |
|---------|---------------|
| `anomaly_detector.py` | Detects anomalies in simulation metrics |
| `attribution_service.py` | Attribution analysis across campaign scenarios |
| `coalition_detector.py` | Detects agent coalitions in simulation data |
| `coalition_labeler.py` | Labels detected coalitions |
| `community_detection.py` | Community detection in agent interaction graphs |
| `counterfactual_service.py` | What-if / counterfactual analysis |
| `debate_engine.py` | Orchestrates agent debates |
| `debate_scorer.py` | Scores debate outcomes |
| `decision_explainer.py` | LLM-powered decision explanations |
| `insight_generator.py` | Generates LLM-powered insights from data |
| `interaction_graph.py` | Builds agent interaction graphs |
| `metrics_collector.py` | Collects and aggregates simulation metrics |
| `relationship_tracker.py` | Tracks evolving agent relationships |
| `scenario_aggregator.py` | Aggregates results across scenarios |
| `sensitivity_analyzer.py` | Parameter sensitivity analysis |
| `sentiment_analyzer.py` | Sentiment analysis on agent content |
| `sentiment_dynamics.py` | Tracks sentiment evolution over time |
| `whatif_engine.py` | What-if scenario engine |

#### Data Generators

| Service | Responsibility |
|---------|---------------|
| `campaign_generator.py` | Generates campaign demo data |
| `cpq_data_generator.py` | CPQ demo data (products, quotes, discounts) |
| `otc_data_generator.py` | Order-to-Cash demo data |
| `pipeline_data_generator.py` | Pipeline funnel demo data |
| `pipeline_sync_generator.py` | Data connector sync status |
| `reconciliation_generator.py` | MRR reconciliation demo data |
| `revenue_data_generator.py` | Revenue analytics demo data |
| `sfdc_data_generator.py` | Salesforce CRM demo data |

#### Infrastructure

| Service | Responsibility |
|---------|---------------|
| `activity_feed.py` | Activity feed event tracking |
| `api_key_service.py` | API key lifecycle management |
| `branch_manager.py` | Simulation branch management |
| `branching_engine.py` | Scenario branching logic |
| `cache.py` | General caching layer |
| `data_sources.py` | External data source registry |
| `diagnostics.py` | System diagnostics |
| `health_monitor.py` | Real-time health metrics (RPS, error rate, latency P95) |
| `ontology_generator.py` | LLM-derived entity/edge type ontologies |
| `permissions.py` | RBAC permission checks |
| `scenario_templates.py` | Scenario template CRUD |
| `text_processor.py` | Text chunking, preprocessing, stats |

### Models (`app/models/`)

In-memory dataclass models with thread-safe singleton managers:

- **Project** — tracks graph build lifecycle: `CREATED → ONTOLOGY_GENERATED → GRAPH_BUILDING → GRAPH_COMPLETED`
- **Task** — async task tracking: `PENDING → PROCESSING → COMPLETED/FAILED` with 0-100% progress and progress detail

Both use file-based persistence in `uploads/` — no SQL database.

### LLM Client (`app/utils/llm_client.py`)

Unified LLM abstraction using the OpenAI SDK with base URL routing:

```
LLM_PROVIDER=anthropic  →  base_url: api.anthropic.com/v1/      model: claude-sonnet-4-20250514
LLM_PROVIDER=openai     →  base_url: api.openai.com/v1/          model: gpt-4o
LLM_PROVIDER=gemini     →  base_url: generativelanguage.../v1beta/openai/  model: gemini-2.5-flash
```

Key methods:
- `chat(messages, temperature, max_tokens)` → text response (strips `<think>` blocks from reasoning models)
- `chat_json(messages)` → parsed JSON (strips markdown fences, validates, low temperature default)

Provider-specific behavior:
- Anthropic: `response_format` parameter excluded (unsupported via OpenAI SDK adapter)
- All providers: responses cleaned of `<think>` reasoning blocks

Provider config resolved in `app/config.py` via `get_llm_config()`.

### Configuration (`app/config.py`)

Environment-driven via `python-dotenv` with class-based hierarchy:

```
BaseConfig → DevelopmentConfig (debug=true, verbose logging)
           → ProductionConfig  (debug=false, stricter validation)
```

Selected via `FLASK_ENV` environment variable.

| Category | Variables |
|----------|-----------|
| **LLM** | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME` |
| **Zep** | `ZEP_API_KEY` |
| **Auth** | `AUTH_ENABLED`, `AUTH_PROVIDER`, `AUTH_ALLOWED_DOMAIN`, `RBAC_DEFAULT_ROLE`, OAuth client IDs/secrets (Google + Okta) |
| **Server** | `BACKEND_PORT`, `FLASK_DEBUG`, `SECRET_KEY`, `CORS_ORIGINS`, `LOG_FILE`, `LOG_LEVEL` |
| **OASIS** | `OASIS_DEFAULT_MAX_ROUNDS`, `OASIS_SIMULATION_DATA_DIR` |
| **Report** | `REPORT_AGENT_MAX_TOOL_CALLS`, `REPORT_AGENT_MAX_REFLECTION_ROUNDS`, `REPORT_AGENT_TEMPERATURE` |
| **Rate Limit** | `RATE_LIMIT_ENABLED`, `RATE_LIMIT_DEFAULT`, `RATE_LIMIT_LLM`, `RATE_LIMIT_WINDOW` |
| **Session** | `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE` |
| **Demo** | `DEMO_SPEED` |

ProductionConfig adds validation: `SECRET_KEY` must not be default, `CORS_ORIGINS` must not be wildcard.

### Auth System

Two-layer authentication:

**1. JWT Middleware (`auth/middleware.py`)**
- `create_token(payload, ttl)` — signs JWT with HS256
- `decode_token(token)` — validates expiry and signature
- `init_auth_middleware(app)` — before_request hook loads `g.user` from Bearer token
- `@require_auth` — decorator that returns 401 when `AUTH_ENABLED=true` and no valid token
- `@require_role(role)` — RBAC-based access control
- Public prefixes (`/health`, `/auth/`) bypass auth entirely

**2. OAuth Routes (`auth/oauth_routes.py`)**
- Google OAuth2 login/callback flow
- Okta SSO login/callback flow
- Domain enforcement (`AUTH_ALLOWED_DOMAIN`, default: `intercom.io`)

When `AUTH_ENABLED=false` (default), all auth decorators pass through.

## Frontend Architecture

### App Structure

```
src/
├── main.js                    App bootstrap (Vue + Pinia + Router + i18n)
├── App.vue                    Root: AppLayout wrapper + router-view with transitions
├── style.css                  Global styles + Tailwind v4 + brand token import
├── router/index.js            28 routes, all lazy-loaded views
├── i18n/                      Internationalization setup
├── lib/
│   ├── perfMonitor.js         Performance monitoring (navigation timing, API latency)
│   └── errorTracker.js        Frontend error tracking (sends to /api/v1/errors)
├── api/                       45 Axios-based API client modules
├── stores/                    40 Pinia state management stores
├── composables/               60+ reusable composition functions
├── components/                100+ UI components (15 directories)
├── views/                     27 page-level components
└── assets/brand-tokens.css    Intercom design tokens (CSS custom properties)
```

### Initialization

`main.js` bootstraps:
1. `createApp(App)` — Vue 3 application instance
2. `createPinia()` — state management
3. `i18n` — internationalization
4. `router` — Vue Router with auth guards
5. `errorTracker.install(app, { router })` — global error boundary
6. Performance monitoring: route navigation timing + page load metrics
7. Service worker registration in production

### Views (28 Routes)

| Route | View | Purpose |
|-------|------|---------|
| `/` | `LandingView` | Hero with D3 swarm animation + scenario cards |
| `/login` | `LoginView` | OAuth login (Google/Okta) |
| `/scenarios` | `ScenariosView` | Scenario template browser |
| `/scenarios/:id` | `ScenarioBuilderView` | Seed text, persona, industry config form |
| `/scenarios/:id/walkthrough` | `ScenarioWalkthroughView` | Guided scenario walkthrough |
| `/workspace/:taskId` | `SimulationWorkspaceView` | Tabbed workspace: graph + simulation + network |
| `/workspace/:taskId/agent/:agentId` | `AgentProfileView` | Individual agent persona details |
| `/report/:taskId` | `ReportView` | Multi-chapter markdown report with D3 charts |
| `/report/new` | `ReportWizardView` | Report configuration wizard |
| `/chat/:taskId` | `ChatView` | Chat with report agent (tool call visualization) |
| `/simulations` | `SimulationsView` | Session history dashboard |
| `/settings` | `SettingsView` | LLM provider, API keys, theme, defaults |
| `/dashboard` | `GtmDashboardView` | Executive GTM dashboard |
| `/dashboard-builder` | `DashboardBuilderView` | Custom dashboard creation |
| `/knowledge-graph/:graphId?` | `KnowledgeGraphView` | Knowledge graph explorer |
| `/marketplace` | `ScenarioMarketplaceView` | Scenario marketplace browser |
| `/analytics` | `AnalyticsView` | Analytics overview |
| `/visualizations` | `VisualizationsView` | Visualization gallery |
| `/comparison` | `ComparisonView` | Side-by-side scenario comparison |
| `/compare` | `CompareView` | Detailed comparison view |
| `/agents` | `AgentsView` | Agent management |
| `/org-chart` | `OrgChartView` | Organization chart visualization |
| `/charts` | `ChartsGalleryView` | D3 chart showcase |
| `/replay/:taskId` | `ReplayView` | Simulation replay |
| `/api-docs` | `ApiDocsView` | Interactive API documentation |
| `/permission-denied` | `PermissionDeniedView` | Access denied page |

Auth guard: routes with `meta.requiresAuth` redirect to `/login` when `AUTH_ENABLED=true` and user is unauthenticated.

### Pinia Stores (40 stores)

#### Core Simulation Stores

| Store | Key State |
|-------|-----------|
| `simulation` | `status`, `simulationId`, `graphTaskId`, `progress`, `metrics`, `sessionRuns` |
| `scenarios` | `scenarios[]`, `detailCache{}`, lazy-fetched from `/api/gtm/scenarios` |
| `graph` | Knowledge graph state and metadata |
| `settings` | `provider`, `apiKey`, `zepKey`, `connectionStatus` — auto-persisted to localStorage |
| `auth` | `user`, `token`, `isAuthenticated` |

#### Analytics & Insights Stores

| Store | Key State |
|-------|-----------|
| `aggregation` | Cross-scenario aggregation results |
| `attribution` | Attribution analysis data |
| `metrics` | OASIS simulation metrics |
| `insights` | LLM-generated insights |
| `pipeline` | Pipeline funnel data |
| `revenue` | Revenue analytics data |

#### Agent Intelligence Stores

| Store | Key State |
|-------|-----------|
| `agents` | Agent registry and wizard state |
| `beliefs` | Agent belief system snapshots |
| `coalition` | Detected coalition groups |
| `personality` | Personality dynamics data |
| `personas` | Generated personas |
| `relationships` | Agent relationship tracking |

#### Domain Stores

| Store | Key State |
|-------|-----------|
| `cpq` | Configure-Price-Quote data |
| `orders` | Order-to-Cash pipeline |
| `reconciliation` | MRR reconciliation data |
| `salesforce` | Salesforce CRM demo data |
| `report` | Report generation state |
| `reportBuilder` | Report builder configuration |
| `templates` | Scenario templates |
| `whatif` | What-if analysis parameters |

#### UI & Infrastructure Stores

| Store | Key State |
|-------|-----------|
| `activity` | Activity feed events |
| `annotations` | User annotations on charts |
| `dashboards` | Custom dashboard configurations |
| `dataPipeline` | Data pipeline connector status |
| `locale` | Internationalization locale |
| `memoryTransfer` | Memory transfer state |
| `navigation` | Navigation breadcrumbs |
| `notifications` | Notification queue |
| `session` | User session management |
| `theme` / `themes` | Dark/light mode + custom themes |
| `toast` | Toast notification stack |
| `tutorial` | Onboarding tutorial state |
| `users` | User management |

### Composables (60+)

Reusable composition functions organized by concern:

#### Simulation & Data

| Composable | Purpose |
|------------|---------|
| `useSimulationPolling` | Orchestrates graph + simulation polling at 2-5s intervals; reactive `graphStatus`, `runStatus`, `recentActions`, `timeline`; falls back to demo mode on network error |
| `useSimulationSSE` | Server-Sent Events stream for real-time simulation updates |
| `useSimulationStream` | WebSocket-based simulation streaming |
| `useSimulationState` | Shared simulation state management |
| `useSimulationCache` | Client-side simulation result caching |
| `useReplay` | Simulation replay controls (play/pause/seek) |
| `useComparisonData` | Cross-scenario comparison data loading |
| `useMetricsCollector` | Client-side metrics aggregation |
| `useMemoryTransfer` | Memory transfer composable |
| `useApiCache` | API response caching |

#### UI & UX

| Composable | Purpose |
|------------|---------|
| `useTheme` | Dark/light mode with system detection, route-specific defaults, localStorage persistence |
| `useToast` | Global toast notification stack with auto-dismiss |
| `useCountUp` | requestAnimationFrame number animation for metrics display |
| `useDemoMode` | Feature flag from `VITE_DEMO_MODE` env var |
| `useDemoPreset` | Pre-configured demo scenarios |
| `useCommandPalette` | `Cmd+K` command palette |
| `useKeyboardShortcuts` | Global keyboard shortcut manager |
| `useNavigationShortcuts` | Route-level shortcuts |
| `useSimulationShortcuts` | Simulation-specific shortcuts |
| `useReportShortcuts` | Report view shortcuts |
| `useBreadcrumbs` | Breadcrumb generation from route |
| `usePagination` | Generic pagination logic |
| `useSortableTable` | Sortable table column logic |
| `useOnboardingTour` | Step-by-step onboarding flow |

#### Animations & Visualization

| Composable | Purpose |
|------------|---------|
| `useChartEntrance` | D3 chart entrance animations |
| `useFlowAnimation` | Animated flow diagrams |
| `useFormAnimations` | Form field animations |
| `useMicroInteractions` | Subtle UI micro-interactions |
| `usePageTransition` | Page transition effects |
| `useParallax` | Scroll parallax effects |
| `useStaggerAnimation` | Staggered list animations |
| `useForceGraph3D` | 3D force-directed graph (WebGL) |
| `useD3PerfMonitor` | D3 rendering performance monitoring |
| `useMobileChart` | Responsive chart adaptations |
| `useTimelineScrubber` | Timeline scrubber controls |
| `useTimelineSync` | Synchronized timeline across panels |
| `useReportTheme` | Report-specific theming |

#### Infrastructure

| Composable | Purpose |
|------------|---------|
| `useAuth` | Authentication state and actions |
| `usePermissions` | RBAC permission checks |
| `useSession` | Session lifecycle management |
| `useIntercom` | Optional Intercom widget integration (deferred script load) |
| `useServiceWorker` | PWA service worker registration |
| `useServiceHealth` | Backend service health monitoring |
| `useServiceStatus` | Service status indicators |
| `useSystemStatus` | System-wide status aggregation |
| `useOnlineStatus` | Network connectivity detection |
| `useOfflineMode` | Offline data queuing |
| `usePullToRefresh` | Mobile pull-to-refresh |
| `usePwaInstall` | PWA install prompt |
| `useWebSocket` | WebSocket connection management |
| `useLazyLoad` | Component lazy loading with intersection observer |
| `useResourcePreload` | Route-aware resource preloading |
| `useAutoSave` | Auto-save form state to localStorage |
| `useDragAndDrop` | Drag-and-drop interactions |
| `useLocale` | Locale/i18n helpers |
| `useLanguage` | Language switching |
| `useTransparency` | UI transparency controls |
| `useActivityFeed` | Activity feed composable |
| `useReportCache` | Report result caching |
| `useDashboardLayout` | Dashboard grid layout management |

### API Client (`api/client.js`)

Axios instance with:
- **Base URL** from `VITE_API_URL` (default `/api/v1`)
- **CSRF token** — reads `csrf_token` cookie, attaches as `X-CSRFToken` header on mutating requests
- **Request deduplication** — concurrent identical GET requests share a single network call (Map-based inflight tracker)
- **Bearer token** — reads from `localStorage('mirofish-auth')`, attaches `Authorization` header
- **Performance monitoring** — timing interceptors record request/response latency
- **Error normalization** — response interceptor standardizes error shape: `{ message, status, data }`

45 API modules mirror the backend blueprint structure, each importing the shared client.

### Component Library (100+)

```
components/
├── agents/       AgentCreationWizard, WizardBasic/Expertise/Personality/Preview
├── analytics/    CohortAnalysis, SegmentPerformance, AnomalyDashboard, AiAnalyst
├── campaigns/    RoiComparison, CostModeler, AttributionComparison
├── charts/       BarChart, LineChart, DonutChart, RadarChart, ChordDiagram,
│                 StreamGraph, SunburstChart, CalendarHeatmap, SmallMultiples,
│                 BulletChart, ParallelCoordinates
├── common/       AppButton, AppInput, AppCard, AppBadge, AppModal, Button, Card,
│                 Input, Modal, CommandPalette, ServiceStatus, ThemeSwitcher,
│                 UserMenu, Pagination, SortableTable, MarkdownEditor, RichTextEditor,
│                 OfflineBanner, PresenceIndicator, DemoModeOverlay, RoleBadge,
│                 LockedFeature, StatusIndicator, SystemStatusBar
├── comparison/   ComparisonLayout, ComparisonTable, ComparisonTimeline,
│                 ComparisonRadar, ChartOverlay, AbScenarioBuilder
├── cpq/          QuoteList, QuoteDetail, ProductCatalog, DiscountAnalysis
├── dashboard/    GtmDashboardLayout, ExecutiveKpis, DealsTicker, DealVelocity,
│                 RevenuePipelineChart, FunnelSummaryWidget, HealthScorecard,
│                 TopAccountsTable, ActivityFeed, WidgetPicker, DashboardGrid,
│                 DashboardMiniChart
│   └── widgets/  KpiCardWidget, LineChartWidget, BarChartWidget, DonutChartWidget,
│                 FunnelWidget, GaugeWidget, TableWidget, TextWidget, ActivityFeedWidget
├── demo/         PresenterToolbar
├── graph/        AgentKnowledgeGraph, CommunityView
├── insights/     InsightCards, AiAnalyst
├── landing/      HeroSwarm (D3 particle animation)
├── layout/       AppLayout, AppNav, AppFooter, MobileNav, GuestBanner
├── navigation/   NavigationMiniMap
├── orders/       BillingOverview
├── report/       ReportCharts
└── simulation/   GraphPanel, SimulationPanel, PhaseNav, SentimentTimeline
```

### D3.js Visualizations

| Component | Chart Type | Data Source |
|-----------|-----------|-------------|
| `HeroSwarm` | Animated particle swarm | Procedural (decoration) |
| `GraphPanel` | Force-directed graph | `/api/v1/graph/task/:id` → nodes/edges |
| `AgentKnowledgeGraph` | Agent-specific knowledge graph | Memory/graph data |
| `SentimentTimeline` | Line + stacked bar | Simulation actions (sentiment scored) |
| `ReportCharts` | Horizontal bar charts | Report section data per chapter |
| `BarChart` | Generic bar chart | Any dataset |
| `LineChart` | Line/area chart | Time series data |
| `DonutChart` | Donut/pie chart | Category breakdowns |
| `RadarChart` | Spider/radar chart | Multi-axis comparison |
| `ChordDiagram` | Chord diagram | Agent interaction flows |
| `StreamGraph` | Stacked stream graph | Temporal data streams |
| `SunburstChart` | Sunburst hierarchy | Hierarchical data |
| `CalendarHeatmap` | Calendar heatmap | Activity over time |
| `SmallMultiples` | Small multiples grid | Comparative faceted data |
| `BulletChart` | Bullet chart | KPI vs target |
| `ParallelCoordinates` | Parallel coordinates | Multi-dimensional data |
| `RevenuePipelineChart` | Revenue pipeline | Pipeline funnel data |
| `ComparisonRadar` | Comparison radar | Cross-scenario comparison |
| `ComparisonTimeline` | Comparison timeline | Temporal comparison |

### Design System

Intercom brand tokens defined in `assets/brand-tokens.css` as CSS custom properties:

| Token | Value | Usage |
|-------|-------|-------|
| Primary Blue | `#2068FF` | Buttons, links, active states |
| Navy | `#050505` | Dark backgrounds, header |
| Fin Orange | `#ff5600` | Persona accents, highlights |
| Accent Purple | `#AA00FF` | Relationship indicators |
| Text | `#1a1a1a` | Primary text |

Dark mode: `.dark` class on `<html>` triggers CSS variable overrides (background `#0a0a1a`, surface `#1a1a2e`).

## Data Flow

### End-to-End Simulation Pipeline

```
1. Scenario Selection          GET /api/v1/gtm/scenarios
   User picks a pre-built        ↓
   scenario or writes seed    ScenarioBuilderView form
   text                          ↓

2. Graph Build                POST /api/v1/gtm/simulate
   Seed text → ontology          ↓ returns task_id
   → Zep graph build          Poll GET /api/v1/graph/task/:id (2s interval)
   (async, ~30-120s)             ↓ graph_id on completion

3. Entity Extraction          GET /api/v1/simulation/entities/:graph_id
   Pull filtered entities        ↓
   from Zep graph             SimulationWorkspaceView → GraphPanel (D3)

4. Simulation Prepare         POST /api/v1/simulation/prepare/:graph_id
   Generate OASIS agent          ↓
   profiles + config          LLM generates personas, timing, events

5. Simulation Start           POST /api/v1/simulation/start
   Spawn OASIS subprocess        ↓ returns simulation_id
   (Twitter/Reddit agents)    Poll GET /api/v1/simulation/status/:id (3s interval)
                                 ↓

6. Simulation Running         Actions collected via file-based IPC
   Agents post, like,            ↓
   reply, follow              SimulationPanel + SentimentTimeline (D3)

7. Simulation Complete        Status → COMPLETED
                                 ↓

8. Report Generation          POST /api/v1/report/generate
   ReACT agent queries Zep       ↓ returns task_id + report_id
   graph with search tools    Poll GET /api/v1/report/generate/status/:id (5s interval)
                                 ↓

9. Report Display             GET /api/v1/report/:id
   Multi-chapter markdown        ↓
   + D3 charts                ReportView → ReportCharts (D3)

10. Interactive Chat          POST /api/v1/report/chat
    Follow-up questions          ↓
    answered by report agent  ChatView (streaming tool call visualization)
```

### State Management Flow

```
API responses
    ↓
Pinia stores (40 stores — simulation, scenarios, settings, auth, etc.)
    ↓
Composables (useSimulationPolling fetches + updates stores)
    ↓
provide/inject (SimulationWorkspaceView provides polling context)
    ↓
Components (GraphPanel, SimulationPanel consume via inject)
```

### Request Flow

```
Frontend (Axios client)
    ↓ CSRF token from cookie → X-CSRFToken header
    ↓ Bearer token from localStorage → Authorization header
    ↓ Request deduplication (concurrent identical GETs)
    ↓
Backend (Flask)
    ↓ JWT middleware → g.user
    ↓ Rate limiter check
    ↓ CSRF validation (state-changing requests)
    ↓ Blueprint route handler
    ↓   → Service layer (business logic)
    ↓   → LLM Client / Zep Client / OASIS IPC
    ↓ Graceful degradation → demo data fallback
    ↓
Response
    ↓ Security headers injected
    ↓ GZIP compressed
    ↓ CSRF cookie refreshed
    ↓
Frontend
    ↓ Error normalization interceptor
    ↓ Performance timing recorded
    ↓ Pinia store updated
    ↓ Reactive UI re-renders
```

## Simulation Engine

### OASIS Integration

The simulation uses [OASIS](https://github.com/camel-ai/oasis) (built on CAMEL-AI) to run multi-agent social media simulations:

1. **Profile Generation** — Zep graph entities → LLM-enriched personas → OASIS agent profiles (Twitter/Reddit format)
2. **Config Generation** — LLM analyzes scenario + entities → timing, activity levels, events, platform-specific action probabilities
3. **Subprocess Execution** — `SimulationRunner` spawns OASIS as a subprocess with platform detection (Windows/Unix)
4. **IPC** — File-based command/response protocol (`commands/` and `responses/` directories) for real-time action collection and agent interviews

### Agent Actions

Each round produces `AgentAction` records:

```
round_num, timestamp, platform (twitter/reddit),
agent_id, agent_name, action_type, action_args, result, success
```

Action types: `CREATE_POST`, `LIKE_POST`, `REPOST`, `FOLLOW`, `DO_NOTHING`, `QUOTE_POST` (Twitter); `CREATE_POST`, `CREATE_COMMENT`, `LIKE_POST`, `DISLIKE_POST`, `SEARCH_POSTS`, `SEARCH_USER`, `TREND`, `REFRESH`, `FOLLOW`, `MUTE` (Reddit).

### Runner Status Lifecycle

```
IDLE → STARTING → RUNNING → COMPLETED
                     ↓          ↓
                  PAUSED     FAILED
                     ↓
                  STOPPING → STOPPED
```

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
# docker-compose.yml (3 services)
services:
  backend:
    build: ./backend
    ports: ["${BACKEND_PORT:-5001}:5001"]
    volumes: [sim_data:/app/uploads]
    healthcheck: GET http://localhost:5001/health (5s interval, 5 retries)
    stop_grace_period: 15s
    restart: unless-stopped

  frontend:
    build: ./frontend
    args: [VITE_API_URL=http://backend:5001/api]
    ports: ["${FRONTEND_PORT:-3000}:3000"]
    depends_on: backend (service_healthy)
    restart: unless-stopped

  nginx:                          # production profile only
    image: nginx:alpine
    ports: ["80:80"]
    depends_on: [backend, frontend]
    healthcheck: GET http://localhost:80/api/health
```

- **Backend Dockerfile** — `python:3.11-slim`, `pip install` from `requirements.txt`, exec form CMD for SIGTERM handling
- **Frontend Dockerfile** — Multi-stage: `node:20-slim` builds with pnpm (`--frozen-lockfile`), runtime serves `dist/` with `serve -s` (SPA mode)
- Named volume `sim_data` persists simulation data across restarts

### Railway

Both services deployed to Railway project `gtm-mirofish-demo`:
- Backend: `https://backend-production-e9d7.up.railway.app`
- Frontend: `https://frontend-production-86ea.up.railway.app`
- No explicit Railway config files — auto-detected from Dockerfiles

### Demo Mode

When `VITE_DEMO_MODE=true` or no LLM key is configured:
- Frontend generates synthetic agent actions and timeline data via `useDemoMode` / `useDemoPreset` composables
- Backend `ServiceHealthTracker` detects unavailable services → `@graceful_degradation` decorator returns mock data
- Data generators (`*_data_generator.py`) produce realistic demo data for all domain features
- All visualizations work with deterministic fallback data

### Graceful Shutdown

- Backend: `STOPSIGNAL SIGTERM` in Dockerfile → `SimulationRunner.register_cleanup()` terminates all OASIS subprocesses
- Health check returns `503` during shutdown for load balancer draining
- `stop_grace_period: 15s` allows in-flight requests to complete

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **OpenAI SDK for all providers** | Single client wraps Anthropic/OpenAI/Gemini via base URL routing — no provider-specific code in business logic |
| **File-based IPC** | OASIS runs as a subprocess; filesystem commands/responses avoid socket complexity and survive process restarts |
| **In-memory state + file persistence** | No database dependency — `TaskManager` and `ProjectManager` use dicts + JSON files in `uploads/` |
| **Circuit breaker (graceful degradation)** | Auto-detects LLM/Zep failures, short-circuits to mock data, retries after 120s recovery interval |
| **CSRF cookie + header pattern** | SPA-friendly: backend sets CSRF token in cookie, frontend reads and sends as `X-CSRFToken` header |
| **Request deduplication** | Concurrent identical GET requests share a single network call, preventing redundant API traffic from reactive re-renders |
| **provide/inject for polling** | `SimulationWorkspaceView` provides polling composable to child components, avoiding prop drilling through tab structure |
| **localStorage for session history** | Simulation runs persist across browser sessions without backend state; auto-cleanup prevents unbounded growth |
| **Lazy-loaded routes** | All views are lazy-loaded via dynamic `import()` for fast initial page load |
| **Demo mode fallback** | Network errors trigger `isDemoFallback` in polling composable, ensuring the app always has something to show |
| **Zep Cloud for graph memory** | Temporal knowledge graph with built-in RAG — entities and relationships extracted from seed text without custom graph DB |
| **Data generators for every domain** | Each feature area (CPQ, revenue, pipeline, etc.) has dedicated mock data generators ensuring demo mode parity |
| **Security headers by default** | HSTS, CSP, X-Frame-Options, etc. applied to all responses via middleware |
| **Rate limiting** | Token bucket per IP with stricter limits for LLM-calling routes (10/min vs 60/min) |

## Dependencies

### Backend
| Package | Purpose |
|---------|---------|
| `flask`, `flask-cors`, `flask-compress`, `flask-wtf` | Web framework, CORS, compression, CSRF |
| `openai` | LLM API client (all providers via base URL) |
| `anthropic` | Optional direct Anthropic client |
| `zep-cloud` | Knowledge graph + RAG |
| `camel-ai`, `camel-oasis` | Multi-agent simulation framework |
| `PyJWT` | JWT authentication |
| `PyMuPDF` | PDF text extraction |
| `python-dotenv` | Environment variable loading |
| `pydantic` | Data validation |

### Frontend
| Package | Purpose |
|---------|---------|
| `vue` (3.x), `vue-router`, `pinia` | UI framework + routing + state |
| `vue-i18n` | Internationalization |
| `d3` (7.x) | Data visualizations (19+ chart types) |
| `axios` | HTTP client with dedup + interceptors |
| `marked` | Markdown rendering |
| `@tailwindcss/vite` | Tailwind CSS v4 build plugin |

## Architecture Decision Records

Detailed ADRs are maintained in `docs/adr/`:

| ADR | Decision |
|-----|----------|
| 001 | Multi-LLM provider abstraction via OpenAI SDK |
| 001 | Vue 3 framework selection |
| 002 | Flask backend architecture |
| 002 | Vue 3 Composition API with Pinia |
| 003 | D3.js for visualizations |
| 003 | Intercom design token system |
| 004 | Async task-based simulation |
| 004 | LLM integration patterns |
| 005 | Demo architecture |
| 005 | Lightweight demo mode Docker |
| 006 | Optional OAuth domain enforcement |
