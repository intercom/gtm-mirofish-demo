# Changelog

All notable changes to the GTM MiroFish Demo project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## March 30, 2026

### New

- **Interactive Tutorial System** — First-time visitors get a guided spotlight tour, contextual help tooltips, and a walkthrough overlay to learn the platform step-by-step.
- **Keyboard Shortcut Quick Reference** — Press `?` to see a comprehensive reference card for all available shortcuts.
- **Performance Benchmarks** — New benchmark pages show API response times and frontend page load metrics with D3 visualizations.
- **Dynamic API Documentation** — Browse all API endpoints from an auto-discovered documentation page with live route details.
- **Demo Data Preset** — One-click demo data wiring for curated presentation mode directly in the Flask backend.

### Improved

- **Accessibility** — Comprehensive audit pass with ARIA roles, labels, and landmarks across all frontend components.
- **Architecture Documentation** — Updated docs reflecting current codebase, plus consolidated Architecture Decision Records (ADRs) and Zep Cloud + Railway deployment records.
- **Demo Script** — Updated with current features, all 6 scenarios, and deployment info.

### Fixed

- Resolved build errors across frontend and backend from parallel agent merges.

### Testing

- **E2E (Playwright):** Landing page, navigation, scenario creation, simulation launch, GTM dashboard, agent management, settings, report generation, and data view tests.
- **API Integration:** Simulation endpoints, report/GTM template endpoints, auth endpoints (41 tests), GTM data endpoints.
- **Unit (Frontend):** 10 simulation components (153 tests), 17 Pinia stores (368 tests), all 11 chart components.
- **Unit (Backend):** 6 backend services (145 tests).
- **Visual Regression:** Baseline screenshots captured for 17 pages.

---

## March 27, 2026

### New

- **Custom Theme Engine** — Choose from 4 built-in themes (Intercom, Dark, Corporate, Minimal) or create your own with a live-preview theme editor. Dark mode is now fully supported across all views.
- **Rich Text Editing** — Scenario descriptions, agent backstories, report annotations, and notes now use a Tiptap-powered rich text editor with markdown import/export and auto-save.
- **Keyboard Shortcuts** — Navigate with `G`-prefix shortcuts, use view-specific shortcuts in the report builder and dashboard, and see indicator badges in the command palette and workspace tabs.
- **Drag-and-Drop Everywhere** — Reorder dashboard widgets, report sections, navigation items, graph nodes, and team compositions with drag-and-drop (including touch support).
- **Animation System** — Smooth page transitions, card hover effects, skeleton loading states, chart entrance animations, staggered list reveals, modal transitions, and toast notifications.
- **Real-Time WebSocket Updates** — Simulation data streams live via Flask-SocketIO with a connection status indicator, JWT authentication, and automatic SSE fallback.
- **Offline Support** — Service worker caches static assets and API responses. IndexedDB stores data for offline viewing. Background sync replays queued changes when you're back online.
- **Authentication & Authorization** — OAuth login (Google + Okta), JWT session management, route-level auth guards, role-based access control, user management with admin UI, and audit logging for role changes.
- **API Key Management** — Generate and manage API keys with file-based persistence, auth middleware, and a frontend management component.
- **CSRF Protection** — Double-submit cookie pattern with Flask-WTF across all POST endpoints.
- **Audit Log System** — Full-stack audit logging with a dedicated viewer component for tracking all system changes.
- **System Health Dashboard** — Monitor backend service health, startup diagnostics, and structured JSON logging from the Settings page.
- **Error Boundary** — Vue rendering errors are caught gracefully with accessible fallback UI and backend error tracking.

### Improved

- **Performance** — Route-based code splitting, component lazy loading, image lazy loading with IntersectionObserver, API response caching, request deduplication, client-side pagination, Vite vendor chunk splitting, D3 tree-shaking with sub-package imports, and resource preloading hints.
- **Security** — Security headers middleware, explicit CORS origin allowlist, rate limiting on all API endpoints, and environment-aware settings with `APP_ENV`.
- **Deployment** — Hardened Railway configuration, docker-compose production profile, and updated deployment guide with nginx proxy setup.
- **CSS Cleanup** — Removed ~60 unused custom properties and 5 dead animation blocks. All hardcoded colors replaced with CSS theme tokens.

### Fixed

- Resolved build errors from parallel overnight agent merges.
- Fixed remaining hardcoded color values in LiveFeed and PersonalityRadar components.
- Corrected rate limiting paths and auth tier for all API endpoints.

---

## March 25–26, 2026

### New

