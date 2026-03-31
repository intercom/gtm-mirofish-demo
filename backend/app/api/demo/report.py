"""Demo Report Blueprint — mock report generation, sections, and chat."""

import time

from flask import Blueprint, Response, request

from . import (
    _reports, _ok, _err, _elapsed,
    REPORT_GEN_SECONDS,
)

from llm_client import chat_completion

report_demo_bp = Blueprint('demo_report', __name__)


# ---------------------------------------------------------------------------
# Report section content
# ---------------------------------------------------------------------------

REPORT_SECTIONS = [
    {
        "section_index": 0,
        "content": """## Executive Summary

This report presents findings from a 72-hour swarm intelligence simulation involving **200 AI agents** representing synthetic buyer personas across SaaS, Healthcare, Fintech, and E-commerce verticals. The simulation tested Intercom's outbound campaign messaging strategy targeting mid-market companies currently using Zendesk.

### Key Findings

- **VP of Support personas showed 3.2x higher engagement with ROI-driven messaging** compared to speed-to-value messaging, with particularly strong response rates among companies spending >$10K/mo on support tooling
- **"Your Zendesk bill is 3x what it should be"** was the highest-performing subject line, achieving a **34.7% simulated open rate** — but triggered spam perception in 8.2% of Healthcare personas due to aggressive competitive framing
- **Healthcare and Fintech verticals require compliance-first messaging** — standard ROI messaging achieved only 12% engagement vs. 31% when HIPAA/SOC2 compliance was mentioned in the first two sentences
- **Optimal email cadence is Day 1 → Day 3 → Day 8 → Day 15** — the standard Day 1 → Day 2 → Day 4 cadence showed 23% higher unsubscribe intent signals
- **Fin AI agent resolution rate claims** (50% automation) were the single most persuasive data point, referenced in 67% of positive engagement signals across all persona types

### Simulation Confidence

| Metric | Value |
|--------|-------|
| Total agent interactions | 12,384 |
| Unique conversation threads | 847 |
| Cross-persona influence events | 234 |
| Simulation convergence score | 0.89 / 1.00 |
| Statistical confidence | 94.2% |

> **Bottom line:** The outbound campaign has strong fundamentals but requires segment-specific message tailoring. A one-size-fits-all approach would underperform by an estimated 40-55% compared to the optimized variant matrix recommended in Chapter 5.""",
    },
    {
        "section_index": 1,
        "content": """## Engagement Analysis

### Engagement by Persona Type

The simulation reveals dramatic differences in how each persona type engages with outbound messaging:

| Persona Type | Open Rate | Reply Rate | Meeting Book Rate | Top Message Trigger |
|-------------|-----------|------------|-------------------|---------------------|
| VP of Support | 38.4% | 12.1% | 4.8% | Cost reduction proof points |
| CX Director | 31.2% | 8.7% | 3.2% | AI resolution rate benchmarks |
| IT Leader | 22.8% | 5.3% | 2.1% | Integration ecosystem details |
| Head of Operations | 35.6% | 10.4% | 4.1% | Efficiency metrics and headcount impact |
| CFO / Finance | 28.9% | 7.8% | 3.6% | ROI calculations with timeframe |

### Engagement by Industry

- **SaaS companies** showed the highest overall engagement (34.2% average open rate), driven by familiarity with the competitive landscape and active tool evaluation cycles
- **Healthcare** had the lowest initial engagement (19.8%) but the **highest conversion-to-meeting rate** (5.1%) when compliance messaging was front-loaded — these buyers are slower to engage but more serious when they do
- **Fintech** personas exhibited strong "comparison shopping" behavior — 73% of engaged fintech personas also researched Freshdesk and HubSpot Service Hub within the simulation, suggesting multi-vendor evaluation is the norm
- **E-commerce** engagement was highly seasonal-dependent — agents simulating Q4 planning cycles showed 2.8x higher engagement than those in steady-state operations

### Engagement by Company Size

| Company Size | Avg Open Rate | Avg Reply Rate | Key Pattern |
|-------------|--------------|----------------|-------------|
| 200-500 employees | 36.1% | 11.2% | Price-sensitive, fast decision cycles |
| 500-1000 employees | 32.4% | 9.8% | Committee-driven, need multiple touches |
| 1000-2000 employees | 27.8% | 7.1% | Security-first, require enterprise features |

### Network Effects

A notable finding: when **3+ personas from the same simulated company** engaged with outbound content, the likelihood of a meeting booking increased by **4.7x**. This suggests that multi-threading (reaching multiple stakeholders at the same company) is significantly more effective than single-contact outreach.

The simulation identified **23 "viral content" events** where one agent's positive engagement triggered interest from connected agents, primarily through simulated internal Slack-like channels. The content that generated these cascade events consistently featured **specific, verifiable metrics** (e.g., "48% AI resolution rate in 30-day pilot") rather than general claims.""",
    },
    {
        "section_index": 2,
        "content": """## Messaging Effectiveness

### Subject Line Performance

All four subject line variants were tested against the full 200-agent population. Results ranked by simulated open rate:

| Rank | Subject Line | Open Rate | Spam Flag Rate | Best Segment |
|------|-------------|-----------|----------------|--------------|
| 1 | "Your Zendesk bill is 3x what it should be" | 34.7% | 8.2% | SaaS VP of Support |
| 2 | "How [Company] cut support costs 40% with AI" | 31.2% | 2.1% | All — safest universal option |
| 3 | "The AI agent your support team actually wants" | 28.9% | 1.4% | CX Directors, Support Managers |
| 4 | "Replace Zendesk in 30 days — here's how" | 24.3% | 11.7% | SaaS IT Leaders only |

**Critical insight:** Subject line #1 has the highest open rate but also the highest spam perception. In Healthcare, the spam flag rate jumps to **14.8%** — this subject line should be **excluded from Healthcare segments entirely**.

Subject line #2 is the recommended default: strong performance across all segments with minimal negative perception. The `[Company]` personalization token increased open rates by an additional 3.2 percentage points when the case study was industry-matched.

### Message Body Analysis

The simulation tested message body variations across three dimensions:

**Tone:**
- **Data-driven tone** outperformed all others across VP and Director personas (+18% engagement vs. casual)
- **Casual tone** performed well with Support Managers and smaller companies but alienated Enterprise buyers (-22%)
- **Consultative tone** was the best performer for IT Leaders who valued being treated as technical peers

**Length:**
- **Short emails (< 100 words)** had the highest open-to-read rate but lowest meeting booking rate
- **Medium emails (100-200 words)** were the optimal length, balancing engagement and conversion
- **Long emails (> 200 words)** were only effective for CFO personas who wanted detailed ROI analysis

**Call-to-Action Style:**
- **Soft ask** ("Would it be useful to see how [similar company] approached this?"): 11.3% reply rate
- **Hard ask** ("Can we schedule 20 minutes this week?"): 7.8% reply rate, but 2.1x higher meeting conversion
- **Question CTA** ("What's your team's biggest support bottleneck right now?"): 14.7% reply rate — highest response rate but lower quality responses

### Competitive Displacement Sensitivity

Mentions of competitor names triggered strong reactions:

- **Zendesk mentions** were well-received by frustrated current users (positive in 64% of interactions) but triggered defensive responses from satisfied Zendesk users (negative in 78%)
- **Freshdesk mentions** were largely neutral — most personas viewed Freshdesk as a lower-tier option and didn't feel defensive
- **HubSpot Service Hub mentions** triggered "already evaluated" fatigue in 34% of personas — many had recently looked at HubSpot and decided against it

**Recommendation:** Lead with value proposition, not competitive displacement. Introduce competitor comparisons only in follow-up emails (email 2 or 3 in sequence) and only when the prospect has shown engagement signals.""",
    },
    {
        "section_index": 3,
        "content": """## Behavioral Patterns

### Temporal Engagement Patterns

The 72-hour simulation revealed distinct behavioral waves:

- **Hours 0-12:** Initial engagement spike. 62% of all first opens occurred within the first 12 simulated hours. VP-level personas opened within 2 hours; Manager-level personas took 6-8 hours on average.
- **Hours 12-36:** "Research phase." Engaged personas spent this period visiting simulated product pages, reading case studies, and discussing internally. **This is when the multi-threading effect is strongest** — reaching a second stakeholder during this window increased conversion 3.1x.
- **Hours 36-56:** Decision crystallization. Personas either moved toward meeting booking or disengaged. The "silent middle" — personas who opened but didn't respond — showed a 23% eventual conversion rate when followed up at Hour 48.
- **Hours 56-72:** Late responders. A surprising 15% of total meetings were booked in this window, primarily from personas who needed internal approval or budget confirmation.

### Persona Behavioral Clusters

The simulation identified five distinct behavioral clusters that cut across job titles:

**Cluster 1: "Rapid Evaluators" (18% of agents)**
- Opened email within 1 hour, clicked through to product page, and either booked or dismissed within 24 hours
- Best reached with: direct CTA, specific metrics, and a clear "next step"
- Over-indexed on: SaaS companies, 200-500 employees

**Cluster 2: "Committee Builders" (24% of agents)**
- Forwarded content to 2-3 internal stakeholders before engaging
- Best reached with: shareable content (case studies, ROI calculators), multi-stakeholder messaging
- Over-indexed on: 500-1000 employee companies, Healthcare

**Cluster 3: "Silent Researchers" (31% of agents)**
- Opened multiple times but never replied to outbound email
- Eventually engaged through a different channel (simulated product page visit, competitor comparison page)
- Best reached with: retargeting-style follow-ups that acknowledge their research behavior

**Cluster 4: "Skeptical Evaluators" (19% of agents)**
- Responded with objections or requests for proof before any positive engagement
- **Most likely to convert once objections are addressed** (34% eventual meeting rate vs. 12% average)
- Best reached with: detailed technical documentation, peer references, and pilot program offers

**Cluster 5: "Passive Observers" (8% of agents)**
- Minimal engagement but remained subscribed. Represent future pipeline for re-engagement campaigns.
- Best reached with: low-frequency, high-value content (quarterly industry reports, benchmark data)

### Objection Mapping

The most common objections by frequency:

1. **"We just renewed our Zendesk contract"** (34% of negative responses) — Counter: offer ROI analysis to build business case for next renewal cycle
2. **"AI chatbots give bad answers"** (28%) — Counter: Fin accuracy benchmarks with comparable company data
3. **"We don't have budget for a migration"** (22%) — Counter: migration cost offset by first-year savings calculation
4. **"We need [specific feature] that you don't have"** (16%) — Counter: feature parity documentation and roadmap

### Network Influence Analysis

Key finding: **8 "influencer" agents** (4% of the population) generated **34% of all positive sentiment cascade events**. These agents shared characteristics:
- Senior titles (VP or Director level)
- At companies with 500+ employees
- Had previously evaluated 2+ support tools
- Engaged with data-driven content (not emotional appeals)

This suggests that identifying and prioritizing "influencer" prospects in real campaigns could dramatically improve campaign ROI.""",
    },
    {
        "section_index": 4,
        "content": """## Recommendations

Based on the simulation findings, we recommend the following prioritized action items:

### Priority 1: Segment-Specific Message Variants (Confidence: 96%)

- **Create 4 industry-specific email variants** instead of one universal template
  - **SaaS:** Lead with Zendesk migration ease and Fin resolution rates
  - **Healthcare:** Lead with HIPAA compliance and patient communication AI
  - **Fintech:** Lead with security certifications and cost-per-ticket metrics
  - **E-commerce:** Lead with seasonal scaling and Shopify integration
- **Expected impact:** 35-45% improvement in overall engagement rate

### Priority 2: Optimize Subject Line Strategy (Confidence: 94%)

- **Default to "How [Company] cut support costs 40% with AI"** as the universal subject line
- **Use "Your Zendesk bill is 3x what it should be"** only for SaaS companies confirmed on Zendesk
- **Never use competitive displacement subject lines** for Healthcare or Fintech segments
- **A/B test "The AI agent your support team actually wants"** for CX Director personas specifically
- **Expected impact:** 8-12% higher open rates with 60% reduction in spam flags

### Priority 3: Revise Email Cadence (Confidence: 91%)

- **Switch from Day 1-2-4 to Day 1-3-8-15 cadence** to reduce unsubscribe pressure
- **Add a "research acknowledgment" touchpoint at Day 5** for prospects who opened but didn't reply — "I noticed you've been exploring [topic] — here's a relevant case study"
- **Introduce multi-threading at Day 3** — reach a second stakeholder at engaged companies
- **Expected impact:** 23% reduction in unsubscribe rate, 18% increase in meeting bookings

### Priority 4: Build "Influencer Prospect" Targeting (Confidence: 87%)

- **Identify real-world equivalents of the 8 influencer archetypes** found in the simulation
- **Characteristics to target:** VP/Director at 500+ employee companies who have evaluated 2+ support tools in the past 18 months
- **Create premium content track** (executive briefings, benchmark reports) for these high-value prospects
- **Expected impact:** 3-4x ROI on outreach to this segment

### Priority 5: Address Top Objections Proactively (Confidence: 85%)

- **Add "contract flexibility" messaging** in Email 2 for the 34% who cite existing contracts
- **Create Fin accuracy benchmark one-pager** for the 28% concerned about AI quality
- **Build an interactive migration cost calculator** for the 22% citing budget constraints
- **Publish feature parity matrix** (Intercom vs. Zendesk vs. Freshdesk) for the 16% with feature concerns
- **Expected impact:** 15-20% improvement in objection-to-engagement conversion

### Implementation Timeline

| Week | Action | Owner |
|------|--------|-------|
| 1 | Create industry-specific email variants | Content team |
| 1 | Implement new subject line strategy | Growth marketing |
| 2 | Update cadence in outbound automation | Marketing ops |
| 2 | Build influencer prospect target list | Sales ops |
| 3 | Create objection-handling collateral | Product marketing |
| 3 | Launch A/B tests with optimized variants | Growth marketing |
| 4 | Analyze first-week results and iterate | All teams |

### Risk Factors

- **Spam filter sensitivity:** Aggressive competitive messaging in subject lines carries brand risk. Monitor deliverability metrics closely in the first 48 hours of any campaign launch.
- **Data freshness:** The simulation used anonymized seed data. Verify that technographic data (who uses Zendesk) is current — stale data was identified as a known issue (25-32% accuracy in Clay enrichment).
- **AI perception gap:** 28% of personas had negative preconceptions about AI chatbots. Leading with "AI agent" framing may backfire — consider "intelligent automation" or "smart support" as alternative positioning.

> **Overall recommendation:** Implement Priorities 1-3 immediately for the next outbound campaign cycle. Priorities 4-5 are medium-term improvements that can be phased in over the following quarter. The simulation predicts a **45-65% improvement in campaign effectiveness** when all five recommendations are implemented versus the current one-size-fits-all approach.""",
    },
]


