# MiroFish GTM Demo — Presenter Script

**Duration:** 10–15 minutes (full) · 5 minutes (abbreviated) · 20 minutes (deep-dive)
**Audience:** GTM leadership, RevOps, Sales/Marketing stakeholders, Engineering
**Prerequisites:** App running locally or via Railway deployment

> This script follows the Outbound Campaign scenario end-to-end. All steps work in demo mode (no LLM key required). Timings are approximate — adjust pacing to audience engagement.

---

## Pre-Demo Checklist

**Option A — Railway (recommended for presentations):**
- [ ] Frontend: https://frontend-production-86ea.up.railway.app
- [ ] Backend: https://backend-production-e9d7.up.railway.app
- [ ] Verify health: visit the backend URL `/health` endpoint

**Option B — Local:**
- [ ] App running at `http://localhost:3000` (frontend) and `http://localhost:5001` (backend)
- [ ] Demo mode active: set `VITE_DEMO_MODE=true` in `frontend/.env.production` if using built assets

**For both options:**
- [ ] Browser: Chrome or Edge, fullscreen, zoom at 100%
- [ ] Close unrelated browser tabs, silence notifications
- [ ] Presenter Toolbar visible (bottom-right floating button — appears automatically in demo mode)
- [ ] Test the full flow once before presenting: landing → scenario → simulation → report → chat

**Presenter Toolbar Controls:**
- **Speed** (1×/2×/3×/5×): Accelerates simulation and graph build timers
- **Skip Phase**: Jumps to next phase if audience is ready to move on
- **Reset Demo**: Clears state, returns to landing page

**Keyboard Shortcuts (Simulation Workspace):**
- `1`–`6`: Switch workspace tabs (Graph, Simulation, Communities, Relationships, Network, Coalitions)
- `R`: Jump to Report view
- `Esc`: Go back

---

## Step 1 — Landing Page & Value Proposition (30 seconds)

**Route:** `/`

**What to show:**
- Hero section with animated swarm visualization
- The 3-step flow: **Seed → Simulate → Reports**
- Scroll to the scenario grid (19 pre-built GTM scenarios across categories)
- Stats banner: 1M agents supported, 4 tools, 2 platforms

**Talking points:**
- "MiroFish is a swarm intelligence engine for GTM operations. Instead of A/B testing on real prospects, you simulate campaigns against hundreds of AI agents that role-play your buyer personas."
- "Think of it as a flight simulator for go-to-market — test your messaging, pricing, and signals before they hit real inboxes."
- "We ship with 19 pre-built scenarios covering outbound campaigns, pricing changes, competitive response, pipeline optimization, churn prevention, and more — all tuned to Intercom's GTM motion."

**If asked:** "How realistic are the agents?" → Scroll to the FAQ section or persona showcase at the bottom of the page.

---

## Step 2 — Simulation History & Metrics (1 minute)

**Route:** `/simulations`

**What to show:**
- Summary stats cards: total runs, total actions, most-used scenario
- Any previous demo runs in the list (status badges, round counts, action counts)
- Search and filter controls (status: completed/in-progress/failed, sort options)

**Talking points:**
- "This is your mission control — every simulation run is tracked with full metrics."
- "You can see at a glance which scenarios ran, how many agent interactions occurred, and jump straight to the report or re-run with different parameters."
- "Each run preserves its configuration so you can iterate on messaging and compare results."

**Transition:** "Let me show you how a simulation starts. We'll use the Outbound Campaign scenario."

---

## Step 3 — Scenario Builder Configuration (1.5 minutes)

**Route:** `/scenarios/outbound_campaign`

**What to show:**
- Pre-loaded seed document (outbound email copy for Zendesk displacement campaign)
- Persona selection: VP of Support, CX Director, IT Leader, Head of Operations
- Industry mix: SaaS, Healthcare, Fintech, E-commerce
- Agent count slider (200), duration (72h), platform mode (Twitter + Reddit)
- Expand Advanced Options: company size filters, regions, minutes per round

