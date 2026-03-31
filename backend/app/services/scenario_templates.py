"""
Pre-built simulation scenario templates for GTM demos.

Each template defines a realistic Intercom GTM scenario with named agent
roles, personas, environment type, round count, and constraints.  Templates
are served via the /api/gtm/templates endpoints so the frontend can offer
one-click scenario setup.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class AgentConfig:
    """Configuration for a single agent in a scenario template."""
    role: str
    persona: str
    department: str
    seniority: str
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioTemplate:
    """A pre-built simulation scenario template."""
    id: str
    name: str
    description: str
    agent_configs: List[AgentConfig]
    environment_type: str
    num_rounds: int
    constraints: List[str]
    seed_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_configs": [a.to_dict() for a in self.agent_configs],
            "environment_type": self.environment_type,
            "num_rounds": self.num_rounds,
            "constraints": self.constraints,
            "seed_text": self.seed_text,
        }

    def to_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "environment_type": self.environment_type,
            "num_rounds": self.num_rounds,
            "agent_count": len(self.agent_configs),
        }


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

TEMPLATES: List[ScenarioTemplate] = [
    # 1. Pipeline Review
    ScenarioTemplate(
        id="pipeline_review",
        name="Pipeline Review",
        description="Sales team reviews Q4 pipeline, debates deal priorities, and aligns on forecast accuracy for Intercom's enterprise segment.",
        environment_type="meeting",
        num_rounds=6,
        agent_configs=[
            AgentConfig(
                role="VP of Sales",
                persona=(
                    "Seasoned sales leader responsible for Intercom's enterprise ARR target. "
                    "Pushes the team to focus on winnable deals and accurate forecasting. "
                    "Skeptical of deals stuck in evaluation and wants proof of champion engagement."
                ),
                department="Sales",
                seniority="VP",
                traits=["results-driven", "direct communicator", "forecast-obsessed"],
            ),
            AgentConfig(
                role="Sales Director, Mid-Market",
                persona=(
                    "Manages a team of 8 AEs selling Intercom Inbox, Fin AI Agent, and Workflows "
                    "to mid-market accounts (200-2000 employees). Strong opinions on deal staging "
                    "and pipeline hygiene. Advocates for multi-threading into economic buyers."
                ),
                department="Sales",
                seniority="Director",
                traits=["methodical", "pipeline-disciplined", "coaching-oriented"],
            ),
            AgentConfig(
                role="Account Executive",
                persona=(
                    "Top-performing AE carrying a $1.8M annual quota. Currently working 3 enterprise "
                    "deals involving Fin AI Agent deployment and Zendesk displacement. Confident in "
                    "deal progression but has limited CFO access on the largest opportunity."
                ),
                department="Sales",
                seniority="Individual Contributor",
                traits=["confident", "relationship-builder", "optimistic on deals"],
            ),
            AgentConfig(
                role="Revenue Operations Manager",
                persona=(
                    "Owns pipeline analytics, Salesforce hygiene, and forecast models. Flags deals "
                    "with stale next steps, missing MEDDIC fields, or inconsistent stage criteria. "
                    "Brings data to every meeting and challenges gut-feel forecasting."
                ),
                department="Revenue Operations",
                seniority="Manager",
                traits=["data-driven", "process-oriented", "diplomatically blunt"],
            ),
        ],
        constraints=[
            "Agents must reference specific Intercom products (Fin AI Agent, Inbox, Workflows, Help Center) when discussing deals",
            "Pipeline amounts should use realistic mid-market and enterprise deal sizes ($30K-$250K ARR)",
            "Forecast categories must follow Intercom's stage model: Discovery, Evaluation, Negotiation, Commit",
            "Agents should surface at least 2 deals with risk factors (competitor threat, budget freeze, champion departure)",
            "RevOps agent must challenge at least one deal's stage with data-backed reasoning",
        ],
        seed_text=(
            "Intercom Q4 pipeline review meeting. The team is reviewing 12 active opportunities "
            "totaling $2.4M in pipeline across mid-market and enterprise segments. Key deals include "
            "a $180K Fin AI Agent deployment at a Series D fintech displacing Zendesk, a $95K "
            "Workflows expansion at a healthcare SaaS company, and a $65K net-new mid-market deal "
            "where the champion just changed roles. Forecast target is $1.1M for the quarter and "
            "current commit is $680K. The team needs to identify which deals can close this quarter "
            "and which should be pushed to Q1."
        ),
    ),

    # 2. Competitive Response
    ScenarioTemplate(
        id="competitive_response",
        name="Competitive Response",
        description="Cross-functional war room reacts to Zendesk announcing a 30% price cut on their AI suite, debating Intercom's positioning and counter-strategy.",
        environment_type="war_room",
        num_rounds=8,
        agent_configs=[
            AgentConfig(
                role="Chief Marketing Officer",
                persona=(
                    "Owns Intercom's brand positioning and competitive narrative. Focused on "
                    "protecting Intercom's premium positioning without entering a price war. "
                    "Wants to double down on Fin AI Agent differentiation and customer proof points."
                ),
                department="Marketing",
                seniority="C-Suite",
                traits=["brand-protective", "strategic thinker", "calm under pressure"],
            ),
            AgentConfig(
                role="VP of Product",
                persona=(
                    "Leads Intercom's product strategy including Fin AI Agent, Workflows 2.0, "
                    "and the Messenger platform. Believes product superiority is the best competitive "
                    "moat. Concerned about feature comparison charts being used against Intercom "
                    "in enterprise deals."
                ),
                department="Product",
                seniority="VP",
                traits=["product-first mindset", "competitive awareness", "long-term thinker"],
            ),
            AgentConfig(
                role="VP of Sales",
                persona=(
                    "Hearing price objections from prospects in real-time. Three enterprise deals "
                    "paused this week citing Zendesk's new pricing. Needs immediate ammunition for "
                    "the sales team: battle cards, ROI calculators, and executive sponsor talking points."
                ),
                department="Sales",
                seniority="VP",
                traits=["urgency-driven", "pragmatic", "field-feedback oriented"],
            ),
            AgentConfig(
                role="Competitive Intelligence Analyst",
                persona=(
                    "Tracks Zendesk, Freshdesk, HubSpot Service Hub, and Salesforce Service Cloud. "
                    "Has detailed analysis of Zendesk's new pricing tiers, feature gaps, and customer "
                    "sentiment from G2, Gartner Peer Insights, and Reddit. Provides data-backed "
                    "competitive positioning."
                ),
                department="Marketing",
                seniority="Senior IC",
                traits=["analytical", "detail-oriented", "evidence-based"],
            ),
            AgentConfig(
                role="VP of Customer Success",
                persona=(
                    "Manages relationships with Intercom's top 200 accounts. Worried about renewal "
                    "risk if customers use Zendesk's price cut as leverage. Wants proactive outreach "
                    "strategy and retention offers for at-risk segments."
                ),
                department="Customer Success",
                seniority="VP",
                traits=["customer-centric", "retention-focused", "relationship-driven"],
            ),
        ],
        constraints=[
            "Discussion must reference real competitor products: Zendesk AI, Freshdesk Freddy, HubSpot Breeze",
            "Agents must avoid recommending across-the-board price cuts — Intercom's strategy is value-based pricing",
            "Competitive Intelligence agent must cite at least 3 specific data points (market share, G2 ratings, feature gaps)",
            "Sales VP must share at least 2 specific deal situations impacted by the competitor move",
            "Final rounds should converge on a 30/60/90-day response plan with assigned owners",
            "Agents should reference Fin AI Agent's 50%+ resolution rate as a key differentiator",
        ],
        seed_text=(
            "Emergency competitive response session. Zendesk announced a 30% price cut on their "
            "AI-powered support suite yesterday, positioning it as 'enterprise AI support at SMB prices.' "
            "The announcement has already impacted three active enterprise deals totaling $420K in pipeline. "
            "Intercom's current win rate against Zendesk is 62% but has dropped 8 points this quarter. "
            "The team needs to decide: Do we adjust pricing? Double down on product differentiation? "
            "Launch a targeted competitive campaign? The board meeting is in 3 weeks and the CEO wants "
            "a clear competitive response strategy."
        ),
    ),

    # 3. Product Launch GTM
    ScenarioTemplate(
        id="product_launch_gtm",
        name="Product Launch GTM",
        description="Cross-functional team plans the go-to-market strategy for Fin AI Agent v2 launch, coordinating messaging, enablement, and launch sequencing.",
        environment_type="planning_session",
        num_rounds=10,
        agent_configs=[
            AgentConfig(
                role="Product Marketing Lead",
                persona=(
                    "Owns the Fin AI Agent v2 launch narrative. Responsible for positioning, "
                    "messaging hierarchy, and launch tier classification. Balancing excitement "
                    "about new capabilities (multi-turn resolution, CRM actions, 94% accuracy) "
                    "with avoiding overpromising."
                ),
                department="Product Marketing",
                seniority="Lead",
                traits=["storyteller", "launch-experienced", "messaging-precise"],
            ),
            AgentConfig(
                role="VP of Product",
                persona=(
                    "Built the Fin AI Agent v2 roadmap. Deep technical knowledge of the new "
                    "capabilities: live CRM data pulls, multi-turn troubleshooting, action execution "
                    "(refunds, subscription updates), and custom workflow triggers. Wants the launch "
                    "to accurately represent what ships on day one vs. what's in beta."
                ),
                department="Product",
                seniority="VP",
                traits=["technically precise", "scope-conscious", "quality-focused"],
            ),
            AgentConfig(
                role="Sales Enablement Manager",
                persona=(
                    "Needs to equip 60+ AEs with demo scripts, competitive battle cards, and "
                    "objection handlers before launch day. Concerned about knowledge gaps on "
                    "Fin v2's new pricing model and how it compares to Zendesk AI and Freshdesk Freddy."
                ),
                department="Sales",
                seniority="Manager",
                traits=["field-empathetic", "deadline-driven", "training-focused"],
            ),
            AgentConfig(
                role="Demand Generation Director",
                persona=(
                    "Plans the launch campaign across email, webinars, paid media, and partner "
                    "channels. Focused on pipeline generation targets: $2M in influenced pipeline "
                    "within 30 days of launch. Wants clear audience segmentation for messaging."
                ),
                department="Marketing",
                seniority="Director",
                traits=["metrics-oriented", "campaign-savvy", "audience-segmentation expert"],
            ),
            AgentConfig(
                role="Solutions Engineer",
                persona=(
                    "Builds the technical demo environment and proof-of-concept integrations. "
                    "Knows which Fin v2 features demo well vs. which need careful scoping. "
                    "Advocates for realistic demo scenarios that match customer environments "
                    "(Salesforce, HubSpot, Slack integrations)."
                ),
                department="Sales Engineering",
                seniority="Senior IC",
                traits=["technical depth", "demo perfectionist", "customer-scenario focused"],
            ),
            AgentConfig(
                role="VP of Customer Success",
                persona=(
                    "Responsible for existing customer adoption of Fin v2. Wants a migration "
                    "path from Fin v1 that doesn't disrupt live support operations. Needs "
                    "customer communication templates and a phased rollout plan for top accounts."
                ),
                department="Customer Success",
                seniority="VP",
                traits=["adoption-focused", "risk-aware", "customer-communication expert"],
            ),
        ],
        constraints=[
            "All messaging must reference specific Fin AI Agent v2 capabilities: multi-turn resolution, CRM actions, 94% accuracy rate",
            "Launch tier must be classified (Tier 1/2/3) with corresponding marketing investment levels",
            "Enablement materials must be ready 2 weeks before launch — agents should plan backward from this deadline",
            "Agents must address existing customer migration separately from new logo acquisition",
            "Demo scenarios must include at least 3 industry verticals (SaaS, Healthcare, E-commerce)",
            "Pricing discussion must reference per-resolution model vs. competitor per-seat pricing",
        ],
        seed_text=(
            "Fin AI Agent v2 go-to-market planning session. The product launches in 6 weeks. "
            "Key new capabilities: multi-turn conversation resolution (not just deflection), "
            "live CRM data pulls from Salesforce and HubSpot, action execution (refunds, subscription "
            "changes, ticket escalation), and custom workflow triggers via Intercom Workflows 2.0. "
            "Internal benchmark shows 94% resolution accuracy on trained topics, up from 68% in v1. "
            "The launch needs to drive $2M in influenced pipeline within 30 days while migrating "
            "1,200 existing Fin v1 customers without disrupting their live support operations. "
            "Zendesk AI and Freshdesk Freddy are expected to announce competing features within "
            "the same quarter."
        ),
    ),

    # 4. Churn Prevention
    ScenarioTemplate(
        id="churn_prevention",
        name="Churn Prevention",
        description="CS, Sales, and Product collaborate to save 5 at-risk enterprise accounts representing $890K in ARR, diagnosing root causes and proposing interventions.",
        environment_type="account_review",
        num_rounds=6,
        agent_configs=[
            AgentConfig(
                role="Customer Success Manager",
                persona=(
                    "Manages 3 of the 5 at-risk accounts directly. Has weekly call notes, NPS "
                    "scores, and support ticket trends. Knows the personal dynamics at each account — "
                    "which champions are disengaged, which executives are evaluating competitors. "
                    "Advocates for concession-based retention where justified."
                ),
                department="Customer Success",
                seniority="Senior IC",
                traits=["empathetic", "account-detail oriented", "retention-creative"],
            ),
            AgentConfig(
                role="Account Executive",
                persona=(
                    "Originally sold 2 of the at-risk accounts and maintains executive relationships. "
                    "Believes some accounts need product improvements, not discounts. Pushes back on "
                    "giving away value and wants to explore expansion paths even for at-risk accounts."
                ),
                department="Sales",
                seniority="Senior IC",
                traits=["commercially minded", "relationship leverager", "expansion-oriented"],
            ),
            AgentConfig(
                role="Product Manager",
                persona=(
                    "Owns the Intercom Inbox and Workflows product areas. Has context on which "
                    "feature requests from at-risk accounts are on the roadmap vs. deprioritized. "
                    "Can offer early access to beta features (Workflows 2.0, custom reporting) "
                    "as a retention lever."
                ),
                department="Product",
                seniority="Manager",
                traits=["roadmap-aware", "trade-off thinker", "beta-access strategic"],
            ),
            AgentConfig(
                role="VP of Customer Success",
                persona=(
                    "Accountable for net revenue retention target of 115%. These 5 accounts "
                    "represent 4% of the enterprise book — losing them would drop NRR below "
                    "target. Makes final calls on retention offers, executive escalations, and "
                    "account restructuring."
                ),
                department="Customer Success",
                seniority="VP",
                traits=["NRR-focused", "decisive", "executive-escalation skilled"],
            ),
        ],
        constraints=[
            "Each at-risk account must have a distinct churn reason (pricing, product gaps, champion loss, competitor threat, poor adoption)",
            "Agents must reference specific Intercom products causing friction (Inbox limitations, Fin accuracy, reporting gaps)",
            "Retention offers must be tiered: standard (contract flex), elevated (discount + feature access), executive (custom terms)",
            "At least one account should be recommended for graceful offboarding rather than retention at any cost",
            "Product Manager must commit to or decline specific feature requests with realistic timelines",
        ],
        seed_text=(
            "Enterprise churn prevention review. Five accounts flagged as high churn risk in the "
            "next 90 days, representing $890K in combined ARR. Account A ($240K, Series D fintech) — "
            "champion departed, new VP evaluating Zendesk. Account B ($180K, healthcare SaaS) — "
            "frustrated with Fin AI accuracy on medical terminology, escalated to executive sponsor. "
            "Account C ($195K, e-commerce) — citing budget cuts, wants 30% discount or will consolidate "
            "to HubSpot Service Hub. Account D ($160K, enterprise manufacturing) — low adoption, only "
            "using Inbox and ignoring Workflows, Help Center, and Fin. Account E ($115K, mid-market "
            "edtech) — contract renewal in 45 days, unresponsive to CS outreach for 3 weeks."
        ),
    ),

    # 5. Budget Allocation
    ScenarioTemplate(
        id="budget_allocation",
        name="Budget Allocation",
        description="Leadership team allocates $4.2M Q1 marketing budget across channels, debating ROI attribution, brand vs. demand trade-offs, and pipeline targets.",
        environment_type="leadership_meeting",
        num_rounds=8,
        agent_configs=[
            AgentConfig(
                role="Chief Marketing Officer",
                persona=(
                    "Owns the full $4.2M quarterly marketing budget. Balancing board pressure "
                    "for efficient pipeline generation with long-term brand investments. Believes "
                    "Intercom's brand awareness gap versus Zendesk is the biggest strategic risk."
                ),
                department="Marketing",
                seniority="C-Suite",
                traits=["big-picture thinker", "board-conscious", "brand-investment advocate"],
            ),
            AgentConfig(
                role="VP of Demand Generation",
                persona=(
                    "Runs paid media, SEM, webinars, and content syndication. Last quarter generated "
                    "$12M in marketing-sourced pipeline on $3.8M spend. Wants to increase paid search "
                    "and LinkedIn spend based on CAC payback improvements. Has channel-level ROI data."
                ),
                department="Marketing",
                seniority="VP",
                traits=["data-driven", "channel-ROI focused", "performance-marketing expert"],
            ),
            AgentConfig(
                role="VP of Product Marketing",
                persona=(
                    "Needs budget for Fin AI Agent v2 launch, competitive programs, and analyst "
                    "relations (Gartner, Forrester). Argues that product marketing spend is "
                    "underfunded relative to the launch calendar. Wants to invest in customer "
                    "evidence programs (case studies, G2 reviews)."
                ),
                department="Product Marketing",
                seniority="VP",
                traits=["launch-calendar driven", "analyst-relations savvy", "evidence-focused"],
            ),
            AgentConfig(
                role="VP of Sales",
                persona=(
                    "Represents the field's perspective on marketing effectiveness. Wants more "
                    "investment in account-based marketing for enterprise deals and sales enablement "
                    "content. Skeptical of brand spend that doesn't directly generate pipeline."
                ),
                department="Sales",
                seniority="VP",
                traits=["pipeline-hungry", "ABM advocate", "ROI skeptic on brand"],
            ),
            AgentConfig(
                role="Chief Financial Officer",
                persona=(
                    "Enforces budget discipline and payback period targets. Requires every channel "
                    "to show CAC payback under 18 months. Pushes for reallocation from underperforming "
                    "channels. Will approve incremental budget only with clear pipeline-to-revenue "
                    "conversion evidence."
                ),
                department="Finance",
                seniority="C-Suite",
                traits=["fiscal discipline", "payback-period focused", "evidence-demanding"],
            ),
        ],
        constraints=[
            "Total budget must not exceed $4.2M — any increase in one channel requires a decrease elsewhere",
            "Agents must reference specific marketing channels: paid search, LinkedIn Ads, content syndication, webinars, events, ABM, analyst relations",
            "At least 15% of budget must be allocated to brand/awareness (CMO non-negotiable)",
            "CFO requires CAC payback data for any channel receiving more than $500K",
            "The Fin AI Agent v2 launch must receive dedicated launch budget — not absorbed into existing programs",
            "Agents should debate at least one channel proposed for reduction or elimination",
        ],
        seed_text=(
            "Q1 marketing budget allocation meeting. Total budget: $4.2M (up 10% from Q4). "
            "Last quarter's results: $12M marketing-sourced pipeline, $3.2M in closed-won revenue, "
            "blended CAC of $18K with 14-month payback. Top-performing channels: paid search ($4.2 "
            "pipeline per $1 spent), LinkedIn Ads ($3.1), webinars ($2.8). Underperforming: trade "
            "events ($0.9), content syndication ($1.4). Upcoming priorities: Fin AI Agent v2 launch "
            "(6 weeks out), Gartner Magic Quadrant submission (Q1 deadline), and 3 enterprise ABM "
            "campaigns targeting financial services vertical. The board wants marketing-sourced "
            "pipeline to reach $15M this quarter while maintaining CAC payback under 18 months."
        ),
    ),

    # 6. MRR Reconciliation Investigation
    ScenarioTemplate(
        id="mrr_reconciliation",
        name="MRR Reconciliation Investigation",
        description="Finance and Ops investigate a $340K discrepancy between billing system MRR and Salesforce reported MRR, tracing root causes across systems.",
        environment_type="investigation",
        num_rounds=6,
        agent_configs=[
            AgentConfig(
                role="Finance Analyst",
                persona=(
                    "Discovered the $340K MRR discrepancy during month-end close. Has detailed "
                    "Stripe billing data showing actual collected revenue vs. Salesforce opportunity "
                    "amounts. Methodical about tracing every dollar and documenting audit trails. "
                    "Suspects a combination of mid-cycle upgrades and manual discount overrides."
                ),
                department="Finance",
                seniority="Senior IC",
                traits=["meticulous", "audit-trail obsessed", "spreadsheet wizard"],
            ),
            AgentConfig(
                role="Revenue Operations Manager",
                persona=(
                    "Owns the Salesforce-to-Stripe data pipeline and CPQ (Configure, Price, Quote) "
                    "configuration. Knows where the integration breaks: custom discount fields that "
                    "don't sync, multi-year contracts with annual escalators, and usage-based "
                    "Fin AI Agent billing that reconciles monthly."
                ),
                department="Revenue Operations",
                seniority="Manager",
                traits=["systems-thinker", "integration-expert", "root-cause hunter"],
            ),
            AgentConfig(
                role="VP of Sales",
                persona=(
                    "Concerned about forecast accuracy implications. If MRR reporting is off by "
                    "$340K, the board deck numbers may need revision. Wants to understand whether "
                    "the discrepancy inflates or deflates reported numbers and the timeline to fix."
                ),
                department="Sales",
                seniority="VP",
                traits=["board-reporting conscious", "urgency-driven", "accountability-focused"],
            ),
            AgentConfig(
                role="Engineering Lead",
                persona=(
                    "Maintains the billing integration between Intercom's internal systems, Stripe, "
                    "and Salesforce. Has access to sync logs, webhook failure records, and can trace "
                    "specific transaction mismatches. Knows about 3 known edge cases in the billing "
                    "sync that were deprioritized last quarter."
                ),
                department="Engineering",
                seniority="Lead",
                traits=["technically deep", "log-diving expert", "honest about tech debt"],
            ),
        ],
        constraints=[
            "The $340K discrepancy must be broken down into at least 3 distinct root causes by the end of the simulation",
            "Agents must reference real billing concepts: MRR vs. ARR, expansion MRR, contraction MRR, churn MRR, usage-based billing",
            "Engineering Lead must identify at least 2 technical root causes (sync failures, edge cases, webhook drops)",
            "Finance Analyst must present transaction-level evidence, not just summary totals",
            "The investigation must produce a remediation plan with owners and timelines for each root cause",
            "Agents should consider whether the discrepancy affects previously reported board metrics",
        ],
        seed_text=(
            "MRR reconciliation investigation. During February month-end close, Finance identified "
            "a $340K discrepancy between Stripe billing system MRR ($8.94M) and Salesforce reported "
            "MRR ($9.28M). Salesforce is reporting higher, which means either revenue is being "
            "over-reported to the board or billing is under-collecting. Initial analysis points to "
            "three areas: (1) 47 accounts with mid-cycle plan changes where Stripe prorated but "
            "Salesforce didn't update until renewal, (2) 12 enterprise accounts on custom contracts "
            "with manual discount overrides in Salesforce that don't flow to Stripe CPQ, and "
            "(3) Fin AI Agent usage-based billing for 89 accounts where consumption charges lag "
            "by 30 days. The CFO needs a root cause analysis and remediation plan before the "
            "board meeting in 10 days."
        ),
    ),
]


class ScenarioTemplateService:
    """Service for accessing pre-built simulation scenario templates."""

    _templates_by_id: Dict[str, ScenarioTemplate] = {t.id: t for t in TEMPLATES}

    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """Return summary list of all available templates."""
        return [t.to_summary() for t in TEMPLATES]

    @classmethod
    def get_template(cls, template_id: str) -> Optional[ScenarioTemplate]:
        """Return a specific template by ID, or None if not found."""
        return cls._templates_by_id.get(template_id)

    @classmethod
    def get_template_ids(cls) -> List[str]:
        """Return all available template IDs."""
        return [t.id for t in TEMPLATES]