- **Agent Intelligence** — Agents now have belief systems, personality dynamics with trait evolution, sentiment engines, long-term memory consolidation, and memory-augmented prompt building. Watch relationships evolve with animated network visualizations.
- **Coalition Detection** — Automatic coalition detection algorithm with D3 force-directed visualization, evolution timeline, consensus tracking, polarization gauge, and swing-agent profiles.
- **Behavior Prediction** — Markov chain-based agent behavior prediction model with anomaly detection, influence flow charts, and what-if prediction panels.
- **Reasoning Transparency** — See how agents think with reasoning trace viewer, decision tree visualization, argument maps, counterfactual comparison, and a transparency toggle in the live feed.
- **Agent Creation Wizard** — Build custom agents step-by-step: basic info, personality vector configuration, expertise selection, and live preview before saving.
- **Structured Debates** — Set up formal debates between agents with topic configuration, orchestration engine, scoring system, and scorecard visualization.
- **Scenario Marketplace** — Browse, preview, rate, and import/export from a catalog of 10+ GTM scenario templates with category filtering and usage tracking.
- **Campaign Analytics** — ROI comparison charts, spend allocation treemaps, attribution model comparison, and a cost modeling calculator across 15 realistic GTM campaigns.
- **What-If Analysis** — Explore parameter sensitivity with tornado charts, parameter sweep visualizations, variant comparison grids, and a full analysis engine.
- **Scenario Branching** — Fork simulations at decision points, visualize branch trees, compare branches side-by-side, and get merge/recommendation insights.
- **Multi-Scenario Dashboard** — Compare simulations across a calendar view, scenario performance leaderboard, cross-scenario trend charts, and outcome distribution bubble charts.
- **A/B Scenario Comparison** — Side-by-side comparison layout with radar charts, comparison tables, timeline overlays, and comparative chart overlays.
- **Charts Gallery** — 8 new advanced D3 chart types: Sunburst, Chord Diagram, Parallel Coordinates, Bullet Chart, Radar, Calendar Heatmap, Stream Graph, and Small Multiples.
- **Network Analysis View** — Agent interaction graphs, centrality analysis, cluster visualization, communication pattern timeline, adjacency matrix heatmap, and information flow diagrams.
- **Animated Visualizations** — Revenue waterfall, pipeline flow, org chart, Sankey flow, deal lifecycle, and counter animations powered by a reusable flow animation engine.
- **Dashboard Builder** — Drag-and-drop widget grid with 9 widget types (KPI cards, charts, tables, text), persistence API, and a widget picker panel.
- **Timeline Scrubber** — Navigate simulation rounds with a scrubber bar, snapshot comparisons, event markers, multi-metric synchronized views, and timeline annotations.
- **Navigation Enhancements** — Mini-map showing workflow progress, global activity feed, system status bar, and enhanced command palette.

### Improved

- **GTM Data Modules** — Expanded Salesforce CRM (account detail view, opportunity pipeline, lead funnel), CPQ (quote management fixes, discount analysis), and data pipeline monitoring with full-stack integration and test coverage.
- **Landing Page** — Scenario template gallery cards integrated into landing page for easy discovery.

### Fixed

- Resolved merge conflicts and broken imports from parallel PRD agent work.
- Fixed Salesforce Pinia store response parsing and demo fallback.
- Fixed CPQ API client URL paths to match baseURL convention.
- Fixed OG meta image URLs to use absolute paths for social sharing.

---

## March 24, 2026

### New