**Talking points:**
- "Every simulation starts with a seed document — this is the campaign copy, pricing page, or signal definition you want to test."
- "We pre-loaded the Outbound Campaign template. It simulates 200 prospect agents receiving Zendesk displacement emails across four persona types and four industries."
- "You control the population: persona mix, industry verticals, company size, geography. The agents are generated from anonymized GTM data — real firmographic distributions, not random noise."
- Point to the seed text: "This is the actual messaging the agents will react to — subject lines like 'Your Zendesk bill is 3x what it should be' and value props around Fin AI resolution rates."

**Action:** Click **Run Simulation** to launch.

---

## Step 4 — Knowledge Graph Building (1.5 minutes)

**Route:** `/workspace/:taskId?tab=graph`

**What to show:**
- D3 force-directed graph rendering in real-time
- Nodes appearing progressively as entities are extracted
- Color coding: orange (personas), blue (topics/products), purple (relationships)
- Left stats panel: entity counts by type, node/edge totals, build status messages

**Talking points:**
- "The first phase builds a knowledge graph from your seed document. MiroFish extracts entities — personas, topics, products, competitive references — and maps their relationships."
- Point to orange nodes: "These are the prospect personas — Sarah Chen VP Support at Acme SaaS, Marcus Johnson CX Director at MedFirst Health."
- Point to blue nodes: "These are the topics the agents will debate — AI-First Support, Zendesk Migration Pain, ROI-Driven Messaging, Competitive Displacement Strategy."
- "The graph gives agents shared context — they don't just react to the email in isolation, they understand the competitive landscape, industry dynamics, and each other's concerns."

**Tip:** If the build finishes quickly, use the Presenter Toolbar speed control to slow it down for dramatic effect.

---

## Step 5 — Live Simulation Feed (3 minutes)

**Route:** `/workspace/:taskId?tab=simulation` (press `2` to switch tabs)

**What to show:**
- Status badge transitioning from Building → Running
- Progress bar advancing through 144 rounds
- Real-time actions feed: agent name, platform, action type, content
- Platform tabs (All / Twitter / Reddit) with per-platform metrics
- Metrics updating: total actions, Twitter actions, Reddit actions

**Talking points:**
- "Now the agents are interacting. Each round simulates 30 minutes of real time — we're compressing 72 hours of prospect behavior into a few minutes."
- Point to the actions feed: "Watch the content — agents aren't just clicking buttons. They're writing realistic responses based on their persona."
- Highlight a specific action: "See this reply from Priya Patel, Head of Ops at PayStream Financial — she's pushing back on migration complexity. That's her persona: process efficiency focused, concerned about disruption."
- "Notice how some agents are more active on Twitter vs Reddit — the platform split reveals channel preferences by persona type."

**Let it run for 60–90 seconds, then:** "While the simulation completes, let me show you the sentiment analysis."

---

## Step 6 — Sentiment Analysis & Agent Profiles (1.5 minutes)

**Route:** Still on `/workspace/:taskId?tab=simulation`, then click into an agent

**What to show:**
- Sentiment Timeline chart (below the actions feed)
  - Toggle between Trend view (line chart) and Distribution view (stacked bar)
  - Show sentiment moving from neutral → polarized as rounds progress
- Click an agent name to open their profile at `/workspace/:taskId/agent/:agentId`
  - Overview tab: persona traits, sentiment label, action stats
  - Activity tab: full timeline of that agent's actions

**Talking points:**
- "The sentiment timeline shows how agent attitudes shift over the course of the campaign. Early rounds are exploratory — by mid-simulation you see clear signal on who's receptive and who's skeptical."
- Switch to Distribution view: "This stacked view shows the sentiment breakdown per round. Watch for the inflection point — that's where your messaging either lands or loses the audience."
- Navigate to an agent profile: "You can drill into any individual agent. This is David Kim, IT Leader at ShopNova — security and compliance focused, technical veto power. His activity shows he engaged early but went silent after round 40. That's a red flag for your messaging."

**Transition:** "The simulation is wrapping up. Let's generate the report."

---

## Step 7 — Report Generation (1.5 minutes)

**Route:** `/report/:taskId`

**What to show:**
- Report generation progress (shimmer loaders → progress percentage)
- Multi-chapter layout rendering section by section
- Chapter sidebar navigation
- Key findings extraction (bullet points)
- D3 charts: persona engagement rates (bar chart), subject line performance (grouped bars)

