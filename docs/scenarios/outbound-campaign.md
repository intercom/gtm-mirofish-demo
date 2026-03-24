# Outbound Campaign Pre-Testing

**ID:** `outbound_campaign` | **Category:** Outbound | **API:** `GET /api/gtm/scenarios/outbound_campaign`

## Business Context

Intercom is launching an automated outbound campaign targeting mid-market SaaS companies (500–2000 employees) currently using Zendesk. The campaign pitches Fin AI agent as a superior alternative that resolves 50% of support conversations automatically.

The core challenge: outbound campaigns are expensive to test in production. Previous AI SDR efforts (Conversica) achieved a 74% open rate but **0% conversion**. Meanwhile, account data quality is poor — 56K incorrect website records and Clay enrichment accuracy of only 25–32% for support tool data. Reps spend 5–30 minutes per account just validating data before engaging.

This scenario lets GTM teams pre-test messaging, subject lines, and cadence against synthetic prospect populations before committing real send budget.

## What the Simulation Tests

The simulation generates **200 synthetic agents** across four persona types and tests outbound email sequences against them:

### Target Personas
- VP of Support
- CX Director
- IT Leader
- Head of Operations

### Firmographic Distribution
- **Industries:** SaaS, Healthcare, Fintech, E-commerce
- **Company sizes:** 200–500, 500–1000, 1000–2000 employees
- **Regions:** North America, EMEA, APAC

### Variables Under Test
- **Four messaging angles:** ROI-focused, speed-to-deploy, AI quality, scale capacity
- **Four subject line variants:**
  - "Your Zendesk bill is 3x what it should be"
  - "How [Company] cut support costs 40% with AI"
  - "Replace Zendesk in 30 days — here is how"
  - "The AI agent your support team actually wants"
- **Cadence timing** across a 72-hour simulated window (30-minute rounds)

### Simulation Parameters
- **Duration:** 72 hours simulated time
- **Round interval:** 30 minutes
- **Mode:** Parallel (all agents active simultaneously)

## Expected Insights

The report should produce these outputs:

1. **Engagement prediction by persona type** — Which roles open, click, and reply at the highest rates
2. **Subject line effectiveness ranking** — Ordered by predicted open rate and positive response rate
3. **Objection mapping by industry** — What pushback each vertical generates and how to counter it
4. **Optimal sequence cadence** — Best spacing between touchpoints for each persona type
5. **Competitive messaging sensitivity** — How aggressively agents can reference Zendesk displacement without triggering negative reactions

## How to Interpret Results

### Engagement Predictions
Look at engagement rates broken down by persona type. **VP of Support** and **Head of Operations** are the most likely to respond to cost/efficiency messaging, while **IT Leaders** tend to engage with technical differentiation points. If a persona type shows <5% predicted engagement, the messaging angle needs rework for that audience.

### Subject Line Rankings
Subject lines are ranked by a combination of open rate prediction and sentiment analysis. A line with high opens but negative sentiment (e.g., "Replace Zendesk in 30 days") may drive curiosity but also trigger defensive reactions — check the sentiment breakdown alongside raw engagement numbers.

### Objection Maps
Each industry cluster generates characteristic objections. Use these to:
- Pre-build objection-handling sequences in the cadence
- Identify which industries are "cold" (high objection density) vs "warm" (engagement-ready)
- Prioritize industries where the value proposition resonates naturally

### Cadence Recommendations
The simulation tests response patterns across 144 rounds (72h / 30min). Optimal cadence will vary by persona seniority — executives typically need more spacing between touches. Look for the "engagement decay" curve: the point where additional touches produce diminishing or negative returns.

### Competitive Sensitivity
Scores range from receptive to hostile. If a segment shows high sensitivity to competitive displacement messaging, consider softening the angle to consultative positioning ("here's what's possible") rather than direct comparison ("replace Zendesk").