# ---------------------------------------------------------------------------
# Report lifecycle routes
# ---------------------------------------------------------------------------

@report_demo_bp.route("/api/v1/report/generate", methods=["POST"])
def report_generate():
    body = request.get_json(silent=True) or {}
    sim_id = body.get("simulation_id", "demo-sim-00001")
    report_id = f"demo-report-{sim_id.split('-')[-1]}"

    if report_id in _reports and _elapsed(_reports, report_id) > REPORT_GEN_SECONDS():
        return _ok({
            "report_id": report_id,
            "status": "completed",
            "already_generated": True,
        })

    _reports[report_id] = {"start": time.time(), "sim_id": sim_id}
    return _ok({
        "report_id": report_id,
        "status": "generating",
        "already_generated": False,
    })


@report_demo_bp.route("/api/v1/report/generate/status", methods=["POST"])
def report_generate_status():
    body = request.get_json(silent=True) or {}
    report_id = body.get("report_id", "")
    if report_id not in _reports:
        return _err("Report not found", 404)
    elapsed = _elapsed(_reports, report_id)
    pct = min(100, int(elapsed / REPORT_GEN_SECONDS() * 100))
    return _ok({"progress": pct, "status": "completed" if pct >= 100 else "generating"})


@report_demo_bp.route("/api/v1/report/<report_id>/progress")
def report_progress(report_id):
    if report_id not in _reports:
        _reports[report_id] = {"start": time.time(), "sim_id": "unknown"}

    elapsed = _elapsed(_reports, report_id)
    pct = min(100, int(elapsed / REPORT_GEN_SECONDS() * 100))
    total_sections = len(REPORT_SECTIONS)
    completed = min(total_sections, int(pct / 100 * total_sections))

    messages = [
        (0, "Analyzing simulation data..."),
        (20, "Generating executive summary..."),
        (40, "Computing engagement metrics..."),
        (60, "Analyzing messaging effectiveness..."),
        (80, "Synthesizing recommendations..."),
        (95, "Finalizing report..."),
    ]
    msg = "Initializing..."
    for threshold, m in messages:
        if pct >= threshold:
            msg = m

    return _ok({
        "progress": pct,
        "total_sections": total_sections,
        "completed_sections": completed,
        "message": msg,
    })


