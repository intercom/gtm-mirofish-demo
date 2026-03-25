#!/usr/bin/env python3
"""Generate 550+ tasks for MiroFish GTM Demo PRD extension (groups 15-95)."""
import json

NEW_TASKS = []

def t(group, title, desc):
    NEW_TASKS.append({"title": title, "completed": False, "parallel_group": group, "description": desc})

# ═══════════════════════════════════════════════════════
# GROUP 15: Foundation (1 task, runs SOLO first)
# ═══════════════════════════════════════════════════════
t(15, "Create comprehensive CLAUDE.md with project rules and architecture",
  "Create a CLAUDE.md file at the repository root that all Ralphy agents will read before starting any task. Include: "
  "1) Project overview — MiroFish GTM Demo is an Intercom-branded swarm intelligence simulation tool built with Vue 3 + Flask. "
  "2) Directory structure — frontend/ (Vue 3 + Vite + Tailwind + Pinia), backend/ (Flask + Blueprints in backend/app/api/, services in backend/app/services/, LLM client in backend/app/utils/llm_client.py). "
  "3) Development commands — `cd frontend && pnpm install && pnpm dev` for frontend, `cd backend && uv sync && uv run python run.py` for backend, `docker compose up -d` for full stack. "
  "4) Coding standards — Vue 3 Composition API with <script setup>, Tailwind CSS with brand tokens from frontend/src/assets/brand-tokens.css, Pinia stores in frontend/src/stores/, composables in frontend/src/composables/. "
  "5) Brand colors — primary blue #2068FF, navy #050505, fin orange #ff5600, accent purple #A0F, text #1a1a1a. "
  "6) Backend patterns — Flask Blueprints registered in backend/app/api/__init__.py, all routes under /api/ prefix, all LLM calls through backend/app/utils/llm_client.py which supports anthropic/openai/gemini providers. "
  "7) Environment variables — LLM_PROVIDER, LLM_API_KEY, ZEP_API_KEY (all optional, app works in demo/mock mode without them). "
  "8) Key rules — never hardcode API keys, always support demo/mock fallback when services unavailable, use pnpm (never npm), use D3.js v7 for visualizations, install via pnpm for frontend and pip for backend. "
  "9) Testing — frontend tests with Vitest (`cd frontend && pnpm test`), backend tests with pytest. "
  "10) API client pattern — use frontend/src/api/client.js baseURL pattern for all new API modules.")

# ═══════════════════════════════════════════════════════
# GROUP 16: Backend Refactor (6 tasks)
# ═══════════════════════════════════════════════════════
t(16, "Consolidate demo_app.py routes into Flask Blueprints",
  "The file backend/demo_app.py still contains route definitions that should be moved into the Blueprint structure under backend/app/api/. "
  "Audit demo_app.py for any routes not yet in Blueprints (health, scenarios, any legacy endpoints). Move each route to its appropriate Blueprint file "
  "(health.py for /api/health/*, gtm_scenarios.py for /api/scenarios/*, etc.). Update demo_app.py to only import and register Blueprints from backend/app/api/__init__.py. "
  "Ensure the app factory pattern works: `create_app()` in backend/app/__init__.py registers all Blueprints. "
  "After refactoring, demo_app.py should be a thin entry point that calls create_app() and runs the server. Verify all existing routes still work by checking each Blueprint's route list.")

t(16, "Create health Blueprint with /api/health and /api/health/detailed",
  "Create backend/app/api/health.py as a Flask Blueprint. Move health check routes from demo_app.py if they exist, or create new ones. "
  "GET /api/health — returns {status: 'ok', timestamp: ISO8601}. "
  "GET /api/health/detailed — returns comprehensive health: Flask status, LLM provider connectivity (test configured provider), Zep connection status (if ZEP_API_KEY set), "
  "memory usage, uptime, and version from frontend/package.json. Return top-level status: 'healthy' (all ok), 'degraded' (optional services down), 'unhealthy' (critical failure). "
  "Register Blueprint in backend/app/api/__init__.py with url_prefix='/api/health'.")

t(16, "Create shared backend utilities module",
  "Create backend/app/utils/shared.py with common utilities used across Blueprints: "
  "1) `json_response(data, status=200)` — standardized JSON response wrapper with CORS headers. "
  "2) `validate_required_fields(data, fields)` — request validation helper that returns 400 with specific missing field errors. "
  "3) `get_env_or_default(key, default=None)` — environment variable getter with type coercion. "
  "4) `demo_mode_active()` — returns True when LLM_API_KEY is not set (used for mock fallback). "
  "5) `rate_limit_key()` — generates rate limit key from request IP. "
  "Import and use these in existing Blueprints where applicable. Do not break existing functionality.")

t(16, "Add request logging middleware",
  "Create backend/app/middleware/request_logger.py with a Flask before_request/after_request middleware that logs: "
  "method, path, status code, response time in ms, and request ID (generate UUID per request). "
  "Use Python logging module with structured format: `[{timestamp}] {request_id} {method} {path} {status} {duration_ms}ms`. "
  "Register the middleware in the app factory (backend/app/__init__.py). Log to both console and backend/logs/ directory with daily rotation. "
  "Skip logging for /api/health endpoint to avoid noise.")

t(16, "Add CORS and error handling middleware",
  "Create backend/app/middleware/error_handler.py with global error handlers: "
  "400 (Bad Request) — returns {error: 'Bad Request', message: str(e)}. "
  "404 (Not Found) — returns {error: 'Not Found', path: request.path}. "
  "500 (Internal Server Error) — returns {error: 'Internal Server Error', request_id: g.request_id} and logs full traceback. "
  "Also create backend/app/middleware/cors.py that configures Flask-CORS with ALLOWED_ORIGINS from env (default '*' for dev). "
  "Register both in the app factory. Ensure all error responses are JSON, not HTML.")

t(16, "Create backend configuration management",
  "Refactor backend/app/config.py to use a class-based configuration pattern: "
  "BaseConfig (shared settings), DevelopmentConfig (debug=True, verbose logging), ProductionConfig (debug=False, strict CORS). "
  "Add all environment variables as class attributes with defaults: LLM_PROVIDER, LLM_API_KEY, LLM_MODEL_NAME, LLM_BASE_URL, ZEP_API_KEY, "
  "DEMO_SPEED, ALLOWED_ORIGINS, LOG_FILE, PORT, AUTH_ENABLED, SECRET_KEY. "
  "Add a `validate()` method that warns about missing optional vars and errors on invalid combinations (e.g., LLM_PROVIDER set but LLM_API_KEY missing). "
  "Use config class in app factory based on FLASK_ENV environment variable.")

# ═══════════════════════════════════════════════════════
# GROUP 17: Salesforce Object Simulation (10 tasks)
# ═══════════════════════════════════════════════════════
t(17, "Create Salesforce data models module",
  "Create backend/app/models/salesforce.py with Python dataclasses representing core Salesforce objects: "
  "Account (id, name, industry, arr, plan_tier, health_score, owner, created_date, renewal_date), "
  "Opportunity (id, name, account_id, stage, amount, close_date, probability, owner, type), "
  "Contact (id, first_name, last_name, email, account_id, title, role, last_activity), "
  "Lead (id, first_name, last_name, email, company, status, source, score, owner). "
  "Use realistic Intercom-relevant field names and types. Add `to_dict()` and `from_dict()` methods. "
  "Add factory methods `create_sample()` on each class that generates realistic demo data using random but deterministic values (seed-based).")