**Talking points:**
- "MiroFish generates a multi-chapter narrative report from the simulation data — not just numbers, but interpretation and recommendations."
- When Chapter 1 loads: "The Executive Summary calls out 200 agents, 12,000+ interactions, and a 94% confidence score. These aren't vanity metrics — confidence is derived from interaction density and sentiment convergence."
- Scroll to Chapter 2: "Engagement Analysis breaks down by persona. VP of Support personas had 38% open rates and respond to ROI messaging 3.2x more than speed-to-value. That's actionable — it tells your SDRs which hook to lead with for each role."
- Point to a chart: "Subject line performance shows 'Your Zendesk bill is 3x what it should be' drove the highest opens but also an 8% spam perception flag. High engagement doesn't mean high conversion — MiroFish catches that distinction."
- "The report also surfaces optimal cadence — Day 1-3-8-15 had 23% lower unsubscribe intent than aggressive Day 1-2-4 sequences."

---

## Step 8 — Interactive Chat (1.5 minutes)

**Route:** `/chat/:taskId`

**What to show:**
- Suggested prompts: "Summarize findings", "Which messaging resonated?", "What should we do next?", "Compare persona engagement"
- Click a suggested prompt, watch the response stream in
- Tool call indicators animating (Insight Forge, Panorama Search)
- Ask a custom follow-up question

**Talking points:**
- "After the report, you can have an interactive conversation with the simulation data. Think of this as Fin for your GTM team."
- Click "Which messaging resonated?": "Watch the tool calls — the agent is querying the simulation database, cross-referencing sentiment data, and synthesizing an answer."
- "You can ask anything: 'What objections did Healthcare prospects raise?', 'Should we soften the Zendesk displacement angle?', 'Which persona should we target first?'"
- Ask: "What should we change about the email sequence for IT Leaders?" to show a custom query.

**Transition:** "Finally, let me show you how the system is configured."

---

## Step 9 — Settings & LLM Configuration (30 seconds)

**Route:** `/settings`

**What to show:**
- LLM Provider selector: Anthropic (Claude), OpenAI (GPT-4o), Google Gemini
- API key input with Test Connection button
- Theme toggle (light/dark/system)
- Default simulation parameters

**Talking points:**
- "MiroFish supports three LLM providers — Claude, GPT-4o, and Gemini. You choose based on your org's preferences and API access."
- "Everything runs in demo mode without API keys, but connecting a real LLM unlocks richer agent reasoning, better report generation, and more natural chat responses."

---

## Step 10 — Wrap-Up & Q&A (1 minute)

**Route:** Return to `/` (landing page)

**Talking points:**
- "What you just saw was one scenario — Outbound Campaign Pre-Testing. MiroFish ships with 18 more covering the full GTM lifecycle."
- "Highlight scenarios by audience interest:"
  - **Revenue leaders**: Pricing Simulation (500 agents reacting to P5 pricing migration), Expansion Revenue, Pipeline Optimization
  - **Sales leaders**: Signal Validation, Enterprise Deal Strategy, Quarterly Pipeline Review
  - **Marketing leaders**: Outbound Campaign, Personalization, Product Launch GTM
  - **Strategy/Ops**: Competitive Response, Market Entry Analysis, Budget Allocation Debate, Churn Prevention War Room
- "The key insight: every GTM team has a 'send and pray' problem. MiroFish replaces guesswork with simulation. Test your messaging before it hits real inboxes, predict pricing reactions before you announce changes, validate signals before you build workflows around them."

**Expected questions and answers:**

| Question | Answer |
|----------|--------|
| How realistic are the agents? | Agents are generated from anonymized GTM data — real firmographic distributions, persona templates based on Intercom ICP roles, and industry-specific communication styles. |
| How long does a real simulation take? | 3–5 minutes for graph building, 5–15 minutes for simulation (depending on agent count and round configuration). Reports generate in 1–2 minutes. |
| Can we use our own data? | Yes — the Custom scenario option lets you paste any seed document. You can also modify persona templates and seed data files. |
| What LLM does it use? | Configurable: Claude Sonnet 4, GPT-4o, or Gemini Flash. Each provider is swappable via a single environment variable. |
| Is the data private? | All simulation data stays in your deployment. LLM calls send only the seed text and agent prompts — no customer PII is involved. |
| How many scenarios are there? | 19 pre-built scenarios across outbound, signals, pricing, competitive, pipeline, expansion, churn, and more. Plus a custom scenario builder for any GTM situation. |
| Can I compare simulation runs? | Yes — the Comparison view (`/comparison`) lets you put two simulation runs side-by-side to compare outcomes with different parameters. |