@report_demo_bp.route("/api/v1/report/<report_id>/sections")
def report_sections(report_id):
    if report_id not in _reports:
        _reports[report_id] = {"start": time.time(), "sim_id": "unknown"}

    elapsed = _elapsed(_reports, report_id)
    pct = min(100, elapsed / REPORT_GEN_SECONDS() * 100)
    total = len(REPORT_SECTIONS)
    visible = min(total, int(pct / 100 * total) + (1 if pct > 5 else 0))

    return _ok({
        "sections": REPORT_SECTIONS[:visible],
        "is_complete": pct >= 100,
    })


@report_demo_bp.route("/api/v1/report/<report_id>/section/<int:section_index>")
def report_section(report_id, section_index):
    if 0 <= section_index < len(REPORT_SECTIONS):
        return _ok(REPORT_SECTIONS[section_index])
    return _err("Section not found", 404)


@report_demo_bp.route("/api/v1/report/<report_id>")
def report_get(report_id):
    return _ok({
        "report_id": report_id,
        "status": "completed",
        "sections": REPORT_SECTIONS,
    })


@report_demo_bp.route("/api/v1/report/by-simulation/<sim_id>")
def report_by_simulation(sim_id):
    report_id = f"demo-report-{sim_id.split('-')[-1]}"
    return _ok({
        "report_id": report_id,
        "status": "completed",
    })