t(17, "Build Salesforce data generator service",
  "Create backend/app/services/sfdc_data_generator.py that generates realistic Salesforce demo data. "
  "Generate 50 Accounts with realistic B2B SaaS company names, industries (Technology, Finance, Healthcare, Retail, Education), "
  "ARR values ($10K-$500K), plan tiers (Essential, Advanced, Expert), health scores (1-100). "
  "For each Account, generate 1-3 Contacts with realistic names and titles (VP Sales, Director of CS, CTO, etc.). "
  "Generate 30 Opportunities across stages: Prospecting, Discovery, Proposal, Negotiation, Closed Won, Closed Lost. "
  "Generate 40 Leads with statuses: New, Contacted, Qualified (MQL), Converted, Disqualified. "
  "Use seed-based randomness so data is deterministic. Store generated data in memory with a module-level cache.")

t(17, "Create Salesforce API Blueprint",
  "Create backend/app/api/salesforce.py as a Flask Blueprint with endpoints: "
  "GET /api/salesforce/accounts — list accounts with pagination (?page=1&per_page=20) and filters (?industry=Technology&tier=Expert). "
  "GET /api/salesforce/accounts/<id> — single account with related contacts and opportunities. "
  "GET /api/salesforce/opportunities — list opportunities with stage filter and date range. "
  "GET /api/salesforce/contacts — list contacts with account filter. "
  "GET /api/salesforce/leads — list leads with status filter and source filter. "
  "GET /api/salesforce/stats — aggregate stats: total accounts, total ARR, avg health score, pipeline value, lead conversion rate. "
  "All endpoints return paginated JSON with {data: [...], total: N, page: N, per_page: N}. "
  "Register Blueprint in backend/app/api/__init__.py.")

t(17, "Build Account detail Vue component",
  "Create frontend/src/components/salesforce/AccountCard.vue — a card component showing Account details. "
  "Display: company name (large, bold), industry badge, plan tier badge (color-coded: Essential=gray, Advanced=blue, Expert=purple), "
  "ARR formatted as currency, health score as a colored progress bar (red <30, yellow 30-70, green >70), owner name, renewal date. "
  "Use Tailwind CSS with brand tokens. Add hover effect with subtle shadow transition. "
  "Accept account object as prop. Emit 'click' event for navigation. Use the card pattern from existing components in frontend/src/components/.")

t(17, "Build Opportunity pipeline Vue component",
  "Create frontend/src/components/salesforce/OpportunityPipeline.vue — a Kanban-style board showing opportunities by stage. "
  "Columns: Prospecting, Discovery, Proposal, Negotiation, Closed Won, Closed Lost. "
  "Each card shows: opportunity name, account name, amount (formatted currency), close date, probability percentage. "
  "Column headers show count and total value. Use drag-and-drop appearance (but read-only for now). "
  "Color-code columns: early stages in blue, late stages in green, Closed Lost in red. "
  "Use CSS Grid for column layout. Make responsive — stack columns vertically on mobile. "
  "Import from frontend/src/api/client.js for data fetching.")

t(17, "Build Lead funnel Vue component",
  "Create frontend/src/components/salesforce/LeadFunnel.vue — a funnel visualization using D3.js v7. "
  "Show lead progression: New → Contacted → MQL → SQL → Converted, with counts and percentages at each stage. "
  "Use a trapezoid/funnel shape where width represents volume at each stage. "
  "Color each stage with brand gradient (light blue at top to dark blue at bottom). "
  "Show conversion rate between each stage as a percentage label on the connecting segment. "
  "Add tooltip on hover showing exact count, percentage of total, and avg time in stage. "
  "Install D3 via `pnpm add d3` if not already installed. Use <script setup> with onMounted for D3 rendering.")

t(17, "Create Salesforce Pinia store",
  "Create frontend/src/stores/salesforce.js as a Pinia store managing Salesforce data state. "
  "State: accounts (array), opportunities (array), contacts (array), leads (array), stats (object), loading (boolean), error (string|null). "
  "Actions: fetchAccounts(filters), fetchOpportunities(filters), fetchContacts(accountId), fetchLeads(filters), fetchStats(). "
  "Getters: accountsByIndustry, opportunitiesByStage, leadsByStatus, totalPipelineValue, avgHealthScore. "
  "Use the API client pattern from frontend/src/api/client.js. Add error handling that sets error state. "
  "Follow the pattern of existing stores in frontend/src/stores/.")

t(17, "Create Salesforce API client module",
  "Create frontend/src/api/salesforce.js following the pattern in frontend/src/api/client.js. "
  "Export functions: getAccounts(params), getAccount(id), getOpportunities(params), getContacts(params), getLeads(params), getSalesforceStats(). "
  "Each function calls the corresponding backend endpoint and returns the response data. "
  "Add request/response interceptors for loading state. Handle 404 and 500 errors gracefully with user-friendly messages. "
  "Use the baseURL pattern from client.js.")

t(17, "Build Salesforce overview dashboard section",
  "Create frontend/src/components/salesforce/SalesforceOverview.vue — a dashboard section with 4 stat cards and 2 charts. "
  "Stat cards (top row, grid-cols-4): Total Accounts, Total ARR (formatted $X.XM), Avg Health Score (with color), Pipeline Value. "
  "Charts (bottom row, grid-cols-2): Industry breakdown donut chart (D3.js), Stage distribution bar chart (D3.js). "
  "Use the Salesforce Pinia store for data. Show loading skeletons while data fetches. "
  "Style stat cards with white background, subtle border, icon on left, value large and bold, label smaller and gray. "
  "Match the visual style of existing dashboard components in the project.")

t(17, "Create Salesforce data page/view",
  "Create frontend/src/views/SalesforceView.vue as a new page accessible from the main navigation. "
  "Layout: SalesforceOverview at top, then tabbed section below with tabs: Accounts (AccountCard grid), Pipeline (OpportunityPipeline), Leads (LeadFunnel). "
  "Add route in frontend/src/router/index.js: { path: '/salesforce', name: 'Salesforce', component: SalesforceView }. "
  "Add navigation item in frontend/src/components/layout/AppNav.vue with a building icon (use Heroicons or similar). "
  "On mount, call salesforceStore.fetchStats() and salesforceStore.fetchAccounts(). "
  "Add page title 'Salesforce CRM' with subtitle 'Simulated Salesforce data for GTM analysis'.")

# ═══════════════════════════════════════════════════════
# GROUP 18: CPQ Quote Simulation (10 tasks)
# ═══════════════════════════════════════════════════════
t(18, "Create CPQ data models",
  "Create backend/app/models/cpq.py with Python dataclasses: "
  "Product (id, name, code, family, unit_price, billing_frequency: monthly|annual, description, is_active), "
  "PriceBookEntry (id, product_id, list_price, currency, is_standard), "
  "Quote (id, opportunity_id, account_name, status: Draft|Review|Approved|Rejected, total_price, discount_pct, created_date, expiry_date), "
  "QuoteLine (id, quote_id, product_id, product_name, quantity, list_price, discount_pct, net_price, subscription_term_months). "
  "Use Intercom product names: Essential, Advanced, Expert plans, Fin AI Agent, Proactive Support, Help Center. "
  "Add factory methods for generating realistic demo quotes with 2-5 line items each.")