---

## Bonus Features (if time allows or audience asks)

These features can be shown ad-hoc during Q&A or in a longer demo session:

### Simulation Replay (`/replay/:taskId`)
- Timeline scrubber showing round-by-round playback of the entire simulation
- "You can rewind to any point in the simulation and see exactly what happened — like a DVR for your GTM experiment."

### Scenario Walkthrough (`/scenarios/:id/walkthrough`)
- Guided step-by-step experience for first-time users
- Progress bar, step cards, and contextual explanations
- "For teams new to MiroFish, the walkthrough mode guides them through each phase with explanations."

### Scenario Marketplace (`/marketplace`)
- Browsable gallery of all 19 scenario templates with search and filtering
- "The marketplace lets you discover scenarios by category — outbound, pricing, competitive, pipeline — and launch any of them with pre-loaded configuration."

### Dashboard & Analytics (`/dashboard`, `/analytics`)
- Aggregated metrics across all simulation runs
- Custom dashboard builder with drag-and-drop widgets
- "For teams running multiple simulations, the dashboard aggregates insights across all your runs."

### Comparison View (`/comparison`)
- Side-by-side comparison of two simulation runs
- "Run the same scenario with different parameters and compare outcomes — true A/B testing for GTM strategy."

### Workspace Deep-Dive Tabs
During the simulation workspace, mention additional tabs if the audience is technical:
- **Communities** (press `3`): Clustered agent groups that self-organize
- **Relationships** (press `4`): How agent connections evolve over time
- **Network** (press `5`): Detailed graph analysis of influence patterns
- **Coalitions** (press `6`): Alliance formation between aligned agents

---

## Backup Plan — Demo Mode

If anything fails during the live demo, MiroFish has built-in graceful degradation:

**If the backend is unreachable:**
- The frontend automatically switches to demo mode
- Landing page shows hardcoded scenario list
- Graph builds with a synthetic 57-entity knowledge graph
- Simulation generates realistic agent actions with sample personas
- Reports display a pre-written 5-section analysis with real insights

**If a specific step hangs:**
- Use the **Presenter Toolbar** (bottom-right):
  - **Skip Phase** jumps to the next stage immediately
  - **Speed 5×** accelerates any running timer
  - **Reset Demo** clears all state and starts fresh

**If LLM calls fail (chat or report):**
- Chat falls back to keyword-matched responses covering: subject lines, personas, healthcare, objections, ROI, cadence, Fin AI
- Reports use pre-generated content with realistic simulation findings

**Quick recovery steps:**
1. If the page goes blank → refresh the browser, navigate to `/`
2. If simulation gets stuck → use Presenter Toolbar "Skip Phase"
3. If local app is down → restart with `docker compose up -d`, wait 10 seconds, refresh
4. If Railway is down → switch to local: `docker compose up -d` and open `http://localhost:3000`
5. If you need a fresh start → Presenter Toolbar "Reset Demo" or clear browser localStorage

---

## Demo Timing Summary

| Step | Duration | Route | Key Action |
|------|----------|-------|------------|
| 1. Landing Page | 0:30 | `/` | Show branding, scroll scenarios |
| 2. Simulation History | 1:00 | `/simulations` | Show metrics, past runs |
| 3. Scenario Builder | 1:30 | `/scenarios/outbound_campaign` | Configure and launch |
| 4. Knowledge Graph | 1:30 | `/workspace/:id?tab=graph` | Watch graph build |
| 5. Live Simulation | 3:00 | `/workspace/:id?tab=simulation` | Watch agents interact |
| 6. Sentiment & Agents | 1:30 | Same + agent profile | Drill into sentiment, agent |
| 7. Report | 1:30 | `/report/:id` | Show chapters, charts |
| 8. Chat | 1:30 | `/chat/:id` | Interactive Q&A |
| 9. Settings | 0:30 | `/settings` | LLM config |
| 10. Wrap-Up | 1:00 | `/` | Summary, Q&A |
| **Total** | **~13 min** | | |