@report_demo_bp.route("/api/v1/report/list")
def report_list():
    return _ok({"reports": []})


@report_demo_bp.route("/api/v1/report/<report_id>/download")
def report_download(report_id):
    full_md = "\n\n---\n\n".join(s["content"] for s in REPORT_SECTIONS)
    return Response(
        full_md,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=mirofish-report-{report_id}.md"},
    )


@report_demo_bp.route("/api/v1/report/check/<sim_id>")
def report_check(sim_id):
    report_id = f"demo-report-{sim_id.split('-')[-1]}"
    if report_id in _reports and _elapsed(_reports, report_id) > REPORT_GEN_SECONDS():
        return _ok({
            "has_report": True,
            "report_id": report_id,
            "report_status": "completed",
        })
    return _ok({
        "has_report": False,
        "report_id": None,
        "report_status": None,
    })


@report_demo_bp.route("/api/v1/report/<report_id>/agent-log")
def report_agent_log(report_id):
    return _ok({"logs": []})


@report_demo_bp.route("/api/v1/report/<report_id>/agent-log/stream")
def report_agent_log_stream(report_id):
    return _ok({"logs": []})


@report_demo_bp.route("/api/v1/report/<report_id>/console-log")
def report_console_log(report_id):
    return _ok({"logs": []})


