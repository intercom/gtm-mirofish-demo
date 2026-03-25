"""
PersonaGenerator — synthesize GTM buyer personas from Zep knowledge graph data.

Extracts entities (companies, products, people, market conditions) from a Zep
graph and uses an LLM to produce rich personas grounded in real graph facts.
Falls back to pre-built templates when Zep/LLM are unavailable.
"""

import json
import os
import random
import uuid as uuid_lib
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.persona_generator')

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')

PERSONALITY_TRAITS = [
    "analytical", "assertive", "cautious", "collaborative", "competitive",
    "creative", "data-driven", "decisive", "detail-oriented", "diplomatic",
    "empathetic", "innovative", "methodical", "pragmatic", "risk-averse",
    "risk-tolerant", "skeptical", "strategic", "visionary",
]

FIRST_NAMES = [
    "Alex", "Jordan", "Morgan", "Casey", "Taylor", "Riley", "Avery",
    "Quinn", "Cameron", "Drew", "Sage", "Reese", "Dakota", "Jamie",
    "Kai", "Rowan", "Skyler", "Finley", "Harper", "Emery",
]

LAST_NAMES = [
    "Chen", "Patel", "Kim", "Mueller", "Santos", "Okafor", "Johansson",
    "Moreau", "Tanaka", "Williams", "Garcia", "Singh", "Novak", "Rivera",
    "Thompson", "Berg", "Nakamura", "Fernandez", "O'Brien", "Larsson",
]

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]


def _load_json(filepath: str) -> Optional[Any]:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