- **GTM Dashboard** — Command center layout with executive KPIs, health scorecard, activity feed, revenue pipeline chart, deal velocity gauge, top accounts table, and recent deals ticker.
- **Pipeline Analytics** — Funnel visualization, waterfall chart, velocity heatmap, forecast view, and conversion trends for your GTM pipeline.
- **Revenue Analytics** — MRR waterfall, ARR trends, cohort retention heatmap, customer revenue treemap, and churn analysis with D3 visualizations.
- **Order-to-Cash** — Order timeline, flow Sankey diagram, billing overview, provisioning status dashboard, and order validation panel.
- **Data Pipeline Monitor** — dbt DAG visualization (D3 + dagre), connector health cards, sync timeline, data freshness monitor, and sync error log.
- **MRR Reconciliation** — Three-way comparison table, source comparison Venn diagram, reconciliation trend chart, discrepancy distribution, and resolution workflow.
- **Salesforce CRM Data** — Overview dashboard with stat cards, lead funnel, opportunity pipeline Kanban, and account cards.
- **CPQ Module** — Product catalog browser, quote management, and discount analysis scatter plot.
- **Analytics View** — Insight cards sidebar, AI analyst chat bubble, segment performance, cohort analysis, and attribution analysis.
- **Predictive Analytics** — Forecast visualizations, goal tracking with bullet charts, and anomaly detection dashboard.
- **OASIS Simulation Engine** — Full OASIS integration with agent factory, interaction protocols, environment manager, metrics collector, and real-time SSE progress streaming. Includes simulation replay, comparison, presets, and AI narration mode.
- **Knowledge Graph** — Zep Cloud integration with entity extraction, community detection, temporal timeline, graph search, and interactive D3 force-directed visualization.
- **Agent Memory System** — Memory abstraction layer with Zep/in-memory backends, temporal memory, cross-simulation transfer, memory diff visualization, and configuration panel.
- **Report Engine** — ReACT-pattern ReportAgent with GTM tools, generation wizard, multi-format export (HTML, PDF, JSON, CSV), comparison view, executive summary generator, annotations, shareable URLs with 24-hour tokens, and confidence intervals on metrics.
- **LLM-Backed Chat** — Streaming chat and interview system with SSE progressive token rendering, batch interview mode, suggested questions per persona, and markdown export.
- **Data Visualizations** — Sentiment timeline, geographic heatmap, treemap, Sankey diagram, influence network, word cloud, engagement heatmap, competitive mentions, decision funnel, sparklines, and chart export (PNG/SVG).
- **Agent Profiles** — Deterministic avatar generation, agent comparison (side-by-side for 2–3 agents), and animated engagement timeline replay.
- **Simulation Workspace** — Split-panel layout with active/review modes, live metrics dashboard, live feed with SSE streaming, and persona customization with LLM-powered generation.
- **UX Features** — Breadcrumb navigation, Ctrl+K command palette, notification center, focus-trapped modals, skeleton loading states, ARIA labels, high contrast mode, print-optimized reports, guided tour, one-click quick-start, and screenshot-ready presentation mode.
- **Settings Enhancements** — LLM temperature slider, model selection, token usage display, import/export settings as JSON, custom persona CRUD, and inline API key validation.
- **Production Hardening** — Production Dockerfile with gunicorn, detailed health endpoint, environment validation, explicit CORS allowlist, docker-compose.production.yml, Gemini provider support, request logging middleware, and Pydantic validation for all POST endpoints.

### Improved

- Expanded landing page into a full scrollable experience with 13 sections and footer.
- Expanded agent action content from 19 to 64 unique templates for richer simulations.
- Refactored config.py to class-based hierarchy with environment-aware selection.
- Consolidated demo_app.py routes into Flask Blueprints.
- Standardized all API routes under `/api/v1/` prefix.
- Added API versioning, GZIP compression, ETag caching, and rate limiting.

### Fixed

- Fixed simulations not appearing when user navigates away early.
- Fixed CTA button scroll behavior and global cursor-pointer for interactive elements.
- Fixed chart rendering issues and bold findings formatting.

---

## March 23, 2026

### New

- **Initial Platform** — Vue 3 + Vite + Tailwind CSS v4 frontend with Intercom branding (primary blue `#2068FF`, navy `#050505`, orange `#ff5600`).
- **Flask Backend** — Blueprint-based API architecture with multi-LLM provider support (Anthropic Claude, OpenAI, Google Gemini) via `LLM_PROVIDER` environment variable.
- **Demo Mode** — All endpoints return mock data when no LLM key is configured, with frontend UI indicators showing demo status.
- **Docker Setup** — Per-service Dockerfiles for backend and frontend with docker-compose for local development.
- **Railway Deployment** — Both services deployed to Railway with cross-origin API routing and OG meta tags for social sharing.
- **Phase Navigation** — Tab-based workflow navigation (Build → Simulate → Report → Chat) integrated across Graph and Simulation views.
- **Intercom Fin.ai** — Fin widget integrated for in-app support and feedback.
- **Progressive Graph Build** — Knowledge graph builds incrementally with skeleton loading, shared simulation state, and session dashboard.
- **Unified Workspace** — Single workspace view combining graph, simulation, and report with persistent history.

### Fixed

- Fixed `fetchOne → fetchScenarioById` method name mismatch in ScenarioBuilderView.
- Fixed `startBuild → startGraphBuild` method name in ScenarioBuilderView.
- Fixed API routing for cross-origin Railway deployment.
- Fixed Railway deploy configuration with `railway.toml` and auth env vars in Dockerfile.
- Fixed graph contrast and enabled chat markdown rendering.