t(18, "Build CPQ data generator service",
  "Create backend/app/services/cpq_data_generator.py that generates realistic CPQ demo data. "
  "Create 6 Products matching Intercom tiers: Essential ($39/seat/mo), Advanced ($99/seat/mo), Expert ($139/seat/mo), "
  "Fin AI Agent ($0.99/resolution), Proactive Support ($499/mo add-on), Help Center (included with all plans). "
  "Generate 20 Quotes linked to Opportunities from sfdc_data_generator: mix of Draft (30%), In Review (20%), Approved (30%), Rejected (20%). "
  "Each quote has 2-5 QuoteLines with realistic seat counts (5-500), discount percentages (0-25%), "
  "and subscription terms (12 or 24 months). Calculate net prices correctly: list_price * quantity * (1 - discount_pct/100) * term_months. "
  "Use deterministic seed-based randomness.")

t(18, "Create CPQ API Blueprint",
  "Create backend/app/api/cpq.py as a Flask Blueprint with endpoints: "
  "GET /api/cpq/products — list all products with family filter. "
  "GET /api/cpq/quotes — list quotes with status filter and pagination. "
  "GET /api/cpq/quotes/<id> — single quote with all line items and calculated totals. "
  "GET /api/cpq/quotes/<id>/pdf-preview — returns HTML representation of a quote PDF. "
  "POST /api/cpq/quotes/<id>/approve — transitions quote from Review to Approved. "
  "POST /api/cpq/quotes/<id>/reject — transitions quote to Rejected with reason. "
  "GET /api/cpq/stats — aggregate: total quotes, approval rate, avg discount, avg deal size, revenue by product. "
  "Register in backend/app/api/__init__.py.")

t(18, "Build Quote detail Vue component",
  "Create frontend/src/components/cpq/QuoteDetail.vue — a detailed quote view. "
  "Header: Quote number, status badge (Draft=gray, Review=yellow, Approved=green, Rejected=red), account name, created/expiry dates. "
  "Line items table: Product, Quantity, List Price, Discount %, Net Price columns. "
  "Footer: Subtotal, Total Discount amount, Total Price (large, bold). "
  "Action buttons: Approve (green), Reject (red), Edit (blue) — only shown for appropriate statuses. "
  "Use a clean table layout with alternating row colors. Format all currency values with $ and commas.")

t(18, "Build Product catalog Vue component",
  "Create frontend/src/components/cpq/ProductCatalog.vue — a grid of product cards. "
  "Each card shows: product name, product family badge, unit price with billing frequency, brief description. "
  "Highlight the most popular product (Advanced) with a 'Most Popular' ribbon. "
  "Group products by family with section headers. Add a search/filter bar at top. "
  "Use the pricing card pattern: white card, subtle border, price in large brand-blue text. "
  "Make cards responsive: 3 columns on desktop, 2 on tablet, 1 on mobile.")

t(18, "Build Quote list Vue component",
  "Create frontend/src/components/cpq/QuoteList.vue — a table listing all quotes. "
  "Columns: Quote #, Account, Status (colored badge), Products (truncated list), Total, Created Date, Expiry. "
  "Add status filter chips at top (All, Draft, Review, Approved, Rejected) with count badges. "
  "Add sorting by clicking column headers (total, date). "
  "Rows are clickable — emit 'select' event with quote ID. Highlight expired quotes with a subtle red background. "
  "Add pagination at bottom with page size selector (10, 25, 50).")

t(18, "Create CPQ Pinia store",
  "Create frontend/src/stores/cpq.js as a Pinia store. "
  "State: products (array), quotes (array), selectedQuote (object|null), stats (object), loading, error. "
  "Actions: fetchProducts(), fetchQuotes(filters), fetchQuote(id), approveQuote(id), rejectQuote(id, reason), fetchCpqStats(). "
  "Getters: quotesByStatus, productsByFamily, totalPipelineValue, avgDiscount, approvalRate. "
  "Follow existing store patterns. Use the API client for all requests.")

t(18, "Create CPQ API client module",
  "Create frontend/src/api/cpq.js following the pattern in frontend/src/api/client.js. "
  "Export: getProducts(params), getQuotes(params), getQuote(id), approveQuote(id), rejectQuote(id, reason), getCpqStats(). "
  "Handle all error cases and return structured responses.")

t(18, "Build discount analysis D3 chart",
  "Create frontend/src/components/cpq/DiscountAnalysis.vue — a D3.js scatter plot showing discount patterns. "
  "X-axis: deal size (total quote value), Y-axis: discount percentage. "
  "Dot color: quote status (green=approved, red=rejected, gray=draft, yellow=review). "
  "Dot size: number of line items. Add trend line showing average discount by deal size range. "
  "Add tooltip on hover: quote #, account, total, discount %, status. "
  "Add reference lines at 10% and 20% discount thresholds with labels. "
  "Use D3.js v7 with <script setup> and onMounted lifecycle hook.")

t(18, "Create CPQ page/view",
  "Create frontend/src/views/CpqView.vue as a new page. "
  "Layout: CPQ stats row (4 cards: Total Quotes, Approval Rate, Avg Discount, Revenue), "
  "then tabbed section: Products (ProductCatalog), Quotes (QuoteList with QuoteDetail slide-over panel), Analytics (DiscountAnalysis). "
  "Add route: { path: '/cpq', name: 'CPQ', component: CpqView }. "
  "Add nav item in AppNav.vue with a calculator/receipt icon. "
  "Page title: 'Configure Price Quote' with subtitle 'Intercom product pricing and quote management simulation'.")

# ═══════════════════════════════════════════════════════
# GROUP 19: Pipeline/Funnel (10 tasks)
# ═══════════════════════════════════════════════════════
t(19, "Create pipeline stage data model",
  "Create backend/app/models/pipeline.py with dataclasses: "
  "PipelineStage (name, order, count, value, conversion_rate_to_next, avg_days_in_stage, color), "
  "FunnelSnapshot (timestamp, stages: list[PipelineStage], total_leads, total_revenue), "
  "ConversionEvent (id, entity_id, from_stage, to_stage, timestamp, duration_days, owner). "
  "Define the standard Intercom GTM funnel: Raw Lead → MQL → SQL → SAO → Proposal → Closed Won / Closed Lost. "
  "Include realistic conversion rates: Lead→MQL 25%, MQL→SQL 40%, SQL→SAO 60%, SAO→Proposal 70%, Proposal→Won 35%.")

t(19, "Build pipeline data generator service",
  "Create backend/app/services/pipeline_data_generator.py that generates 6 months of pipeline history. "
  "Generate monthly FunnelSnapshots with realistic progression: start with 1000 raw leads/month, "
  "apply conversion rates with ±10% random variance per month. Track cumulative metrics. "
  "Generate 200 ConversionEvents showing individual lead/opportunity movements through stages with timestamps. "
  "Include seasonal patterns: Q4 (Oct-Dec) gets 20% more leads, Q1 (Jan-Mar) has 10% lower conversion. "
  "Calculate velocity metrics: avg days per stage, total cycle time from Lead to Close.")

t(19, "Create pipeline API endpoints",
  "Add endpoints to backend/app/api/salesforce.py (or create backend/app/api/pipeline.py Blueprint): "
  "GET /api/pipeline/funnel — current funnel snapshot with all stages. "
  "GET /api/pipeline/funnel/history — monthly funnel snapshots for trend analysis (?months=6). "
  "GET /api/pipeline/conversions — conversion events with date range filter. "
  "GET /api/pipeline/velocity — stage-by-stage velocity metrics (avg days, median days). "
  "GET /api/pipeline/forecast — simple forecast based on current pipeline × probability. "
  "Register Blueprint if new file created.")