---

## Shortened 5-Minute Version

If time is limited, compress to these five steps:

1. **Landing Page** (15s) — Quick scroll, point to scenario grid
2. **Scenario Builder** (30s) — Show pre-loaded config, click Run
3. **Simulation** (2min) — Watch graph build, switch to simulation tab, highlight actions feed and sentiment
4. **Report** (1.5min) — Show key findings, one chart, mention cadence recommendation
5. **Chat** (1min) — Ask "Which messaging resonated?", show tool calls, wrap up

---

## Extended 20-Minute Deep-Dive Version

For technical audiences or stakeholders who want the full picture, add these after the standard 13-minute flow:

6. **Scenario Marketplace** (2min) — Browse all 19 scenarios, show category filters, open a different scenario (e.g., Pricing Simulation) to show breadth
7. **Replay** (2min) — Open Replay view for a completed simulation, scrub through the timeline, show how agent behavior evolves
8. **Comparison** (1.5min) — Compare two simulation runs side-by-side (e.g., same scenario with different agent counts)
9. **Dashboard** (1.5min) — Show aggregated metrics across all runs, highlight the custom dashboard builder

---

## Audience-Specific Tips

### For GTM Leadership (VP Sales, CMO, CRO)
- Lead with business outcomes: "predict churn before it happens", "test messaging before it hits real inboxes"
- Emphasize the Pricing Simulation and Outbound Campaign scenarios
- Spend more time on the Report and Chat phases — these deliver the actionable insights
- Skip technical details (Settings, Architecture)

### For RevOps / Sales Ops
- Emphasize the scenario configuration: "you control every variable"
- Show the Simulation History view and metrics tracking
- Highlight comparison capabilities for iterative testing
- Mention the 19 pre-built scenarios covering their full workflow

### For Engineering / Technical Audiences
- Show the Settings page and multi-LLM provider support
- Mention the keyboard shortcuts in the workspace
- Discuss the knowledge graph in more depth (Zep Cloud, entity extraction)
- Point out the D3.js visualizations and real-time data architecture
- Show the API docs at `/api-docs` if available

### For Executive Briefings (5 minutes max)
- Use the Shortened 5-Minute Version
- Focus on one scenario (Outbound Campaign)
- Skip to Report immediately after showing 30 seconds of simulation
- End with the "flight simulator for GTM" metaphor

---

## Available Scenarios Reference

All 19 pre-built scenarios with their focus areas:

| Scenario | Focus | Agents | Best For |
|----------|-------|--------|----------|
| Outbound Campaign | Zendesk displacement email testing | 200 | Sales/Marketing demos |
| Signal Validation | Intent signal predictivity | 500 | RevOps demos |
| Pricing Simulation | P5 pricing migration reactions | 500 | Revenue/Finance demos |
| Personalization | Email variant ranking | 200 | Marketing demos |
| AI Adoption Strategy | AI tool adoption barriers | 200 | Product demos |
| Pipeline Optimization | Deal pipeline efficiency | — | Sales Ops demos |
| Market Entry Analysis | New market/vertical entry | — | Strategy demos |
| Competitor Price War | Competitive pricing response | — | Pricing demos |
| Churn Prevention War Room | Retention strategy effectiveness | — | CS/Success demos |
| Expansion Revenue | Account expansion motions | — | Revenue demos |
| Enterprise Deal Strategy | Complex enterprise sale dynamics | — | Enterprise Sales demos |
| Product Launch GTM | New product launch effectiveness | — | Product Marketing demos |
| Quarterly Pipeline Review | Pipeline health and forecasting | — | Sales Leadership demos |
| Expansion vs Acquisition | Organic growth vs M&A | — | Strategy/Executive demos |
| Budget Allocation Debate | Marketing/sales budget outcomes | — | Finance/Ops demos |
| Competitive Response | Competitive move simulation | — | Strategy demos |
| Order Validation | Order validation and fulfillment | — | Ops demos |
| MRR Reconciliation | Revenue reconciliation | — | Finance demos |
| MRR Reconciliation Investigation | Detailed MRR discrepancy analysis | — | Finance deep-dives |
