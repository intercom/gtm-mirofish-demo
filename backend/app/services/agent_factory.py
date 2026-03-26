"""
OASIS Agent Factory

Creates simulation agents from multiple sources:
- GTM archetypes (pre-built persona templates for common GTM roles)
- Custom persona specifications
- Batch creation with firmographic distribution

Produces OasisAgentProfile objects compatible with the existing simulation pipeline.
"""

import random
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import Config
from ..utils.logger import get_logger
from .oasis_profile_generator import OasisAgentProfile

logger = get_logger('mirofish.agent_factory')

# ---------------------------------------------------------------------------
# GTM Agent Archetypes
# ---------------------------------------------------------------------------
# Each archetype defines a GTM persona template with role-specific attributes.
# These can be instantiated into OasisAgentProfile objects without a Zep graph.

ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "cfo": {
        "id": "cfo",
        "name": "CFO",
        "title": "Chief Financial Officer",
        "category": "executive",
        "description": "Budget-focused executive concerned with ROI, cost containment, and vendor consolidation.",
        "persona_template": (
            "You are a Chief Financial Officer at a {segment} company. "
            "You evaluate all software purchases through a financial lens — TCO, ROI payback period, "
            "and budget predictability matter more than feature richness. "
            "You push back on price increases and demand clear value justification. "
            "You are aware of competitor pricing from {competitors} and use it as leverage. "
            "Communication style: data-driven, concise, skeptical of marketing claims."
        ),
        "bio_template": "CFO | {segment} | Focused on operational efficiency and cost optimization",
        "default_attrs": {
            "profession": "Chief Financial Officer",
            "interested_topics": ["pricing", "ROI", "budget", "vendor management", "cost optimization"],
            "influence_weight": 1.4,
            "sentiment_bias": -0.1,
            "stance": "opposing",
        },
    },
    "vp_operations": {
        "id": "vp_operations",
        "name": "VP Operations",
        "title": "Vice President of Operations",
        "category": "executive",
        "description": "Operational leader focused on workflow efficiency, uptime, and team productivity.",
        "persona_template": (
            "You are a VP of Operations at a {segment} company. "
            "You care about tool reliability, integration quality, and how changes affect daily workflows. "
            "You have 5+ years of experience with Intercom and strong opinions about the product direction. "
            "Price changes concern you less than service disruption or feature removal. "
            "Communication style: practical, detail-oriented, focused on implementation impact."
        ),
        "bio_template": "VP Operations | {segment} | Building scalable operational processes",
        "default_attrs": {
            "profession": "VP Operations",
            "interested_topics": ["operations", "workflow", "integrations", "uptime", "team productivity"],
            "influence_weight": 1.2,
            "sentiment_bias": 0.0,
            "stance": "neutral",
        },
    },
    "cx_leader": {
        "id": "cx_leader",
        "name": "CX Leader",
        "title": "Customer Experience Leader",
        "category": "leadership",
        "description": "Customer experience champion who evaluates tools by their impact on CSAT and customer outcomes.",
        "persona_template": (
            "You are a Customer Experience Leader at a {segment} company. "
            "You evaluate every product change through the lens of customer impact — CSAT scores, "
            "resolution times, and customer effort scores are your north star metrics. "
            "You are vocal about changes that degrade the customer experience and champion features "
            "that improve self-service and personalization. "
            "Communication style: empathetic, customer-centric, passionate about outcomes."
        ),
        "bio_template": "CX Leader | {segment} | Obsessed with customer outcomes and experience",
        "default_attrs": {
            "profession": "Customer Experience Leader",
            "interested_topics": ["customer experience", "CSAT", "NPS", "self-service", "personalization"],
            "influence_weight": 1.1,
            "sentiment_bias": 0.1,
            "stance": "neutral",
        },
    },
    "product_manager": {
        "id": "product_manager",
        "name": "Product Manager",
        "title": "Product Manager",
        "category": "product",
        "description": "Technical product leader who evaluates platforms by API quality, extensibility, and roadmap.",
        "persona_template": (
            "You are a Product Manager at a {segment} company. "
            "You evaluate tools on API quality, extensibility, and alignment with your product roadmap. "
            "You care about data portability, webhook reliability, and custom integration capabilities. "
            "You actively compare features with {competitors} and maintain a detailed switching cost analysis. "
            "Communication style: analytical, technically fluent, roadmap-focused."
        ),
        "bio_template": "PM | {segment} | Building product experiences with the right tools",
        "default_attrs": {
            "profession": "Product Manager",
            "interested_topics": ["product strategy", "API", "integrations", "roadmap", "competitive analysis"],
            "influence_weight": 1.0,
            "sentiment_bias": 0.0,
            "stance": "neutral",
        },
    },
    "support_manager": {
        "id": "support_manager",
        "name": "Support Manager",
        "title": "Support Manager",
        "category": "operations",
        "description": "Front-line support leader managing ticket volumes, SLAs, and agent efficiency.",
        "persona_template": (
            "You are a Support Manager at a {segment} company managing a team of {team_size} agents. "
            "You measure success by first-response time, resolution rate, and agent utilization. "
            "You depend heavily on automation features and are sensitive to changes in bot capabilities. "
            "You share frustrations publicly when tools create friction for your team. "
            "Communication style: direct, metrics-driven, protective of team workflows."
        ),
        "bio_template": "Support Manager | {segment} | Leading a team of {team_size} support agents",
        "default_attrs": {
            "profession": "Support Manager",
            "interested_topics": ["support operations", "SLA", "automation", "ticket management", "agent training"],
            "influence_weight": 0.9,
            "sentiment_bias": 0.0,
            "stance": "neutral",
        },
    },
    "sdr": {
        "id": "sdr",
        "name": "SDR",
        "title": "Sales Development Representative",
        "category": "sales",
        "description": "Outbound sales rep using Intercom for prospecting, live chat, and lead qualification.",
        "persona_template": (
            "You are a Sales Development Representative at a {segment} company. "
            "You use Intercom daily for live chat engagement, lead qualification, and outbound sequences. "
            "You care about response speed, lead routing accuracy, and integration with your CRM. "
            "You are early-career, social-media savvy, and share both positive and negative tool experiences online. "
            "Communication style: enthusiastic, quick, metric-focused (meetings booked, pipeline created)."
        ),
        "bio_template": "SDR | {segment} | Driving pipeline through conversational selling",
        "default_attrs": {
            "profession": "Sales Development Representative",
            "interested_topics": ["sales", "pipeline", "lead generation", "CRM", "outbound"],
            "influence_weight": 0.7,
            "sentiment_bias": 0.1,
            "stance": "supportive",
        },
    },
    "account_executive": {
        "id": "account_executive",
        "name": "Account Executive",
        "title": "Account Executive",
        "category": "sales",
        "description": "Quota-carrying sales rep focused on deal velocity, feature demonstrations, and competitive positioning.",
        "persona_template": (
            "You are an Account Executive at a {segment} company. "
            "You sell using Intercom as a differentiator and need the product to look strong in demos. "
            "You are sensitive to pricing changes that affect deal negotiations and competitive positioning. "
            "You track wins and losses against {competitors} and feed insights back to product. "
            "Communication style: persuasive, relationship-oriented, commercially minded."
        ),
        "bio_template": "AE | {segment} | Closing deals and building lasting partnerships",
        "default_attrs": {
            "profession": "Account Executive",
            "interested_topics": ["sales", "deals", "competitive positioning", "demos", "negotiations"],
            "influence_weight": 0.9,
            "sentiment_bias": 0.0,
            "stance": "neutral",
        },
    },
    "cs_manager": {
        "id": "cs_manager",
        "name": "Customer Success Manager",
        "title": "Customer Success Manager",
        "category": "customer_success",
        "description": "Retention-focused CSM who monitors health scores, adoption, and expansion opportunities.",
        "persona_template": (
            "You are a Customer Success Manager at a {segment} company. "
            "You own a book of {book_size} accounts and monitor health scores, adoption metrics, and renewal risk. "
            "You are the first to hear customer complaints about pricing or feature changes. "
            "You advocate internally for customer needs and flag churn risks early. "
            "Communication style: empathetic, proactive, data-informed."
        ),
        "bio_template": "CSM | {segment} | Driving customer retention and expansion",
        "default_attrs": {
            "profession": "Customer Success Manager",
            "interested_topics": ["retention", "customer health", "adoption", "renewal", "expansion"],
            "influence_weight": 0.8,
            "sentiment_bias": 0.1,
            "stance": "supportive",
        },
    },
    "marketing_director": {
        "id": "marketing_director",
        "name": "Marketing Director",
        "title": "Marketing Director",
        "category": "marketing",
        "description": "Demand generation leader using Intercom for messaging campaigns, user engagement, and analytics.",
        "persona_template": (
            "You are a Marketing Director at a {segment} company. "
            "You use Intercom for in-app messaging, targeted campaigns, and user engagement analytics. "
            "You evaluate the platform on segmentation capabilities, A/B testing, and attribution clarity. "
            "You benchmark against {competitors} marketing features and track industry trends. "
            "Communication style: strategic, brand-conscious, metrics-obsessed."
        ),
        "bio_template": "Marketing Director | {segment} | Growing through data-driven engagement",
        "default_attrs": {
            "profession": "Marketing Director",
            "interested_topics": ["marketing", "campaigns", "analytics", "segmentation", "engagement"],
            "influence_weight": 1.0,
            "sentiment_bias": 0.0,
            "stance": "neutral",
        },
    },
    "revops_lead": {
        "id": "revops_lead",
        "name": "RevOps Lead",
        "title": "Revenue Operations Lead",
        "category": "operations",
        "description": "Revenue operations specialist focused on data integrity, funnel optimization, and tool consolidation.",
        "persona_template": (
            "You are a Revenue Operations Lead at a {segment} company. "
            "You own the tech stack and optimize the revenue funnel across marketing, sales, and CS. "
            "You evaluate tools on data quality, integration depth, and total cost of ownership. "
            "You are the decision-maker for tool consolidation and vendor negotiations. "
            "Communication style: systematic, data-obsessed, integration-focused."
        ),
        "bio_template": "RevOps | {segment} | Optimizing the revenue engine end-to-end",
        "default_attrs": {
            "profession": "Revenue Operations Lead",
            "interested_topics": ["RevOps", "tech stack", "data integrity", "funnel optimization", "integrations"],
            "influence_weight": 1.1,
            "sentiment_bias": -0.05,
            "stance": "neutral",
        },
    },
}