t(19, "Build funnel visualization D3 component",
  "Create frontend/src/components/pipeline/FunnelChart.vue — a horizontal funnel visualization using D3.js v7. "
  "Each stage rendered as a trapezoid, width proportional to count. Stages flow left to right. "
  "Between stages, show conversion rate as a percentage with an arrow. "
  "Color each stage with brand gradient (lightest blue at top/left to darkest at bottom/right). "
  "On hover, show tooltip: stage name, count, value ($), avg days, conversion rate. "
  "Add animation on mount — stages expand from zero width. Make responsive to container width.")

t(19, "Build conversion trend line chart",
  "Create frontend/src/components/pipeline/ConversionTrends.vue — a multi-line D3.js chart showing conversion rates over time. "
  "One line per stage transition (Lead→MQL, MQL→SQL, SQL→SAO, SAO→Proposal, Proposal→Won). "
  "X-axis: months, Y-axis: conversion rate (0-100%). Legend with toggleable lines. "
  "Add hover crosshair showing all values at that month. Use brand colors for each line. "
  "Show a horizontal dashed line for the overall average of each metric. "
  "Add annotation for notable changes (>5% change month-over-month).")

t(19, "Build pipeline velocity heatmap",
  "Create frontend/src/components/pipeline/VelocityHeatmap.vue — a heatmap showing time spent in each stage by month. "
  "Rows: pipeline stages. Columns: months. Cell color: green (fast) to red (slow) based on avg days relative to target. "
  "Target days per stage: Lead 7d, MQL 14d, SQL 21d, SAO 14d, Proposal 10d. "
  "Show exact day count in each cell. Add column totals showing total cycle time per month. "
  "Use D3.js color scale: d3.interpolateRdYlGn (reversed so green=fast). "
  "Add click handler on cells that could show individual deals in that stage/month.")

t(19, "Build pipeline forecast component",
  "Create frontend/src/components/pipeline/PipelineForecast.vue — shows revenue forecast based on current pipeline. "
  "Display a bar chart with two bars per stage: 'Weighted Value' (amount × probability) and 'Unweighted Value'. "
  "Show total forecast at top as a large number with confidence range (±15%). "
  "Add a simple time-based projection: expected close dates by stage, with a stacked area chart showing when deals might close. "
  "Include a 'Best Case / Expected / Worst Case' summary using 90th/50th/10th percentile scenarios.")

t(19, "Create pipeline Pinia store",
  "Create frontend/src/stores/pipeline.js as a Pinia store. "
  "State: funnelData, funnelHistory, conversions, velocity, forecast, loading, error. "
  "Actions: fetchFunnel(), fetchFunnelHistory(months), fetchConversions(dateRange), fetchVelocity(), fetchForecast(). "
  "Getters: overallConversionRate, avgCycleTime, totalPipelineValue, forecastedRevenue. "
  "Create frontend/src/api/pipeline.js with corresponding API client functions.")

t(19, "Build pipeline waterfall chart",
  "Create frontend/src/components/pipeline/PipelineWaterfall.vue — a D3.js waterfall chart showing how pipeline value changes. "
  "Start: Beginning pipeline value. Add: New opportunities. Subtract: Lost/disqualified. End: Current pipeline. "
  "Green bars for additions, red bars for subtractions, blue bars for running total. "
  "Show values on each bar. Add connector lines between bars. "
  "Monthly granularity with option to switch to weekly. Make responsive.")

t(19, "Create Pipeline analytics view",
  "Create frontend/src/views/PipelineView.vue as a dedicated pipeline analytics page. "
  "Layout: 4 KPI cards at top (Total Pipeline, Forecast Revenue, Avg Cycle Time, Overall Conversion Rate), "
  "then a 2-column grid: FunnelChart (left, full height), ConversionTrends (right top) + VelocityHeatmap (right bottom). "
  "Below: PipelineWaterfall (full width) and PipelineForecast (full width). "
  "Add route: { path: '/pipeline', name: 'Pipeline', component: PipelineView }. "
  "Add nav item in AppNav.vue with a chart-bar icon.")

# ═══════════════════════════════════════════════════════
# GROUP 20: Revenue Metrics (10 tasks)
# ═══════════════════════════════════════════════════════
t(20, "Create revenue data models",
  "Create backend/app/models/revenue.py with dataclasses: "
  "RevenueMetric (month, mrr, arr, new_mrr, expansion_mrr, contraction_mrr, churn_mrr, net_new_mrr), "
  "CustomerRevenue (account_id, account_name, mrr, plan, seats, usage_units, start_date, last_renewal), "
  "ChurnEvent (account_id, account_name, mrr_lost, reason, churn_date, was_voluntary), "
  "ExpansionEvent (account_id, account_name, previous_mrr, new_mrr, expansion_type: upsell|cross_sell|seat_add, date). "
  "Use realistic Intercom-scale numbers: total MRR ~$2M, 500 customers, avg $4K MRR.")

t(20, "Build revenue data generator service",
  "Create backend/app/services/revenue_data_generator.py generating 12 months of revenue history. "
  "Start at $1.8M MRR, grow to $2.2M over 12 months (22% YoY growth). "
  "Monthly breakdown: new business ~$80K, expansion ~$40K, contraction ~-$15K, churn ~-$30K, net new ~$75K. "
  "Generate 500 CustomerRevenue records with power-law distribution (few large, many small). "
  "Generate 60 ChurnEvents with reasons: budget cuts (30%), competitor (25%), not using (20%), merged/acquired (15%), other (10%). "
  "Generate 80 ExpansionEvents: seat additions (50%), plan upgrades (30%), add-on purchases (20%). "
  "All values with ±15% monthly variance for realism.")

t(20, "Create revenue API Blueprint",
  "Create backend/app/api/revenue.py as a Flask Blueprint: "
  "GET /api/revenue/metrics — monthly revenue metrics for last N months (?months=12). "
  "GET /api/revenue/customers — customer revenue list with sort/filter (plan, mrr range). "
  "GET /api/revenue/churn — churn events with date range and reason filters. "
  "GET /api/revenue/expansion — expansion events with type filter. "
  "GET /api/revenue/summary — top-level: current MRR, ARR, growth rate, net retention, gross retention, LTV, CAC. "
  "GET /api/revenue/cohort — cohort retention analysis by signup month. "
  "Register in backend/app/api/__init__.py.")

t(20, "Build MRR waterfall chart component",
  "Create frontend/src/components/revenue/MrrWaterfall.vue — D3.js waterfall chart showing MRR bridge. "
  "Bars: Starting MRR → +New → +Expansion → -Contraction → -Churn → Ending MRR. "
  "Green for positive (new, expansion), red for negative (contraction, churn), blue for totals. "
  "Show dollar values on each bar with proper formatting ($XXK). Add month selector to see different months. "
  "Animate bars on mount. Add connector lines between bars. Include net new MRR callout.")

t(20, "Build ARR trend chart component",
  "Create frontend/src/components/revenue/ArrTrend.vue — D3.js area chart showing ARR over time. "
  "Stacked areas: New business (dark blue), Expansion (light blue), with churn shown as a separate red line below. "
  "X-axis: months. Y-axis: ARR in $M. Add annotation for hitting milestones (e.g., '$2M ARR'). "
  "Show growth rate as a secondary Y-axis line. Add hover tooltip with full monthly breakdown. "
  "Include a subtle grid and clean axis labels.")

t(20, "Build cohort retention heatmap",
  "Create frontend/src/components/revenue/CohortRetention.vue — a heatmap table showing revenue retention by signup cohort. "
  "Rows: signup months (Jan-Dec). Columns: months since signup (0-11). "
  "Cell values: retention percentage (100% at month 0). Color: green (>100% = expansion) to red (<80% = high churn). "
  "Diagonal pattern showing natural retention decay. Add row averages on right, column averages at bottom. "
  "Use D3.js color scale. Add click handler to show cohort details.")

