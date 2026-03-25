"""
Persona Service
In-memory CRUD and LLM-powered generation for agent personas.
"""

import json
import os
import uuid
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.persona_service')

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')


def _load_persona_templates() -> List[Dict[str, Any]]:
    path = os.path.join(SEED_DATA_DIR, 'persona_templates.json')
    with open(path) as f:
        data = json.load(f)
    return data.get('personas', [])


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# In-memory persona store (keyed by id)
# ---------------------------------------------------------------------------
_personas: Dict[str, Dict[str, Any]] = {}
_initialized = False


def _ensure_initialized():
    """Seed the store with template personas on first access."""
    global _initialized
    if _initialized:
        return
    _initialized = True
    for tmpl in _load_persona_templates():
        pid = str(uuid.uuid4())
        _personas[pid] = {
            'id': pid,
            'name': _generate_name_for_role(tmpl['role']),
            'source': 'template',
            'created_at': _utcnow_iso(),
            'updated_at': _utcnow_iso(),
            **tmpl,
        }
    logger.info("Loaded %d template personas", len(_personas))


_SAMPLE_NAMES = {
    'VP of Support': 'Dana Whitfield',
    'CX Director': 'Marcus Chen',
    'IT Leader': 'Priya Kapoor',
    'Head of Operations': 'Jordan Blake',
}


def _generate_name_for_role(role: str) -> str:
    return _SAMPLE_NAMES.get(role, f"Agent {role}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_personas(source: Optional[str] = None) -> List[Dict[str, Any]]:
    _ensure_initialized()
    personas = list(_personas.values())
    if source:
        personas = [p for p in personas if p.get('source') == source]
    return sorted(personas, key=lambda p: p.get('created_at', ''))


def get_persona(persona_id: str) -> Optional[Dict[str, Any]]:
    _ensure_initialized()
    return _personas.get(persona_id)


def update_persona(persona_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    _ensure_initialized()
    persona = _personas.get(persona_id)
    if persona is None:
        return None
    immutable = {'id', 'created_at'}
    for key, value in updates.items():
        if key not in immutable:
            persona[key] = value
    persona['source'] = 'custom'
    persona['updated_at'] = _utcnow_iso()
    return persona


def clone_persona(persona_id: str, overrides: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    _ensure_initialized()
    original = _personas.get(persona_id)
    if original is None:
        return None
    new_id = str(uuid.uuid4())
    cloned = {
        **original,
        'id': new_id,
        'source': 'custom',
        'created_at': _utcnow_iso(),
        'updated_at': _utcnow_iso(),
    }
    if overrides:
        immutable = {'id', 'created_at'}
        for key, value in overrides.items():
            if key not in immutable:
                cloned[key] = value
    _personas[new_id] = cloned
    return cloned


def generate_personas(
    scenario_type: str,
    num_agents: int = 4,
    role_distribution: Optional[Dict[str, int]] = None,
    personality_diversity: float = 0.5,
) -> List[Dict[str, Any]]:
    """Generate personas using LLM when available, otherwise mock."""
    _ensure_initialized()

    if Config.LLM_API_KEY:
        try:
            return _generate_with_llm(
                scenario_type, num_agents, role_distribution, personality_diversity,
            )
        except Exception:
            logger.exception("LLM persona generation failed, falling back to mock")

    return _generate_mock(scenario_type, num_agents, role_distribution, personality_diversity)


# ---------------------------------------------------------------------------
# LLM generation
# ---------------------------------------------------------------------------

_GENERATE_SYSTEM_PROMPT = """\
You are a GTM simulation persona designer for Intercom.
Given a scenario type and parameters, generate realistic buyer-committee personas.
Return a JSON object with a "personas" array. Each persona must have:
- name (string): realistic full name
- role (string): job title
- seniority (string): one of "executive", "director", "manager", "individual_contributor"
- priorities (array of strings)
- concerns (array of strings)
- decision_authority (string): one of "final_approver", "influencer", "technical_veto", "end_user"
- communication_style (string): brief description
- typical_objections (array of strings)
- bio (string): 2-3 sentence background
- personality_traits (object): keys "openness", "assertiveness", "detail_orientation" each 0.0-1.0
"""


def _generate_with_llm(
    scenario_type: str,
    num_agents: int,
    role_distribution: Optional[Dict[str, int]],
    personality_diversity: float,
) -> List[Dict[str, Any]]:
    from ..utils.llm_client import LLMClient

    client = LLMClient()

    user_msg = json.dumps({
        'scenario_type': scenario_type,
        'num_agents': num_agents,
        'role_distribution': role_distribution,
        'personality_diversity': personality_diversity,
    })

    result = client.chat_json(
        messages=[
            {'role': 'system', 'content': _GENERATE_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_msg},
        ],
        temperature=0.4 + (personality_diversity * 0.5),
    )

    generated = result.get('personas', [])
    personas = []
    for raw in generated[:num_agents]:
        pid = str(uuid.uuid4())
        persona = {
            'id': pid,
            'source': 'generated',
            'created_at': _utcnow_iso(),
            'updated_at': _utcnow_iso(),
            **raw,
        }
        _personas[pid] = persona
        personas.append(persona)

    logger.info("LLM generated %d personas for scenario '%s'", len(personas), scenario_type)
    return personas


# ---------------------------------------------------------------------------
# Mock / demo-mode generation
# ---------------------------------------------------------------------------

_MOCK_BIOS = [
    "Seasoned leader with 15+ years in enterprise SaaS, focused on operational efficiency.",
    "Data-driven executive who transformed support operations at two Fortune 500 companies.",
    "Technical leader passionate about automation and reducing toil in support workflows.",
    "Customer-obsessed director known for building high-performing distributed CX teams.",
]

_MOCK_FIRST = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Quinn', 'Avery']
_MOCK_LAST = ['Park', 'Nakamura', 'Okafor', 'Petrov', 'Martinez', 'Singh', 'Weber', 'Dubois']


def _generate_mock(
    scenario_type: str,
    num_agents: int,
    role_distribution: Optional[Dict[str, int]],
    personality_diversity: float,
) -> List[Dict[str, Any]]:
    templates = _load_persona_templates()
    personas: List[Dict[str, Any]] = []

    roles_to_generate: List[Dict[str, Any]] = []
    if role_distribution:
        tmpl_by_role = {t['role']: t for t in templates}
        for role, count in role_distribution.items():
            base = tmpl_by_role.get(role, templates[0])
            for _ in range(count):
                roles_to_generate.append(dict(base))
    else:
        for i in range(num_agents):
            roles_to_generate.append(dict(templates[i % len(templates)]))

    for i, base in enumerate(roles_to_generate[:num_agents]):
        pid = str(uuid.uuid4())
        spread = personality_diversity
        persona = {
            'id': pid,
            'name': f"{random.choice(_MOCK_FIRST)} {random.choice(_MOCK_LAST)}",
            'source': 'generated',
            'bio': _MOCK_BIOS[i % len(_MOCK_BIOS)],
            'personality_traits': {
                'openness': round(0.5 + random.uniform(-spread, spread) * 0.4, 2),
                'assertiveness': round(0.5 + random.uniform(-spread, spread) * 0.4, 2),
                'detail_orientation': round(0.5 + random.uniform(-spread, spread) * 0.4, 2),
            },
            'created_at': _utcnow_iso(),
            'updated_at': _utcnow_iso(),
            **base,
        }
        _personas[pid] = persona
        personas.append(persona)

    logger.info("Mock generated %d personas for scenario '%s'", len(personas), scenario_type)
    return personas