@report_demo_bp.route("/api/v1/report/<report_id>/console-log/stream")
def report_console_log_stream(report_id):
    return _ok({"logs": []})


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------

CHAT_RESPONSES = {
    "subject line": {
        "response": "Based on the simulation data, here's the subject line performance breakdown:\n\n1. \"Your Zendesk bill is 3x what it should be\" — 34.7% open rate (but 8.2% spam flag in Healthcare)\n2. \"How [Company] cut support costs 40% with AI\" — 31.2% open rate (safest universal option)\n3. \"The AI agent your support team actually wants\" — 28.9% open rate (best for CX Directors)\n4. \"Replace Zendesk in 30 days\" — 24.3% open rate (highest spam risk at 11.7%)\n\nThe key insight is that subject line #1 has the highest raw performance but carries brand risk in regulated industries. For a universal campaign, I'd recommend #2 as the default with #1 reserved for confirmed Zendesk accounts in SaaS.",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "subject line performance by open rate and spam flag rate"}, "result": "Analyzed 200 agent interactions across 4 subject line variants. Competitive displacement framing shows highest engagement but also highest negative sentiment in Healthcare (14.8% spam flag) and Fintech (9.1% spam flag)."},
        ],
        "sources": ["Simulation Rounds 1-144", "Agent Engagement Metrics", "Spam Perception Analysis"],
    },
    "persona": {
        "response": "The simulation reveals significant persona-based variation in engagement:\n\n\u2022 VP of Support: 38.4% open rate, responds most strongly to ROI-driven messaging with specific cost reduction numbers. They want to see \"40% cost reduction\" not \"significant savings.\"\n\n\u2022 CX Director: 31.2% open rate, most engaged by AI resolution rate benchmarks. They care about CSAT impact and agent experience.\n\n\u2022 IT Leader: 22.8% open rate \u2014 the hardest to engage. They prioritize integration ecosystem details and security certifications. Lead with technical credibility.\n\n\u2022 Head of Operations: 35.6% open rate, focused on efficiency metrics and headcount impact. They're running the numbers immediately.\n\n\u2022 CFO: 28.9% open rate, responds to detailed ROI calculations with specific timeframes. They need a business case they can present to the board.\n\nThe biggest surprise: VP of Support personas showed 3.2x higher engagement with ROI messaging compared to speed-to-value messaging. We assumed speed would win, but these buyers care more about proving budget impact to their CFO.",
        "tool_calls": [
            {"name": "panorama_search", "arguments": {"query": "persona engagement breakdown by role title"}, "result": "Retrieved engagement data for 5 persona types across 12,384 total interactions. VP of Support and Head of Operations are highest-engagement personas. IT Leaders require the most touches before converting."},
        ],
        "sources": ["Agent Cluster Analysis", "Persona Engagement Matrix", "Cross-Role Comparison Report"],
    },
    "healthcare": {
        "response": "Healthcare is a fascinating segment in this simulation. Here's what the data shows:\n\n\u2022 Initial engagement is the LOWEST of all verticals at 19.8% average open rate\n\u2022 BUT conversion-to-meeting rate is the HIGHEST at 5.1% \u2014 these buyers are slow to engage but very serious when they do\n\u2022 HIPAA compliance must be mentioned in the first two sentences or engagement drops to 12%\n\u2022 Standard ROI messaging achieves only 12% engagement vs 31% when compliance is front-loaded\n\u2022 The subject line \"Your Zendesk bill is 3x what it should be\" triggers a 14.8% spam flag rate in Healthcare \u2014 it should be excluded entirely\n\nThe recommended approach for Healthcare: Lead with \"HIPAA-compliant AI-powered support\" positioning, include SOC2 certification badges in email signature, and use the consultative CTA style (\"What are your biggest compliance challenges with your current support tool?\").",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "healthcare vertical engagement patterns and compliance sensitivity"}, "result": "Healthcare personas prioritize compliance verification before evaluating features. 89% of healthcare decision-makers checked for HIPAA documentation within first 3 interactions. Compliance-first messaging improved engagement 2.6x."},
        ],
        "sources": ["Vertical Analysis - Healthcare", "Compliance Sensitivity Index", "HIPAA Messaging A/B Results"],
    },
    "objection": {
        "response": "The simulation identified four primary objection patterns with clear counter-strategies:\n\n1. **\"We just renewed our Zendesk contract\"** (34% of negative responses)\n   \u2192 Counter: Don't push for immediate switch. Offer ROI analysis to build business case for next renewal. Plant the seed now, harvest in 6-12 months.\n\n2. **\"AI chatbots give bad answers\"** (28%)\n   \u2192 Counter: This is the most convertible objection! Share Fin accuracy benchmarks and offer a controlled pilot. 34% of \"Skeptical Evaluator\" personas who raised this objection eventually booked meetings.\n\n3. **\"We don't have budget for a migration\"** (22%)\n   \u2192 Counter: Build an interactive migration cost calculator showing first-year savings offset. The math almost always works in Intercom's favor for companies spending >$5K/mo on support.\n\n4. **\"We need [specific feature] you don't have\"** (16%)\n   \u2192 Counter: Feature parity matrix + roadmap. Most gaps are perceived, not real.\n\nKey insight: Skeptical Evaluators (Cluster 4) have the HIGHEST eventual meeting rate at 34%. Don't be discouraged by initial pushback \u2014 address it directly with data.",
        "tool_calls": [
            {"name": "panorama_search", "arguments": {"query": "objection frequency and conversion rates by objection type"}, "result": "Mapped 4 primary objection categories across 847 conversation threads. 'AI quality concerns' objection has highest overcome rate (34%) when addressed with specific accuracy benchmarks and pilot program offers."},
        ],
        "sources": ["Objection Mapping Analysis", "Skeptical Evaluator Cluster Study", "Counter-Strategy Effectiveness Report"],
    },
    "roi": {
        "response": "The ROI story from the simulation is compelling:\n\n\u2022 **Cost reduction:** Companies spending >$10K/mo on support tools showed the strongest engagement with cost-saving messaging. The \"40% cost reduction\" claim was the most-cited metric in positive engagement signals.\n\n\u2022 **Headcount efficiency:** Head of Operations personas responded 3.1x more strongly to \"handle 10x volume without hiring\" than generic efficiency claims. They're doing literal headcount math.\n\n\u2022 **Time-to-value:** Deployment speed (\"3 weeks vs 6 months\") was the #2 most persuasive data point after resolution rate claims. But it was most effective for smaller companies (200-500 employees) who can't afford long implementation cycles.\n\n\u2022 **AI resolution rate:** Fin's 50% automation claim was referenced in 67% of positive engagement signals. This is the single most powerful metric in the entire messaging arsenal.\n\nThe simulation suggests framing ROI differently by persona:\n- **For VPs:** \"Save $280K/yr and redeploy 3 agents to proactive outreach\"\n- **For CFOs:** \"40% cost reduction with 90-day payback period\"\n- **For Ops leaders:** \"Handle holiday surge without temporary hires\"",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "ROI messaging effectiveness by persona and company size"}, "result": "ROI-driven messaging outperformed speed messaging by 3.2x among VP personas. Cost reduction claims most effective at >$10K/mo spend. Resolution rate (50%) was referenced in 67% of positive engagement signals."},
        ],
        "sources": ["ROI Sensitivity Analysis", "Persona-Specific Messaging Study", "Cost Reduction Impact Model"],
    },
    "cadence": {
        "response": "The simulation revealed a clear winner for email cadence:\n\n**Current cadence (Day 1-2-4):** Triggers \"too aggressive\" perception in 23% of personas. The Day 2 follow-up feels pushy, especially for Enterprise buyers who need time to process.\n\n**Recommended cadence (Day 1-3-8-15):**\n- Day 1: Initial outreach with value proposition\n- Day 3: \"Research acknowledgment\" \u2014 acknowledge their evaluation without being pushy\n- Day 8: Case study or social proof relevant to their industry\n- Day 15: Direct ask with specific meeting time offer\n\nThis cadence showed 23% lower unsubscribe intent and 18% higher eventual meeting bookings.\n\n**Critical addition:** Multi-threading at Day 3. When a second stakeholder at the same company was contacted during the \"research phase\" (Hours 12-36), conversion increased 3.1x. The simulation strongly supports reaching multiple buying committee members early.\n\n**Late responder insight:** 15% of meetings were booked in the Day 12-15 window by personas who needed internal approval time. Don't give up after Day 8.",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "email cadence timing optimization and multi-threading impact"}, "result": "Day 1-3-8-15 cadence outperformed Day 1-2-4 by 18% in meeting bookings with 23% fewer unsubscribes. Multi-threading (2+ contacts at same company) at Day 3 increased conversion 3.1x."},
        ],
        "sources": ["Cadence Optimization Analysis", "Multi-Threading Impact Study", "Temporal Engagement Patterns"],
    },
    "fin": {
        "response": "Fin AI agent data from the simulation:\n\n\u2022 **Resolution rate claims are the #1 persuasion lever** \u2014 \"50% AI resolution\" was referenced in 67% of positive engagement signals across ALL persona types\n\u2022 Agents who received Fin-specific messaging showed 2.4x higher engagement than those who received generic \"AI support\" messaging\n\u2022 The most effective Fin proof point was: \"48% resolution rate in 30-day pilot\" \u2014 specific, time-bounded, and verifiable\n\u2022 IT Leaders specifically asked about Fin's accuracy on technical queries vs. simple FAQ-type questions\n\u2022 Healthcare personas needed assurance that Fin could handle HIPAA-sensitive interactions\n\n**Interesting pattern:** Personas who had previously experienced a failed chatbot deployment (Cluster 4: Skeptical Evaluators) were actually MORE likely to engage with Fin messaging when it included accuracy benchmarks and pilot program structure. They want AI to work \u2014 they just need proof.\n\nRecommendation: Create a \"Fin Accuracy Report\" one-pager showing resolution rates by ticket category, and include it as an attachment in Email 2 of the sequence.",
        "tool_calls": [
            {"name": "panorama_search", "arguments": {"query": "Fin AI agent perception and engagement metrics across persona types"}, "result": "Fin-specific messaging achieved 2.4x engagement vs generic AI messaging. 50% resolution rate claim was most-cited metric. Skeptical Evaluators showed 34% eventual conversion when provided accuracy benchmarks."},
        ],
        "sources": ["Fin Perception Analysis", "AI Accuracy Benchmark Study", "Pilot Program Engagement Data"],
    },
}