t(20, "Build churn analysis component",
  "Create frontend/src/components/revenue/ChurnAnalysis.vue — multi-chart view of churn patterns. "
  "Top: donut chart showing churn reasons distribution. "
  "Middle: line chart showing monthly churn rate trend (gross and net). "
  "Bottom: bar chart showing churn by plan tier (which plans churn most?). "
  "All charts use D3.js v7. Add a summary card showing: logo churn rate, revenue churn rate, avg churned MRR. "
  "Use red color palette for churn-related visuals.")

t(20, "Build customer revenue treemap",
  "Create frontend/src/components/revenue/CustomerTreemap.vue — D3.js treemap showing revenue distribution. "
  "Each rectangle is a customer, sized by MRR. Color by plan tier (Essential=gray, Advanced=blue, Expert=purple). "
  "Group by industry or plan tier (toggleable). Show company name and MRR on rectangles large enough. "
  "Add zoom interaction — click to zoom into a group. Add tooltip with full customer details. "
  "Highlight top 10 customers that make up majority of revenue (power law visualization).")

t(20, "Create revenue Pinia store and API client",
  "Create frontend/src/stores/revenue.js and frontend/src/api/revenue.js. "
  "Store state: metrics, customers, churnEvents, expansionEvents, summary, cohortData, loading, error. "
  "Actions: fetchMetrics(months), fetchCustomers(filters), fetchChurn(dateRange), fetchExpansion(dateRange), fetchSummary(), fetchCohort(). "
  "Getters: currentMrr, currentArr, growthRate, netRetention, grossRetention, avgMrr. "
  "API client: getRevenueMetrics, getCustomers, getChurnEvents, getExpansionEvents, getRevenueSummary, getCohortData.")

t(20, "Create Revenue analytics view",
  "Create frontend/src/views/RevenueView.vue as the revenue analytics page. "
  "Layout: 6 KPI cards (MRR, ARR, Growth Rate, Net Retention, Gross Retention, Avg Customer MRR). "
  "Two-column grid: ArrTrend (left), MrrWaterfall (right). "
  "Full-width: CohortRetention heatmap. "
  "Two-column: ChurnAnalysis (left), CustomerTreemap (right). "
  "Add route: { path: '/revenue', name: 'Revenue', component: RevenueView }. Nav item with currency-dollar icon.")

# ═══════════════════════════════════════════════════════
# GROUP 21: Order-to-Cash Flow (10 tasks)
# ═══════════════════════════════════════════════════════
t(21, "Create order-to-cash data models",
  "Create backend/app/models/order_to_cash.py with dataclasses: "
  "Order (id, quote_id, account_id, status: Pending|Validated|Provisioned|Active|Failed, total, line_items, created_date, activated_date), "
  "ProvisioningStep (order_id, step_name, status: pending|running|success|failed, started_at, completed_at, error_message), "
  "BillingRecord (id, order_id, account_id, amount, period_start, period_end, status: pending|invoiced|paid|overdue, invoice_number), "
  "ValidationResult (order_id, field, status: pass|fail|warning, message). "
  "Model the Intercom order flow: Quote Approved → Order Created → Validation → Provisioning → Billing → Active.")

t(21, "Build order-to-cash data generator",
  "Create backend/app/services/otc_data_generator.py generating realistic order-to-cash data. "
  "Generate 50 Orders linked to approved Quotes from cpq_data_generator. "
  "Each order goes through 5 ProvisioningSteps: license_validation, entitlement_setup, workspace_config, billing_setup, activation. "
  "95% of orders succeed fully. 3% fail at provisioning (show realistic errors). 2% have billing warnings. "
  "Generate BillingRecords: monthly invoices for each active order. 90% paid, 5% pending, 3% overdue, 2% failed. "
  "Generate ValidationResults: product compatibility checks, discount approval threshold checks, contract term validation. "
  "Timeline: orders take 1-3 days from creation to activation, billing starts next cycle.")

t(21, "Create order-to-cash API Blueprint",
  "Create backend/app/api/orders.py as a Flask Blueprint: "
  "GET /api/orders — list orders with status filter and pagination. "
  "GET /api/orders/<id> — single order with provisioning steps, validation results, billing records. "
  "GET /api/orders/<id>/timeline — chronological timeline of all events for this order. "
  "POST /api/orders/<id>/retry-provisioning — retry failed provisioning step. "
  "GET /api/billing — billing records with status filter and date range. "
  "GET /api/billing/summary — billing KPIs: total invoiced, total collected, collection rate, overdue amount. "
  "Register in backend/app/api/__init__.py.")

t(21, "Build order timeline Vue component",
  "Create frontend/src/components/orders/OrderTimeline.vue — a vertical timeline showing order lifecycle events. "
  "Each event: timestamp, event name, status icon (check=success, x=failed, spinner=running, clock=pending). "
  "Events: Order Created, Validation Started, Validation Complete, Provisioning Step 1-5, Billing Setup, Activation. "
  "Failed steps shown in red with error message. Success steps in green. Pending in gray. "
  "Add elapsed time between each step. Animate the timeline on mount — events appear sequentially. "
  "Use CSS timeline pattern with a vertical line and circular nodes.")

t(21, "Build provisioning status dashboard component",
  "Create frontend/src/components/orders/ProvisioningDashboard.vue — overview of all order provisioning. "
  "Top: 4 stat cards (Total Orders, Success Rate, Avg Provisioning Time, Failed Count). "
  "Middle: horizontal stacked bar chart showing orders by status (Pending, Validated, Provisioned, Active, Failed). "
  "Bottom: table of recent orders with status badges, sortable by date and status. "
  "Failed orders highlighted with red background and 'Retry' button. "
  "Auto-refresh indicator in top-right corner.")

t(21, "Build billing overview component",
  "Create frontend/src/components/orders/BillingOverview.vue — billing analytics dashboard. "
  "D3.js stacked bar chart: monthly billing by status (paid=green, pending=yellow, overdue=red, failed=gray). "
  "KPI cards: Collection Rate, Days Sales Outstanding (DSO), Total Invoiced MTD, Overdue Amount. "
  "Table: recent invoices with sortable columns (account, amount, status, due date, days overdue). "
  "Add aging chart: bar chart showing overdue amounts by age (0-30, 30-60, 60-90, 90+ days).")

t(21, "Build order validation component",
  "Create frontend/src/components/orders/ValidationPanel.vue — shows validation results for an order. "
  "List each validation check: field name, status (pass/fail/warning), message. "
  "Pass checks have green checkmark, fails have red X, warnings have yellow triangle. "
  "Group checks by category: Product Validation, Pricing Validation, Contract Validation, Compliance. "
  "Show overall validation status at top: 'All Checks Passed' (green) or 'X Issues Found' (red/yellow). "
  "Failed validations are expandable to show remediation steps.")

t(21, "Build order flow Sankey diagram",
  "Create frontend/src/components/orders/OrderFlowSankey.vue — D3.js Sankey diagram showing order flow. "
  "Nodes: Quote Approved → Order Created → Validation Pass/Fail → Provisioning Success/Fail → Billing Active/Failed. "
  "Link width proportional to order count. Color: green for success paths, red for failure paths. "
  "Show percentage on each link. Add tooltip with count and percentage on hover. "
  "Use d3-sankey plugin (install via pnpm if needed). Make responsive to container width.")

