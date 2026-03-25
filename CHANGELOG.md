# Changelog

All notable changes to the GTM MiroFish Demo project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

#### Core Platform
- Vue 3 + Vite + Tailwind frontend with Intercom branding (#2068FF blue, #050505 navy)
- Flask backend with Blueprint-based API architecture
- Multi-LLM provider support (Anthropic Claude, OpenAI, Google Gemini) via `LLM_PROVIDER` env var
- Demo/mock mode for all endpoints when no LLM key is configured
- Docker Compose local development setup with per-service Dockerfiles
- Railway deployment configuration for backend and frontend services

#### GTM Simulation Engine
- OASIS swarm intelligence simulation orchestrator with LLM-driven agents
- Agent factory for creating simulation agents from GTM persona archetypes
- Agent prompt engineering module for OASIS simulation agents
- Interaction protocol service for agent-to-agent communication
- Environment manager for simulation lifecycle
- OASIS metrics collector with backend API and frontend display
- Simulation execution engine for in-memory LLM-driven GTM simulations
- Real-time simulation progress via Server-Sent Events (SSE)
- Simulation state manager composable with finite state machine
- Simulation controls panel with start/stop and configuration
- Simulation scenario templates service with 6 pre-built GTM demo scenarios
- Simulation replay viewer and comparison (side-by-side analysis)
- Simulation result caching for offline replay
- Simulation presets (quick configs) in ScenarioBuilderView
- AI narration mode during simulation
- Deterministic agent avatar generation from persona data

#### Knowledge Graph
- Zep Cloud SDK integration for knowledge graph operations
- Zep-powered knowledge graph API with 6 endpoints
- Entity extraction service for simulation interactions
- Graph memory service for knowledge graph operations
- Interactive D3.js force-directed knowledge graph visualization
- Community detection visualization with clustered graph
- Temporal knowledge timeline component
- Graph search interface component
- Standalone Knowledge Graph visualization view

#### Agent Memory System
- Agent memory abstraction layer with Zep/in-memory backends
- Temporal memory service with Zep integration
- Cross-simulation memory transfer system
- Memory persistence API endpoints
- Memory configuration panel for agent memory behavior
- Agent memory viewer component with D3 visualization
- Agent knowledge graph component
- Memory diff visualization feature

#### Report Generation
- ReportAgent engine with ReACT pattern for autonomous report generation
- GTM tool definitions and execution handlers for report generation
- Report generation wizard with template selection
- Multi-format report export (HTML, PDF, JSON)
- Intercom-branded PDF export endpoint
- Report comparison view with side-by-side chapter navigation
- Executive summary one-pager generation
- Report annotations/notes per chapter
- Shareable report URLs with 24-hour expiring tokens
- Report sharing component with share link generation
- Pre-built report templates with template selector UI
- ToolCallLog component for ReportAgent reasoning transparency
- Interactive data tables with sorting, filtering, and pagination
- 95% confidence intervals on simulation metrics and report charts
- Print-optimized report styles

#### Data Visualizations (D3.js v7)
- Agent sentiment timeline visualization
- Geographic engagement heatmap with world map
- Treemap visualization for topic distribution
- Sankey diagram for agent journey visualization
- Agent influence network force-directed graph
- Word cloud visualization from agent posts
- Engagement heatmap visualization
- Competitive mention tracking visualization
- Decision journey funnel visualization
- Sparkline mini-charts for metric cards
- Chart export buttons (PNG/SVG)
- Scatter and horizontal bar chart types
- Hover tooltips and click-to-drill on all charts
- Chart entrance animations with staggered D3 transitions
- D3 rendering performance monitoring
- Count-up animations for SimulationPanel metrics

#### GTM Data Modules
- **Pipeline Analytics** — funnel visualization, waterfall chart, velocity heatmap, forecast, conversion trends
- **Revenue Analytics** — MRR waterfall, ARR trends, cohort retention heatmap, customer revenue treemap, churn analysis
- **Order-to-Cash** — order timeline, flow Sankey diagram, billing overview, provisioning status, order validation
- **GTM Dashboard** — command center layout with executive KPIs, health scorecard, activity feed, revenue pipeline chart, deal velocity gauge, top accounts table, recent deals ticker
- **Data Pipeline Monitor** — dbt DAG visualization (D3 + dagre), connector health cards, sync timeline, data freshness monitor, sync error log
- **MRR Reconciliation** — three-way comparison table, source comparison Venn diagram, reconciliation trend chart, discrepancy distribution, resolution workflow
- **Salesforce CRM Data** — overview dashboard with stat cards, lead funnel, opportunity pipeline Kanban, account cards
- **CPQ (Configure, Price, Quote)** — product catalog, quote management, discount analysis scatter plot
- **Analytics View** — InsightCards sidebar, AI analyst chat bubble, segment performance, cohort analysis, attribution analysis
- **Predictive Analytics** — forecasts, goal tracking with bullet charts, anomaly detection dashboard

#### Agent Interaction
- LLM-backed chat and interview system
- SSE streaming chat with progressive token rendering
- Streaming interview responses in AgentProfileView
- Agent click-through panel with full profile view
- Batch interview mode to ask all agents simultaneously
- Suggested interview questions per persona
- Interview and chat export as markdown
- Agent comparison view (side-by-side for 2-3 agents)
- Animated engagement timeline replay component

#### Authentication & Authorization
- JWT auth middleware with `auth_required` and `auth_optional` decorators
- OAuth flow endpoints (Google + Okta OIDC)
- Session management (backend model + API, frontend store + composable)
- Auth guards on Vue Router with route meta and navigation guard
- Login page Vue component with auth guard
- UserMenu component in navbar
- Role-based access control model with role hierarchy
- Permission checking middleware with decorators
- User management API with CRUD endpoints and frontend component
- Role indicators in UI with permission-aware API responses
- Audit logging for role changes

#### Security
- Security headers middleware (Flask backend)
- API key authentication middleware with server-side persistence
- CSRF protection with Flask-WTF and double-submit cookie pattern
- Rate limiting on all API endpoints using Flask-Limiter
- Comprehensive audit log with full-stack implementation
- CORS explicit origin allowlist (replaced wildcard)
- Environment validation on startup

#### Real-Time Features
- Flask-SocketIO backend for real-time simulation updates
- WebSocket composable with socket.io-client
- WebSocket authentication with token-based connect validation
- WebSocket connection status indicator
- Real-time event emitter service
- WebSocket event handlers for simulation updates
- Connected data views and simulation to WebSocket push updates

#### Offline Support
- Service worker for caching static assets and API responses
- IndexedDB offline data store with idb wrapper
- OfflineBanner component for connectivity feedback
- Offline support in Pinia stores
- Background sync queue for offline change replay
- Offline-first report viewing with IndexedDB caching
- useOfflineMode composable for offline detection

#### Performance Optimization
- Route-based code splitting for all views
- Component lazy loading for heavy Vue components
- Request deduplication in API client
- Client-side performance monitoring
- API response caching (backend + frontend)
- Data pagination for large lists
- API request batching to reduce HTTP overhead during polling
- Image and asset lazy loading with IntersectionObserver
- Vite build optimization with vendor chunk splitting
- Resource preloading hints
- D3 tree-shaking with sub-package imports
- CSS cleanup: removed ~60 unused custom properties and 5 dead animation blocks
- Build-time optimization checks as postbuild script
- GZIP compression middleware via flask-compress
- ETag caching for GTM scenario data endpoints

#### Theming & Branding
- Theme data model with 4 default themes (Intercom, Dark, Corporate, Minimal)
- Theme persistence and system preference detection
- ThemeSwitcher component with navbar integration
- Custom theme editor with live preview
- Dark mode toggle and theme-aware chart colors
- CSS custom properties replacing all hardcoded colors
- High contrast mode with independent toggle
- Intercom design tokens in Tailwind config and brand-tokens.css

#### UX Enhancements
- Keyboard shortcut system with useKeyboardShortcuts composable
- G-prefix navigation shortcuts and view-specific shortcuts
- Keyboard shortcuts help modal and quick reference card
- Ctrl+K command palette for quick navigation and actions
- Drag-and-drop reordering (dashboard cards, report sections, navigation, graph nodes, team composer)
- useDragAndDrop composable with drag source, drop target, and sortable
- Breadcrumb navigation across all views
- Notification center with persistent history
- Focus management for modals with useFocusTrap composable
- Skeleton loading states replacing spinners
- Rich text editor (Tiptap) for scenario descriptions, agent backstories, report text, and annotations
- Auto-save in ScenarioBuilderView editor
- MarkdownEditor component with import/export and preview
- Onboarding tour for first-time visitors
- One-click quick-start demo flow
- Guided tour walkthrough for new users

#### Animations & Transitions
- Animation utility library with Web Animations API
- Direction-aware page transitions with route-depth awareness
- Card hover and interaction animations
- Loading skeleton components for content-aware states
- Button and form interaction animations
- List item stagger animations via useStaggerAnimation composable
- Modal and panel transition animations
- Notification and toast animations
- Parallax hero scroll effect on landing page

#### Observability & Monitoring
- Structured logging throughout the app
- Backend health monitoring service with health dashboard in Settings
- Startup diagnostics service with pre-flight checks
- Frontend error tracking service with backend logging endpoint
- ErrorBoundary component for Vue rendering errors
- Request/response logging middleware with request IDs and timing
- Token usage tracking and display in SettingsView
- Performance benchmark pages for API response time and page load tracking

#### Testing
- **E2E (Playwright):** Landing page, navigation, scenario creation, simulation launch, GTM dashboard, agent management, report generation, settings, data views
- **API Integration:** Simulation endpoints (79 tests), report and GTM template endpoints, auth endpoints, GTM data endpoints (42 tests), demo_app.py (100 tests)
- **Unit (Backend):** Comprehensive backend service tests (118 tests)
- **Unit (Frontend):** Pinia stores, simulation components, chart components
- **Visual Regression:** Baseline screenshots for all 8 views

#### Accessibility
- ARIA roles, labels, and landmarks across frontend
- Keyboard navigation support for all interactive elements
- Comprehensive accessibility audit pass

#### Documentation
- Architecture Decision Records (ADRs) for 6 key decisions
- Architecture documentation covering system design, data flow, and key decisions
- API documentation page
- Deployment documentation for all deployment targets
- Troubleshooting FAQ
- Marp presentation slides for GTM demo
- Demo script document for live presentations
- Demo data preset for curated presentation mode
- Interactive tutorial system with spotlight tour, guided walkthrough, and contextual help

#### Configuration & Settings
- LLM temperature slider and model selection in SettingsView
- Import/export settings as JSON
- Custom persona type creation with CRUD endpoints
- Inline validation feedback for API key fields
- Screenshot-ready presentation mode
- Pydantic request validation for all POST endpoints

### Changed
- Refactored config.py to class-based hierarchy with environment-aware selection
- Consolidated demo_app.py routes into Flask Blueprints
- Replaced barrel D3 import with sub-packages for explicit dependency tracking
- Expanded agent action content from 19 to 64 unique templates
- Expanded landing page into full scrollable experience with 13 sections and footer
- Consolidated report navigation and routing under /reports namespace
- Added API versioning with /api/v1/ prefix to all endpoints

### Fixed
- Simulations not appearing when user navigates away early
- CTA button scroll behavior and global cursor-pointer for interactive elements
- Chart rendering issues and bold findings formatting
- Railway deploy configuration (railway.toml, auth env vars)
- CLAUDE.md documentation drift (view count, package manager, API routes, Tailwind config reference)
