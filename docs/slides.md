---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #ffffff;
    color: #1a1a1a;
  }
  h1 { color: #2068FF; }
  h2 { color: #050505; }
  h3 { color: #2068FF; }
  a { color: #2068FF; }
  strong { color: #050505; }
  code { background: rgba(32, 104, 255, 0.08); color: #2068FF; border-radius: 4px; padding: 2px 6px; }
  section.title {
    background: #050505;
    color: #ffffff;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.title h1 { color: #2068FF; font-size: 2.5em; }
  section.title h2 { color: #ffffff; font-weight: 400; font-size: 1.2em; }
  section.title p { color: rgba(255, 255, 255, 0.6); }
  section.dark {
    background: #050505;
    color: #e0e0e0;
  }
  section.dark h1, section.dark h2, section.dark h3 { color: #2068FF; }
  section.dark strong { color: #ff5600; }
  section.accent {
    background: #2068FF;
    color: #ffffff;
  }
  section.accent h1, section.accent h2 { color: #ffffff; }
  section.accent strong { color: #ff5600; }
  .columns { display: flex; gap: 2rem; }
  .columns > div { flex: 1; }
  footer { color: rgba(0, 0, 0, 0.4); font-size: 0.7em; }
---

<!-- _class: title -->
<!-- _paginate: false -->

# MiroFish GTM Demo

## Swarm Intelligence for GTM Operations

Powered by multi-agent AI simulation

<!-- Speaker notes: Welcome everyone. Today I'll show you MiroFish — a platform that uses AI agent swarms to simulate and predict GTM outcomes before you commit resources. -->

---

# The Problem

GTM teams operate in silos with incomplete information.

<div class="columns">
<div>

### What happens today
- Sales, Marketing, CS make decisions **independently**
- Pipeline forecasts rely on **gut instinct**
- Competitive responses are **reactive**, not proactive
- Cross-functional alignment takes **weeks** of meetings

</div>
<div>

### The cost
- **73%** of GTM campaigns miss targets
- Misaligned teams waste **$1M+** annually
- Competitive threats detected **too late**
- Revenue leakage from **poor handoffs**

</div>
</div>

<!-- Speaker notes: Every GTM team we talk to faces the same challenge — decisions happen in silos. Sales doesn't know what marketing is planning. CS feedback never reaches product. The result is misalignment and wasted resources. -->

---

# The Solution

**Simulate GTM decisions before making them** using AI agent swarms.

MiroFish creates a virtual world populated by AI agents representing your GTM stakeholders — each with distinct personas, knowledge, and biases — then simulates how they interact, debate, and reach decisions.

### The insight engine
1. **Build** a knowledge graph from your GTM context
2. **Spawn** AI agents with realistic personas
3. **Simulate** multi-round discussions and decisions
4. **Analyze** emergent patterns, coalitions, and risks

<!-- Speaker notes: MiroFish flips the script. Instead of guessing how your GTM strategy will play out, you simulate it first. AI agents act as stand-ins for real stakeholders, and you watch the dynamics unfold. -->

---

<!-- _class: dark -->

# Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                Vue 3 Frontend                    │
│   Landing · Scenarios · Simulation · Reports     │
│   Knowledge Graph · Chat · Agent Profiles        │
└──────────────────────┬──────────────────────────┘
                       │ REST + SSE
┌──────────────────────▼──────────────────────────┐
│              Flask Backend API                   │
│   Graph Builder · OASIS Engine · Report Gen      │
├──────────┬───────────┬───────────┬──────────────┤
│ Anthropic│  OpenAI   │  Gemini   │  Demo Mode   │
│  Claude  │  GPT-4o   │  Flash    │  (fallback)  │
└──────────┴───────────┴───────────┴──────────────┘
```

Multi-LLM support — switch providers via a single env var.
**Demo mode** works with zero API keys configured.

<!-- Speaker notes: The architecture is straightforward. Vue 3 frontend talks to a Flask backend that orchestrates the simulation. We support all three major LLM providers and can run fully offline in demo mode. -->

---

# Live Demo Walkthrough

### What we'll show

| Step | Feature | Duration |
|------|---------|----------|
| 1 | Landing page with Intercom branding | 30s |
| 2 | Select a GTM scenario template | 1 min |
| 3 | Build knowledge graph from seed text | 1 min |
| 4 | Launch simulation — watch agents debate live | 3 min |
| 5 | Explore agent profiles and reasoning | 1 min |
| 6 | View coalition formation and sentiment | 1 min |
| 7 | Generate AI-powered report | 1 min |
| 8 | Chat with the simulated world | 1 min |

<!-- Speaker notes: Here's what we'll walk through. The whole demo takes about 10 minutes. Each step builds on the previous one. -->

---

# Key Features

<div class="columns">
<div>

### AI Agents
- **Real LLM-powered** reasoning (not scripted)
- Distinct **personas** with knowledge and biases
- Multi-round **debate** with belief evolution
- **Coalition detection** — who aligns with whom

</div>
<div>

### Knowledge Graph
- Auto-generated from **seed text**
- Entities, relationships, and concepts
- **Real-time** visualization with D3.js
- Feeds agent **context and memory**

</div>
</div>

<!-- Speaker notes: Two pillars of the platform. First, the agents are real — powered by Claude, GPT-4, or Gemini. They don't follow scripts. Second, the knowledge graph gives agents shared context so their discussions are grounded. -->

---

# GTM Scenario Templates

Four pre-built scenarios tailored for GTM teams:

| Scenario | Focus | Agents |
|----------|-------|--------|
| **Pipeline Review** | Forecast accuracy, deal risk | Sales, RevOps, CS |
| **Competitive Response** | Positioning against threats | Product, Marketing, Sales |
| **Outbound Campaign** | Campaign strategy simulation | Marketing, SDR, Ops |
| **Pricing Simulation** | Pricing impact analysis | Finance, Product, Sales |

Each template includes **seed data**, **persona definitions**, and **discussion prompts** — ready to simulate in one click.

<!-- Speaker notes: We ship four GTM scenarios out of the box. Each one is designed around a real GTM motion. You can also build custom scenarios from scratch. -->

---

<!-- _class: dark -->

# Visualization Showcase

<div class="columns">
<div>

### D3.js Visualizations
- Agent activity **heatmaps**
- Sentiment **timeline charts**
- Competitive mention **tracking**
- Coalition **network graphs**

</div>
<div>

### Real-time Updates
- Live simulation **progress**
- Streaming agent **responses**
- Knowledge graph **growth**
- Influence **propagation**

</div>
</div>

All charts use **Intercom brand colors** (#2068FF, #ff5600, #050505) and respond to dark/light mode.

<!-- Speaker notes: Visualizations are built with D3.js. We track sentiment, competitive mentions, agent influence networks, and activity patterns. Everything updates in real time during the simulation. -->

---

# Technical Highlights

<div class="columns">
<div>

### Frontend
- **Vue 3** Composition API
- **Vite** for fast dev + build
- **Tailwind CSS** with design tokens
- **D3.js v7** for visualizations
- **Pinia** state management

</div>
<div>

### Backend
- **Flask** with Blueprint API
- **SSE streaming** for live updates
- **Multi-LLM** (Anthropic, OpenAI, Gemini)
- **Marshmallow** request validation
- **Demo mode** fallback for every endpoint

</div>
</div>

### Infrastructure
Docker + Railway deployment · CORS + OAuth · Health checks · Request logging · Token usage tracking

<!-- Speaker notes: Quick tech overview for the engineers in the room. Standard modern stack — Vue 3, Flask, Docker. The key differentiator is the multi-LLM support and the demo mode fallback that makes every feature work without API keys. -->

---

<!-- _class: accent -->

# What Makes This Different

### Not another dashboard. A **simulation engine**.

- **Predictive** — see outcomes before committing
- **Multi-perspective** — every stakeholder voice is represented
- **Emergent** — insights arise from agent interaction, not rules
- **Actionable** — AI-generated reports with specific recommendations

> "What if we could test our GTM strategy the way engineers test code?"

<!-- Speaker notes: The key differentiator is emergence. We don't program the outcomes. The agents interact, and patterns emerge — just like they do in real organizations. That's what makes the insights valuable. -->

---

<!-- _class: title -->
<!-- _paginate: false -->

# Q&A

### Questions and Discussion

Demo: `localhost:3000` · Backend: `localhost:5001`

Run with: `docker compose up -d`