t(21, "Create order-to-cash Pinia store and API client",
  "Create frontend/src/stores/orders.js and frontend/src/api/orders.js. "
  "Store state: orders, selectedOrder, billingRecords, billingSummary, loading, error. "
  "Actions: fetchOrders(filters), fetchOrder(id), fetchOrderTimeline(id), retryProvisioning(id), fetchBilling(filters), fetchBillingSummary(). "
  "Getters: ordersByStatus, failedOrders, avgProvisioningTime, collectionRate. "
  "API client matching all backend endpoints.")

t(21, "Create Order-to-Cash view",
  "Create frontend/src/views/OrdersView.vue as the order-to-cash page. "
  "Layout: ProvisioningDashboard at top, then two-column: OrderFlowSankey (left), recent OrderTimeline (right, showing most recent order). "
  "Below: tabbed section — Orders (sortable table with slide-over detail panel showing OrderTimeline + ValidationPanel), Billing (BillingOverview). "
  "Add route: { path: '/orders', name: 'Orders', component: OrdersView }. Nav item with shopping-cart icon. "
  "Page title: 'Order to Cash' subtitle: 'End-to-end order lifecycle from quote to billing'.")

# ═══════════════════════════════════════════════════════
# GROUP 22: GTM Dashboard (10 tasks)
# ═══════════════════════════════════════════════════════
t(22, "Create GTM dashboard layout component",
  "Create frontend/src/components/dashboard/GtmDashboardLayout.vue — the main GTM dashboard container. "
  "Use CSS Grid with named areas: header (full width), kpis (full width row of cards), "
  "chart-left (2/3 width), chart-right (1/3 width), full-chart (full width), table (full width). "
  "Accept slots for each area so child components can be placed freely. "
  "Add a date range picker in the header that controls all dashboard data. "
  "Add a 'Last updated X seconds ago' indicator with auto-refresh toggle. "
  "Responsive: stack all sections vertically on mobile.")

t(22, "Build executive KPI row component",
  "Create frontend/src/components/dashboard/ExecutiveKpis.vue — a row of 8 KPI cards showing top-level GTM metrics. "
  "Cards: Total ARR ($2.2M), MRR Growth (+4.2%), Pipeline Value ($3.1M), Win Rate (35%), "
  "Net Retention (112%), Avg Deal Size ($48K), Sales Cycle (45 days), Active Customers (500). "
  "Each card: large number, label, trend arrow (up green / down red), sparkline showing last 6 months. "
  "Pull data from revenue, pipeline, and salesforce stores. "
  "Use the existing stat card pattern but enhanced with sparkline mini-charts using D3.js.")

t(22, "Build revenue vs pipeline combo chart",
  "Create frontend/src/components/dashboard/RevenuePipelineChart.vue — D3.js combination chart. "
  "Left Y-axis: ARR as area chart (blue fill). Right Y-axis: pipeline value as bar chart (lighter blue, semi-transparent). "
  "X-axis: months. Add a line overlay showing conversion rate trend. "
  "Show target line for ARR goal (dashed horizontal line). "
  "Tooltip shows all three values on hover. Legend at top-right. "
  "Make the chart responsive and animated on mount.")

t(22, "Build GTM health scorecard component",
  "Create frontend/src/components/dashboard/HealthScorecard.vue — a traffic-light scorecard for GTM health. "
  "Metrics with status (green/yellow/red based on thresholds): "
  "Pipeline Coverage (>3x = green, 2-3x = yellow, <2x = red), "
  "Win Rate (>30% = green, 20-30% = yellow, <20% = red), "
  "Churn Rate (<2% = green, 2-5% = yellow, >5% = red), "
  "Sales Cycle (<45d = green, 45-60d = yellow, >60d = red), "
  "NRR (>110% = green, 100-110% = yellow, <100% = red), "
  "Lead Response Time (<1h = green, 1-4h = yellow, >4h = red). "
  "Each metric: name, value, status dot, target, trend. Use a clean table layout with colored status indicators.")

t(22, "Build activity feed component",
  "Create frontend/src/components/dashboard/ActivityFeed.vue — a real-time feed of GTM events. "
  "Events: 'Acme Corp closed for $120K' (won deal), 'Lead scored 85+ from Campaign X' (hot lead), "
  "'Renewal at risk: BigCo health score dropped to 35' (churn risk), 'Q4 pipeline target 80% achieved' (milestone). "
  "Each event: icon, timestamp, message, category badge (deal, lead, risk, milestone). "
  "Generate 20 realistic events with timestamps spread over last 7 days. "
  "Auto-scroll to newest. Add category filter chips. Animate new events sliding in from top.")

t(22, "Build top accounts table component",
  "Create frontend/src/components/dashboard/TopAccountsTable.vue — sortable table of top accounts by ARR. "
  "Columns: Rank, Account Name, ARR, Plan, Health Score (colored bar), Pipeline, Last Activity, Renewal Date. "
  "Show top 20 accounts. Highlight at-risk accounts (health < 40) with red row background. "
  "Add mini bar chart in ARR column showing relative size. Sortable by all columns. "
  "Clickable rows to navigate to account detail. Add search/filter at top. "
  "Footer: summary row showing totals for ARR and pipeline.")

t(22, "Build deal velocity gauge component",
  "Create frontend/src/components/dashboard/DealVelocity.vue — a gauge/speedometer chart using D3.js. "
  "Show current deal velocity (pipeline × win rate × avg deal size / sales cycle length). "
  "Gauge ranges: red (low velocity), yellow (moderate), green (high). "
  "Show current value as large centered text. Show target with a needle marker. "
  "Below gauge: breakdown of the 4 components with individual trend indicators. "
  "Add tooltip explaining the velocity formula. Animate needle on mount.")

t(22, "Build GTM funnel summary widget",
  "Create frontend/src/components/dashboard/FunnelSummaryWidget.vue — a compact funnel for the dashboard. "
  "Simplified version of the pipeline funnel: MQL → SQL → Opportunity → Closed Won. "
  "Show count and value at each stage. Show conversion rates between stages. "
  "Compact enough to fit in a dashboard widget (max 300px height). "
  "Click to navigate to full Pipeline view. Use horizontal layout on wider screens.")

t(22, "Build recent deals ticker component",
  "Create frontend/src/components/dashboard/DealsTicker.vue — a horizontal scrolling ticker of recent deal activity. "
  "Show last 10 deals: company name, stage change, amount. "
  "Won deals in green, lost in red, stage advances in blue. "
  "Smooth auto-scroll animation (CSS animation, marquee-style). Pause on hover. "
  "Click any deal to see details. Compact single-line format. "
  "Place at the very top of the dashboard as a news-ticker style element.")

t(22, "Create GTM Dashboard view",
  "Create frontend/src/views/GtmDashboardView.vue — the unified GTM dashboard page. "
  "Layout using GtmDashboardLayout: DealsTicker at top, ExecutiveKpis below, "
  "RevenuePipelineChart (2/3) + HealthScorecard (1/3), "
  "FunnelSummaryWidget (1/3) + DealVelocity (1/3) + ActivityFeed (1/3), "
  "TopAccountsTable (full width). "
  "Add route: { path: '/gtm-dashboard', name: 'GTM Dashboard', component: GtmDashboardView }. "
  "Make this the default landing page after the existing Landing page. Add prominent nav item. "
  "Page title: 'GTM Command Center' with subtitle 'Real-time GTM operations intelligence'.")