DEFAULT_CHAT = {
    "response": "That's a great question! Based on the simulation data, here's what I can tell you:\n\nThe 72-hour simulation with 200 AI agents produced 12,384 total interactions across Twitter and Reddit platforms. The key themes that emerged were:\n\n1. **ROI-driven messaging outperforms speed messaging** by 3.2x among senior buyer personas\n2. **Healthcare and Fintech require compliance-first positioning** \u2014 standard messaging only achieves 12% engagement vs 31% with compliance front-loaded\n3. **Multi-threading (reaching multiple stakeholders)** increases conversion 4.7x\n4. **Optimal cadence is Day 1-3-8-15** instead of the current Day 1-2-4\n\nYou can ask me about specific topics like:\n- Subject line performance\n- Persona-specific engagement patterns\n- Objection handling strategies\n- ROI messaging optimization\n- Email cadence recommendations\n- Fin AI agent positioning\n- Industry-specific approaches (Healthcare, Fintech, etc.)\n\nWhat would you like to dive deeper into?",
    "tool_calls": [
        {"name": "panorama_search", "arguments": {"query": "simulation overview and key metrics"}, "result": "72-hour simulation, 200 agents, 12,384 interactions, 847 unique threads, 94.2% statistical confidence. Top finding: segment-specific messaging improves engagement 35-45%."},
    ],
    "sources": ["Full Simulation Report", "Executive Summary", "Cross-Section Analysis"],
}