# Segments for firmographic distribution
SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]

# Competitors referenced in persona templates
COMPETITORS = ["Zendesk", "Freshdesk", "HubSpot Service Hub", "Salesforce Service Cloud", "Help Scout"]

# MBTI types for random assignment
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

COUNTRIES = ["US", "UK", "Canada", "Australia", "Germany", "France", "India", "Brazil", "Japan"]


def _seed_rng(seed_str: str) -> random.Random:
    """Create a deterministic RNG from a string seed."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


class AgentFactory:
    """
    Factory for creating OASIS simulation agents from GTM archetypes.

    Supports:
    - Single agent creation from an archetype + overrides
    - Batch creation with firmographic distribution
    - LLM-enhanced persona generation (optional)
    - Demo/mock mode when no LLM key is configured
    """

    def __init__(self):
        self._llm_client = None

    @property
    def llm_available(self) -> bool:
        return bool(Config.LLM_API_KEY)

    def _get_llm_client(self):
        if self._llm_client is None and self.llm_available:
            from ..utils.llm_client import LLMClient
            self._llm_client = LLMClient()
        return self._llm_client

    # ------------------------------------------------------------------
    # Public: archetype registry
    # ------------------------------------------------------------------

    @staticmethod
    def list_archetypes() -> List[Dict[str, Any]]:
        """Return all available archetypes (metadata only, no templates)."""
        return [
            {
                "id": a["id"],
                "name": a["name"],
                "title": a["title"],
                "category": a["category"],
                "description": a["description"],
                "default_topics": a["default_attrs"].get("interested_topics", []),
            }
            for a in ARCHETYPES.values()
        ]

    @staticmethod
    def get_archetype(archetype_id: str) -> Optional[Dict[str, Any]]:
        """Return full archetype definition by ID."""
        return ARCHETYPES.get(archetype_id)

    # ------------------------------------------------------------------
    # Public: single agent creation
    # ------------------------------------------------------------------

    def create_agent(
        self,
        archetype_id: str,
        user_id: int,
        *,
        segment: str = "Mid-Market",
        overrides: Optional[Dict[str, Any]] = None,
        use_llm: bool = False,
    ) -> OasisAgentProfile:
        """
        Create a single agent from an archetype.

        Args:
            archetype_id: Key in ARCHETYPES
            user_id: Numeric user ID for the OASIS profile
            segment: Company segment (SMB / Mid-Market / Enterprise)
            overrides: Optional dict to override any profile field
            use_llm: Whether to call LLM for richer persona text
        """
        archetype = ARCHETYPES.get(archetype_id)
        if not archetype:
            raise ValueError(f"Unknown archetype: {archetype_id}")

        overrides = overrides or {}
        rng = _seed_rng(f"{archetype_id}_{user_id}_{segment}")

        # Template variables
        team_size = rng.choice([5, 8, 12, 15, 20, 30])
        book_size = rng.choice([30, 50, 80, 120])
        competitors = ", ".join(rng.sample(COMPETITORS, k=min(3, len(COMPETITORS))))
        tmpl_vars = {
            "segment": segment,
            "competitors": competitors,
            "team_size": str(team_size),
            "book_size": str(book_size),
        }

        # Build persona and bio from templates
        persona = archetype["persona_template"].format(**tmpl_vars)
        bio = archetype["bio_template"].format(**tmpl_vars)

        # Optionally enrich with LLM
        if use_llm and self.llm_available:
            persona = self._enrich_persona_with_llm(archetype, persona, segment)

        defaults = archetype["default_attrs"]
        name = overrides.get("name") or self._generate_name(archetype_id, user_id, rng)
        username = self._generate_username(name, rng)

        # Firmographic-adjusted social stats
        karma_base = {"SMB": 800, "Mid-Market": 2000, "Enterprise": 4000}.get(segment, 1500)
        follower_base = {"SMB": 100, "Mid-Market": 500, "Enterprise": 2000}.get(segment, 300)

        profile = OasisAgentProfile(
            user_id=user_id,
            user_name=username,
            name=name,
            bio=overrides.get("bio", bio),
            persona=overrides.get("persona", persona),
            karma=overrides.get("karma", karma_base + rng.randint(-200, 500)),
            friend_count=overrides.get("friend_count", rng.randint(50, 500)),
            follower_count=overrides.get("follower_count", follower_base + rng.randint(-50, 300)),
            statuses_count=overrides.get("statuses_count", rng.randint(100, 3000)),
            age=overrides.get("age", rng.randint(28, 55)),
            gender=overrides.get("gender", rng.choice(["male", "female", "non-binary"])),
            mbti=overrides.get("mbti", rng.choice(MBTI_TYPES)),
            country=overrides.get("country", rng.choice(COUNTRIES)),
            profession=defaults.get("profession"),
            interested_topics=overrides.get("interested_topics", defaults.get("interested_topics", [])),
        )
        return profile

    # ------------------------------------------------------------------
    # Public: batch creation
    # ------------------------------------------------------------------

    def create_batch(
        self,
        distribution: List[Dict[str, Any]],
        *,
        use_llm: bool = False,
        start_user_id: int = 1,
    ) -> List[OasisAgentProfile]:
        """
        Create a batch of agents from a distribution spec.

        Args:
            distribution: List of dicts, each with:
                - archetype_id (str): archetype key
                - count (int): number of agents to create
                - segment (str, optional): defaults to random
                - overrides (dict, optional): per-archetype field overrides
            use_llm: Whether to call LLM for richer personas
            start_user_id: Starting user_id (auto-increments)

        Returns:
            List of OasisAgentProfile
        """
        profiles: List[OasisAgentProfile] = []
        uid = start_user_id

        for spec in distribution:
            archetype_id = spec["archetype_id"]
            count = spec.get("count", 1)
            segment_override = spec.get("segment")
            overrides = spec.get("overrides")

            for i in range(count):
                segment = segment_override or random.choice(SEGMENTS)
                profile = self.create_agent(
                    archetype_id=archetype_id,
                    user_id=uid,
                    segment=segment,
                    overrides=overrides,
                    use_llm=use_llm,
                )
                profiles.append(profile)
                uid += 1

        logger.info(f"Agent factory created {len(profiles)} agents from {len(distribution)} archetype specs")
        return profiles

    def create_from_scenario(
        self,
        scenario_config: Dict[str, Any],
        *,
        use_llm: bool = False,
        start_user_id: int = 1,
    ) -> List[OasisAgentProfile]:
        """
        Create agents from a GTM scenario template's agent_config.

        Reads the persona_types and count from a scenario JSON (e.g. pricing_simulation.json)
        and distributes agents evenly across persona types and segments.

        Args:
            scenario_config: The agent_config section from a GTM scenario
            use_llm: Whether to use LLM for enrichment
            start_user_id: Starting user_id
        """
        persona_types = scenario_config.get("persona_types", [])
        total_count = scenario_config.get("count", 50)
        segments = scenario_config.get("firmographic_mix", {}).get("segments", SEGMENTS)

        if not persona_types:
            persona_types = ["support_manager", "cx_leader", "product_manager"]

        # Map scenario persona names to archetype IDs
        type_to_archetype = self._resolve_persona_types(persona_types)

        # Distribute count across types
        per_type = max(1, total_count // len(type_to_archetype))
        remainder = total_count - per_type * len(type_to_archetype)

        distribution = []
        for i, (_, archetype_id) in enumerate(type_to_archetype.items()):
            count = per_type + (1 if i < remainder else 0)
            # Rotate through segments
            segment = segments[i % len(segments)] if segments else None
            distribution.append({
                "archetype_id": archetype_id,
                "count": count,
                "segment": segment,
            })

        return self.create_batch(
            distribution,
            use_llm=use_llm,
            start_user_id=start_user_id,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_persona_types(self, persona_types: List[str]) -> Dict[str, str]:
        """Map human-readable persona type names to archetype IDs."""
        mapping: Dict[str, str] = {}
        # Build a lookup from name/title variations to archetype ID
        lookup: Dict[str, str] = {}
        for aid, arch in ARCHETYPES.items():
            lookup[aid] = aid
            lookup[arch["name"].lower()] = aid
            lookup[arch["title"].lower()] = aid

        for pt in persona_types:
            key = pt.lower().strip()
            matched = lookup.get(key)
            if not matched:
                # Fuzzy: check if any archetype name is contained in the persona type
                for name, aid in lookup.items():
                    if name in key or key in name:
                        matched = aid
                        break
            if matched:
                mapping[pt] = matched
            else:
                # Default to support_manager for unrecognized types
                logger.warning(f"Unknown persona type '{pt}', defaulting to support_manager")
                mapping[pt] = "support_manager"

        return mapping

    @staticmethod
    def _generate_name(archetype_id: str, user_id: int, rng: random.Random) -> str:
        """Generate a plausible name for an agent."""
        first_names = [
            "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery",
            "Cameron", "Dakota", "Emery", "Finley", "Harper", "Jesse", "Kendall",
            "Logan", "Parker", "Reese", "Sage", "Drew", "Blake", "Charlie", "Sam",
            "Jamie", "Skyler", "Robin", "Hayden", "Peyton", "Rowan", "Elliot",
        ]
        last_names = [
            "Chen", "Patel", "Johnson", "Kim", "Rodriguez", "Nakamura", "O'Brien",
            "Larsson", "Muller", "Santos", "Williams", "Lee", "Garcia", "Martinez",
            "Brown", "Davis", "Wilson", "Anderson", "Taylor", "Thomas", "Moore",
            "Jackson", "White", "Harris", "Clark", "Lewis", "Young", "Hall", "Scott",
        ]
        return f"{rng.choice(first_names)} {rng.choice(last_names)}"

    @staticmethod
    def _generate_username(name: str, rng: random.Random) -> str:
        """Generate a username from a display name."""
        base = name.lower().replace(" ", "_")
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        return f"{base}_{rng.randint(100, 999)}"

    def _enrich_persona_with_llm(
        self,
        archetype: Dict[str, Any],
        base_persona: str,
        segment: str,
    ) -> str:
        """Use LLM to expand a template persona into a richer, more detailed version."""
        client = self._get_llm_client()
        if not client:
            return base_persona

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a GTM persona generator. Given a base persona description, "
                    "expand it into a vivid, detailed character profile (150-250 words). "
                    "Include: background story, specific motivations, communication quirks, "
                    "and how they evaluate software vendors. Keep it in second person ('You are...'). "
                    "Return ONLY the expanded persona text, nothing else."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Role: {archetype['title']}\n"
                    f"Segment: {segment}\n"
                    f"Base persona:\n{base_persona}"
                ),
            },
        ]

        try:
            return client.chat(messages=messages, temperature=0.8, max_tokens=500)
        except Exception as e:
            logger.warning(f"LLM enrichment failed, using template: {e}")
            return base_persona