@dataclass
class Persona:
    """A GTM buyer persona with graph-grounded context."""
    id: str
    name: str
    title: str
    department: str
    personality_traits: List[str]
    expertise_areas: List[str]
    biases: List[str]
    known_facts: List[str]
    goals: List[str]
    communication_style: str
    decision_authority: str
    typical_objections: List[str]
    firmographic: Dict[str, Any] = field(default_factory=dict)
    mbti: Optional[str] = None
    source: str = "template"  # "zep_graph" | "template" | "custom"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PersonaGenerator:
    """
    Generate GTM buyer personas from Zep graph data.

    Three main entry points:
      - generate_from_graph(role, graph_id, scenario_context)
      - enhance_persona(base_persona, simulation_context)
      - generate_team(scenario, num_agents)
    """

    def __init__(self):
        self._templates = None
        self._account_profiles = None
        self._llm = None
        self._entity_reader = None

    # ------------------------------------------------------------------
    # Lazy loaders — avoid import/init errors when keys are missing
    # ------------------------------------------------------------------

    @property
    def templates(self) -> List[Dict[str, Any]]:
        if self._templates is None:
            data = _load_json(os.path.join(SEED_DATA_DIR, 'persona_templates.json'))
            self._templates = data.get("personas", []) if data else []
        return self._templates

    @property
    def account_profiles(self) -> List[Dict[str, Any]]:
        if self._account_profiles is None:
            data = _load_json(os.path.join(SEED_DATA_DIR, 'account_profiles.json'))
            self._account_profiles = data.get("profiles", []) if data else []
        return self._account_profiles

    def _get_llm(self):
        if self._llm is None:
            from ..utils.llm_client import LLMClient
            self._llm = LLMClient()
        return self._llm

    def _get_entity_reader(self):
        if self._entity_reader is None:
            from .zep_entity_reader import ZepEntityReader
            self._entity_reader = ZepEntityReader()
        return self._entity_reader

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_from_graph(
        self,
        role: str,
        graph_id: str,
        scenario_context: Optional[Dict[str, Any]] = None,
    ) -> Persona:
        """
        Generate a single persona for *role* using entities from the Zep graph.

        Falls back to template-based generation when Zep or LLM are unavailable.
        """
        graph_context = self._extract_graph_context(graph_id)
        if graph_context and Config.LLM_API_KEY:
            return self._generate_with_llm(role, graph_context, scenario_context)
        return self._generate_from_template(role, scenario_context)

    def enhance_persona(
        self,
        base_persona: Persona,
        simulation_context: Dict[str, Any],
    ) -> Persona:
        """Add simulation-specific context to an existing persona."""
        if not Config.LLM_API_KEY:
            return base_persona

        try:
            llm = self._get_llm()
            messages = [
                {"role": "system", "content": (
                    "You enhance GTM buyer personas with simulation-specific context. "
                    "Return valid JSON matching the input schema, with richer goals, "
                    "biases, and known_facts that reflect the simulation scenario."
                )},
                {"role": "user", "content": json.dumps({
                    "persona": base_persona.to_dict(),
                    "simulation_context": simulation_context,
                    "instruction": (
                        "Enhance this persona for the given simulation. "
                        "Add 1-2 new goals, biases, or known_facts that reflect "
                        "the simulation context. Keep all existing fields."
                    ),
                })},
            ]
            result = llm.chat_json(messages, temperature=0.5)
            persona_data = result.get("persona", result)
            return self._dict_to_persona(persona_data, source=base_persona.source)
        except Exception as e:
            logger.warning(f"Persona enhancement failed, returning original: {e}")
            return base_persona

    def generate_team(
        self,
        scenario: Dict[str, Any],
        num_agents: int = 10,
    ) -> List[Persona]:
        """
        Generate a balanced team of personas for a scenario.

        Uses graph data when graph_id is available in the scenario,
        otherwise falls back to templates.
        """
        agent_config = scenario.get("agent_config", {})
        persona_types = agent_config.get("persona_types", [])
        if not persona_types:
            persona_types = [t["role"] for t in self.templates]

        graph_id = scenario.get("graph_id")
        firmographic_mix = agent_config.get("firmographic_mix", {})

        personas: List[Persona] = []
        for i in range(num_agents):
            role = persona_types[i % len(persona_types)]
            firmo = self._pick_firmographic(firmographic_mix)
            scenario_ctx = {
                "scenario_name": scenario.get("name", ""),
                "scenario_id": scenario.get("id", ""),
                "firmographic": firmo,
            }

            if graph_id and Config.ZEP_API_KEY:
                persona = self.generate_from_graph(role, graph_id, scenario_ctx)
            else:
                persona = self._generate_from_template(role, scenario_ctx)

            persona.firmographic = firmo
            personas.append(persona)

        return personas

    # ------------------------------------------------------------------
    # Graph context extraction
    # ------------------------------------------------------------------

    def _extract_graph_context(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Pull entities and edges from Zep, categorise them for persona synthesis."""
        if not Config.ZEP_API_KEY:
            return None

        try:
            reader = self._get_entity_reader()
            filtered = reader.filter_defined_entities(graph_id, enrich_with_edges=True)

            companies, products, people, market_conditions, competitors = [], [], [], [], []
            for entity in filtered.entities:
                etype = (entity.get_entity_type() or "").lower()
                entry = {
                    "name": entity.name,
                    "summary": entity.summary,
                    "facts": [e.get("fact", "") for e in entity.related_edges if e.get("fact")],
                }
                if etype in ("company", "organization", "account"):
                    companies.append(entry)
                elif etype in ("product", "tool", "software", "platform"):
                    products.append(entry)
                elif etype in ("person", "expert", "publicfigure", "role"):
                    people.append(entry)
                elif etype in ("competitor", "vendor"):
                    competitors.append(entry)
                else:
                    market_conditions.append(entry)

            return {
                "companies": companies,
                "products": products,
                "people": people,
                "market_conditions": market_conditions,
                "competitors": competitors,
                "entity_types": list(filtered.entity_types),
                "total_entities": filtered.filtered_count,
            }
        except Exception as e:
            logger.warning(f"Graph context extraction failed: {e}")
            return None

    # ------------------------------------------------------------------
    # LLM-based generation
    # ------------------------------------------------------------------

    def _generate_with_llm(
        self,
        role: str,
        graph_context: Dict[str, Any],
        scenario_context: Optional[Dict[str, Any]] = None,
    ) -> Persona:
        """Use LLM + graph context to synthesize a rich persona."""
        template = self._find_template(role)
        firmo = (scenario_context or {}).get("firmographic", {})

        system_prompt = (
            "You are a GTM persona generator. Given a role template, graph-extracted "
            "market context, and firmographic data, create a realistic buyer persona. "
            "The persona should feel like a real person making real purchasing decisions.\n\n"
            "Return valid JSON with exactly these fields:\n"
            "name (string), title (string), department (string), "
            "personality_traits (list of 3-5 strings), expertise_areas (list of 3-5 strings), "
            "biases (list of 2-3 strings — cognitive/professional biases that affect decisions), "
            "known_facts (list of 3-5 strings — specific facts from graph context this person would know), "
            "goals (list of 3-5 strings), communication_style (string), "
            "decision_authority (string), typical_objections (list of 2-4 strings), "
            "mbti (string — one of the 16 MBTI types)"
        )

        user_prompt = json.dumps({
            "role": role,
            "template": template,
            "graph_context": {
                "companies": graph_context.get("companies", [])[:5],
                "products": graph_context.get("products", [])[:5],
                "competitors": graph_context.get("competitors", [])[:5],
                "market_conditions": graph_context.get("market_conditions", [])[:5],
            },
            "firmographic": firmo,
        })

        try:
            llm = self._get_llm()
            result = llm.chat_json(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": user_prompt}],
                temperature=0.7,
            )
            persona = self._dict_to_persona(result, source="zep_graph")
            return persona
        except Exception as e:
            logger.warning(f"LLM persona generation failed, using template: {e}")
            return self._generate_from_template(role, scenario_context)

    # ------------------------------------------------------------------
    # Template fallback generation
    # ------------------------------------------------------------------

    def _generate_from_template(
        self,
        role: str,
        scenario_context: Optional[Dict[str, Any]] = None,
    ) -> Persona:
        """Generate a persona from pre-built templates + randomised traits."""
        template = self._find_template(role)
        firmo = (scenario_context or {}).get("firmographic", {})

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        traits = random.sample(PERSONALITY_TRAITS, k=min(4, len(PERSONALITY_TRAITS)))

        return Persona(
            id=str(uuid_lib.uuid4()),
            name=name,
            title=template.get("role", role),
            department=self._infer_department(role),
            personality_traits=traits,
            expertise_areas=template.get("priorities", [])[:4],
            biases=[f"Anchored on {template.get('concerns', ['cost'])[0]}"],
            known_facts=[
                f"Industry: {firmo.get('industry', 'SaaS')}",
                f"Company size: {firmo.get('company_size', '500-1000')}",
            ],
            goals=template.get("priorities", ["improve efficiency"]),
            communication_style=template.get("communication_style", "professional"),
            decision_authority=template.get("decision_authority", "influencer"),
            typical_objections=template.get("typical_objections", []),
            firmographic=firmo,
            mbti=random.choice(MBTI_TYPES),
            source="template",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_template(self, role: str) -> Dict[str, Any]:
        for t in self.templates:
            if t.get("role", "").lower() == role.lower():
                return t
        return self.templates[0] if self.templates else {}

    def _pick_firmographic(self, mix: Dict[str, Any]) -> Dict[str, str]:
        industries = mix.get("industries", ["SaaS"])
        sizes = mix.get("company_sizes", ["500-1000"])
        regions = mix.get("regions", ["North America"])
        profile = random.choice(self.account_profiles) if self.account_profiles else {}
        return {
            "industry": random.choice(industries),
            "company_size": random.choice(sizes),
            "region": random.choice(regions),
            "segment": profile.get("segment", "Mid-Market"),
            "current_tool": profile.get("current_support_tool", ""),
            "arr_range": profile.get("arr_range", ""),
        }

    @staticmethod
    def _infer_department(role: str) -> str:
        role_lower = role.lower()
        if any(k in role_lower for k in ("support", "cx", "customer")):
            return "Customer Experience"
        if any(k in role_lower for k in ("it", "security", "engineering")):
            return "IT / Engineering"
        if any(k in role_lower for k in ("operations", "ops")):
            return "Operations"
        if any(k in role_lower for k in ("sales", "revenue")):
            return "Sales"
        if any(k in role_lower for k in ("marketing",)):
            return "Marketing"
        return "General Management"

    def _dict_to_persona(self, data: Dict[str, Any], source: str = "zep_graph") -> Persona:
        return Persona(
            id=data.get("id", str(uuid_lib.uuid4())),
            name=data.get("name", f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"),
            title=data.get("title", ""),
            department=data.get("department", ""),
            personality_traits=data.get("personality_traits", []),
            expertise_areas=data.get("expertise_areas", []),
            biases=data.get("biases", []),
            known_facts=data.get("known_facts", []),
            goals=data.get("goals", []),
            communication_style=data.get("communication_style", ""),
            decision_authority=data.get("decision_authority", "influencer"),
            typical_objections=data.get("typical_objections", []),
            firmographic=data.get("firmographic", {}),
            mbti=data.get("mbti"),
            source=source,
        )