# ═══════════════════════════════════════════════════════
# GROUP 23: Census/Fivetran + dbt (10 tasks)
# ═══════════════════════════════════════════════════════
t(23, "Create sync pipeline data models",
  "Create backend/app/models/data_pipeline.py with dataclasses: "
  "SyncJob (id, connector_name, source, destination, status: running|success|failed|scheduled, "
  "rows_synced, started_at, completed_at, duration_seconds, error_message), "
  "DbtModel (name, schema, materialization: table|view|incremental, depends_on: list[str], "
  "status: success|error|skipped, rows_affected, execution_time_seconds, last_run), "
  "DbtTest (name, model, status: pass|fail|warn, severity, message, last_run), "
  "DataFreshness (table_name, last_updated, expected_interval_hours, is_stale). "
  "Model both Fivetran (source → Snowflake) and Census (Snowflake → Salesforce) sync patterns.")

t(23, "Build data pipeline generator service",
  "Create backend/app/services/pipeline_sync_generator.py generating realistic sync data. "
  "Fivetran connectors (5): Salesforce→Snowflake, Stripe→Snowflake, HubSpot→Snowflake, Zendesk→Snowflake, Intercom→Snowflake. "
  "Census reverse syncs (3): Snowflake→Salesforce (lead scoring), Snowflake→HubSpot (segments), Snowflake→Intercom (tags). "
  "Generate 100 SyncJobs over last 30 days. 92% success, 5% failed (with realistic errors), 3% running. "
  "dbt models (30): dim_accounts, dim_contacts, fct_opportunities, fct_billing_events, mart_revenue, mart_pipeline, etc. "
  "Model dependencies forming a DAG (sources → staging → intermediate → marts). "
  "Generate 50 DbtTests: not_null, unique, relationships, accepted_values. 95% pass, 3% fail, 2% warn.")

t(23, "Create data pipeline API Blueprint",
  "Create backend/app/api/data_pipeline.py as a Flask Blueprint: "
  "GET /api/pipeline/syncs — sync job history with connector and status filters. "
  "GET /api/pipeline/syncs/<id> — single sync job with row-level details. "
  "GET /api/pipeline/connectors — list of connectors with last sync status and schedule. "
  "GET /api/pipeline/dbt/models — list of dbt models with status and dependencies. "
  "GET /api/pipeline/dbt/dag — DAG structure for visualization (nodes + edges). "
  "GET /api/pipeline/dbt/tests — test results with status filter. "
  "GET /api/pipeline/freshness — data freshness check for all monitored tables. "
  "GET /api/pipeline/stats — sync success rate, avg duration, total rows synced, dbt pass rate. "
  "Register in backend/app/api/__init__.py.")

t(23, "Build dbt DAG visualization component",
  "Create frontend/src/components/pipeline/DbtDagVisualization.vue — D3.js force-directed graph showing dbt model dependencies. "
  "Nodes: dbt models colored by type (source=gray, staging=blue, intermediate=purple, mart=green). "
  "Edges: dependency arrows pointing downstream. Node size proportional to execution time. "
  "Status overlay: green border (success), red border (error), gray border (skipped). "
  "On hover: show model name, schema, materialization, rows affected, execution time. "
  "Click to expand model details in a side panel. Add zoom/pan with D3 zoom behavior. "
  "Layout using d3-dag or dagre for proper hierarchical layout.")

t(23, "Build sync status timeline component",
  "Create frontend/src/components/pipeline/SyncTimeline.vue — Gantt-style chart showing sync job execution. "
  "Rows: one per connector. Timeline: last 24 hours. Bars: individual sync runs colored by status. "
  "Green=success, red=failed, blue=running, gray=scheduled. Bar width proportional to duration. "
  "On hover: sync details (rows synced, duration, error if failed). "
  "Add vertical 'now' line. Show schedule markers as small dots on each row. "
  "Use D3.js with time scale for X-axis.")

t(23, "Build data freshness monitor component",
  "Create frontend/src/components/pipeline/FreshnessMonitor.vue — table showing data freshness status. "
  "Columns: Table Name, Last Updated (relative time), Expected Interval, Status (Fresh/Stale/Unknown). "
  "Status icons: green clock (fresh), red clock (stale), gray question mark (unknown). "
  "Sort by staleness — most stale at top. Highlight stale tables with red background. "
  "Add 'SLA' column showing how far past the expected interval (e.g., '2h overdue'). "
  "Add summary bar at top: X fresh, Y stale, Z unknown.")

t(23, "Build sync error log component",
  "Create frontend/src/components/pipeline/SyncErrorLog.vue — filterable log of sync failures. "
  "Each entry: timestamp, connector name, error type, error message (collapsible full text). "
  "Group by connector with error count badges. Add severity color coding. "
  "Search/filter by connector, error type, date range. "
  "Show suggested remediation for common errors (auth expired, rate limited, schema change). "
  "Add 'error rate trend' sparkline showing errors per day for last 7 days.")

t(23, "Build connector health cards",
  "Create frontend/src/components/pipeline/ConnectorHealthCards.vue — card grid for each sync connector. "
  "Each card: connector name, source→destination, last sync status badge, last sync time (relative), "
  "success rate (last 30 days), avg rows/sync, avg duration. "
  "Mini sparkline showing sync success/fail over last 7 days. "
  "Add visual connector icon (Salesforce logo colors for SF, Stripe purple for Stripe, etc.). "
  "Cards use the brand card style with hover shadow effect.")

t(23, "Create data pipeline Pinia store and API client",
  "Create frontend/src/stores/dataPipeline.js and frontend/src/api/dataPipeline.js. "
  "Store state: syncs, connectors, dbtModels, dbtDag, dbtTests, freshness, stats, loading, error. "
  "Actions: fetchSyncs(filters), fetchConnectors(), fetchDbtModels(), fetchDbtDag(), fetchDbtTests(), fetchFreshness(), fetchPipelineStats(). "
  "Getters: syncsByConnector, failedSyncs, staleTableCount, dbtPassRate, connectorHealthMap. "
  "API client with matching functions for all endpoints.")

t(23, "Create Data Pipeline view",
  "Create frontend/src/views/DataPipelineView.vue as the data pipeline monitoring page. "
  "Layout: 4 KPI cards (Sync Success Rate, Avg Duration, Stale Tables, dbt Pass Rate). "
  "ConnectorHealthCards (full width, scrollable row). "
  "Two-column: DbtDagVisualization (2/3), FreshnessMonitor (1/3). "
  "Full-width: SyncTimeline. Below: tabbed — Sync History (table), dbt Tests (table), Error Log (SyncErrorLog). "
  "Add route: { path: '/data-pipeline', name: 'Data Pipeline', component: DataPipelineView }. Nav item with database icon. "
  "Page title: 'Data Pipeline Monitor' subtitle: 'Fivetran, Census, and dbt sync health'.")

# ═══════════════════════════════════════════════════════
# GROUP 24: MRR Reconciliation (10 tasks)
# ═══════════════════════════════════════════════════════
t(24, "Create reconciliation data models",
  "Create backend/app/models/reconciliation.py with dataclasses: "
  "ReconciliationRecord (account_id, account_name, sf_mrr, billing_mrr, snowflake_mrr, "
  "sf_vs_billing_diff, sf_vs_snowflake_diff, billing_vs_snowflake_diff, status: matched|discrepancy|unresolved, "
  "discrepancy_type: amount_mismatch|missing_in_source|timing_lag|currency_rounding, resolution_notes), "
  "ReconciliationRun (id, run_date, total_accounts, matched_count, discrepancy_count, total_discrepancy_value, "
  "largest_discrepancy, avg_discrepancy, run_duration_seconds), "
  "ReconciliationRule (name, description, check_type, threshold, action: flag|auto_resolve|escalate). "
  "Model the three-way reconciliation: Salesforce MRR vs Stripe/Billing MRR vs Snowflake mart MRR.")