_REPORT_CHAT_SYSTEM = """You are MiroFish, an AI research analyst for Intercom's GTM team.

You have access to results from a completed swarm intelligence simulation:
- 200 AI agents representing buyer personas across SaaS, Healthcare, Fintech, and E-commerce
- 72-hour simulation, 144 rounds, running on Twitter and Reddit platforms
- Outbound campaign targeting mid-market companies currently using Zendesk

Key findings you should reference:
- VP of Support personas showed 3.2x higher engagement with ROI-driven messaging vs speed-to-value messaging
- "Your Zendesk bill is 3x what it should be" achieved 34.7% open rate but 8.2% spam flag rate in Healthcare
- Healthcare and Fintech require compliance-first messaging (12% engagement without vs 31% with)
- Optimal email cadence is Day 1-3-8-15 (not Day 1-2-4)
- Fin AI agent 50% resolution rate was the single most persuasive data point (referenced in 67% of positive signals)
- Multi-threading (3+ personas at same company) increases meeting booking 4.7x
- 12,384 total interactions, 847 unique threads, 94.2% statistical confidence
- Subject line "How [Company] cut support costs 40% with AI" is the safest universal option (31.2% open, 2.1% spam)
- "Replace Zendesk in 30 days" had 24.3% open rate but 11.7% spam flag — worst performer
- Data-driven tone outperformed casual tone by 18% among VP/Director personas
- Medium emails (100-200 words) optimal length; short emails have lowest meeting conversion
- Skeptical Evaluators (19% of agents) have the HIGHEST eventual meeting rate (34%) when objections are addressed
- Top objection: "We just renewed our Zendesk contract" (34% of negative responses)
- 8 "influencer" agents (4% of population) generated 34% of positive sentiment cascades

Respond with data-backed insights. Use markdown formatting.
Reference specific metrics and percentages from the simulation data.
Keep responses focused and actionable. If asked about something not in the simulation data, say so honestly."""


@report_demo_bp.route("/api/v1/report/chat", methods=["POST"])
def report_chat():
    body = request.get_json(silent=True) or {}
    question = (body.get("message") or body.get("question") or "")
    chat_history = body.get("chat_history") or []

    llm_messages = [{"role": "system", "content": _REPORT_CHAT_SYSTEM}]
    for msg in chat_history:
        if msg.get("role") in ("user", "assistant"):
            llm_messages.append({"role": msg["role"], "content": msg["content"]})
    llm_messages.append({"role": "user", "content": question})

    llm_response = chat_completion(llm_messages, max_tokens=2048)

    if llm_response:
        return _ok({
            "response": llm_response,
            "tool_calls": [
                {"name": "insight_forge", "arguments": {"query": question[:100]}, "result": "Analyzed simulation data with LLM."},
            ],
            "sources": ["Simulation Report", "Agent Engagement Data", "LLM Analysis"],
        })

    q_lower = question.lower()
    matched = None
    for keyword, response_data in CHAT_RESPONSES.items():
        if keyword in q_lower:
            matched = response_data
            break

    if not matched:
        matched = DEFAULT_CHAT

    return _ok(matched)