t(24, "Build reconciliation data generator",
  "Create backend/app/services/reconciliation_generator.py generating realistic reconciliation data. "
  "Take the 500 customer accounts and for each generate three MRR values: "
  "85% match exactly across all three sources. "
  "8% have small discrepancies (<$100) from timing lags or rounding. "
  "5% have moderate discrepancies ($100-$1000) from missed syncs or pending updates. "
  "2% have large discrepancies (>$1000) from genuine data quality issues. "
  "Generate 4 weekly ReconciliationRuns showing improvement trend (discrepancies decreasing). "
  "Create 10 ReconciliationRules: amount tolerance ($5), percentage tolerance (1%), missing record check, "
  "currency normalization, timing window (48h), etc.")

t(24, "Create reconciliation API Blueprint",
  "Create backend/app/api/reconciliation.py as a Flask Blueprint: "
  "GET /api/reconciliation/runs — list of reconciliation runs with stats. "
  "GET /api/reconciliation/runs/<id> — single run with all records. "
  "GET /api/reconciliation/current — most recent run's results. "
  "GET /api/reconciliation/discrepancies — only discrepancy records, sorted by magnitude. "
  "GET /api/reconciliation/account/<id> — reconciliation history for a specific account. "
  "POST /api/reconciliation/resolve/<record_id> — mark discrepancy as resolved with notes. "
  "GET /api/reconciliation/rules — active reconciliation rules. "
  "GET /api/reconciliation/stats — overall recon health: match rate, total discrepancy value, trend. "
  "Register in backend/app/api/__init__.py.")

t(24, "Build three-way comparison table component",
  "Create frontend/src/components/reconciliation/ThreeWayTable.vue — table comparing MRR across sources. "
  "Columns: Account, Salesforce MRR, Billing MRR, Snowflake MRR, SF vs Billing Diff, SF vs Snow Diff, Status. "
  "Color-code differences: green (match), yellow (<$100), orange ($100-$1000), red (>$1000). "
  "Add filter: All, Matched Only, Discrepancies Only. Sort by any column, default by discrepancy magnitude. "
  "Show totals row at bottom. Expandable rows showing discrepancy details and resolution options. "
  "Add search by account name. Highlight the source(s) that differ.")

t(24, "Build discrepancy distribution chart",
  "Create frontend/src/components/reconciliation/DiscrepancyDistribution.vue — D3.js histogram of discrepancy sizes. "
  "X-axis: discrepancy amount ranges ($0-$10, $10-$50, $50-$100, $100-$500, $500-$1000, $1000+). "
  "Y-axis: count of accounts. Stacked by discrepancy type (timing, rounding, missing, genuine). "
  "Add reference line at average discrepancy. Show summary: mean, median, max, std dev. "
  "Color bars by type. Add tooltip with exact counts per category.")

t(24, "Build reconciliation trend chart",
  "Create frontend/src/components/reconciliation/ReconTrendChart.vue — D3.js line chart showing recon health over time. "
  "Lines: match rate (%), total discrepancy value ($), discrepancy count. "
  "X-axis: reconciliation run dates. Dual Y-axis: percentage (left), dollar value (right). "
  "Show improvement trend with green area fill when match rate is above 95% target. "
  "Add annotation markers for rule changes or process improvements. "
  "Goal: demonstrate that reconciliation is improving over time.")

t(24, "Build source comparison Venn diagram",
  "Create frontend/src/components/reconciliation/SourceVenn.vue — Venn diagram showing data overlap between sources. "
  "Three circles: Salesforce, Billing, Snowflake. "
  "Intersections show: all three match (center), two match (overlapping pairs), unique to one source. "
  "Size proportional to account count. Color: green (all match), yellow (partial match), red (unique). "
  "Use D3.js with manual circle positioning. Show counts and percentages in each region. "
  "Tooltip on each region showing example accounts. This is a conceptual diagram — exact Venn proportions not critical.")

t(24, "Build resolution workflow component",
  "Create frontend/src/components/reconciliation/ResolutionWorkflow.vue — interface for resolving discrepancies. "
  "Show discrepancy details: account, all three source values, difference amounts. "
  "Resolution options: Auto-resolve (within tolerance), Manual correction (enter correct value), "
  "Escalate to Finance, Mark as timing lag (will resolve on next sync). "
  "Add notes field for resolution explanation. Show resolution history for repeat offenders. "
  "Confirm dialog before resolution. Update status to 'resolved' via API call.")

t(24, "Create reconciliation Pinia store and API client",
  "Create frontend/src/stores/reconciliation.js and frontend/src/api/reconciliation.js. "
  "Store state: runs, currentRun, discrepancies, accountHistory, rules, stats, loading, error. "
  "Actions: fetchRuns(), fetchCurrentRun(), fetchDiscrepancies(), fetchAccountRecon(id), resolveDiscrepancy(id, resolution), fetchRules(), fetchStats(). "
  "Getters: matchRate, totalDiscrepancyValue, criticalDiscrepancies (>$1000), unresolvedCount. "
  "API client matching all endpoints.")

t(24, "Create Reconciliation view",
  "Create frontend/src/views/ReconciliationView.vue as the MRR reconciliation page. "
  "Layout: 4 KPI cards (Match Rate, Total Discrepancy Value, Unresolved Count, Trend direction). "
  "Two-column: ReconTrendChart (2/3), SourceVenn (1/3). "
  "Full-width: ThreeWayTable with ResolutionWorkflow in a slide-over panel. "
  "Full-width: DiscrepancyDistribution. "
  "Add route: { path: '/reconciliation', name: 'Reconciliation', component: ReconciliationView }. Nav item with scale/balance icon. "
  "Page title: 'MRR Reconciliation' subtitle: 'Three-way reconciliation: Salesforce vs Billing vs Snowflake'.")

# ═══════════════════════════════════════════════════════
# GROUP 25: CHECKPOINT (1 task)
# ═══════════════════════════════════════════════════════
t(25, "CHECKPOINT: Verify app builds and runs after GTM data integration",
  "Run comprehensive build and smoke test: "
  "1) cd frontend && pnpm install && pnpm build — verify no TypeScript/build errors. "
  "2) cd frontend && pnpm lint — verify no linting errors. "
  "3) cd backend && pip install -r requirements.txt — verify no missing dependencies. "
  "4) python -c 'from app import create_app; app = create_app(); print(\"Backend OK\")' — verify app factory works. "
  "5) Verify all new API Blueprints are registered: check backend/app/api/__init__.py imports. "
  "6) Verify all new routes are accessible by listing Flask routes: app.url_map. "
  "7) Verify all new Vue views have routes in frontend/src/router/index.js. "
  "8) Verify all new nav items are in AppNav.vue. "
  "Fix any build errors, missing imports, or registration issues found. "
  "Create a checkpoint summary in docs/checkpoint-group-25.md listing what was built and any issues found.")

# Write output
if __name__ == "__main__":
    with open("PRD.json") as f:
        prd = json.load(f)

    print(f"Existing tasks: {len(prd['tasks'])}")
    print(f"New tasks (groups 15-25): {len(NEW_TASKS)}")

    # Don't write yet — this is part 1 of the generator
    # Save tasks for merging later
    with open("tmp/tasks_15_25.json", "w") as f:
        json.dump(NEW_TASKS, f, indent=2)

    print(f"Saved {len(NEW_TASKS)} tasks to tmp/tasks_15_25.json")
