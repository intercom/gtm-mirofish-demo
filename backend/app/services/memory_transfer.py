"""
Cross-simulation memory transfer service.

Exports agent memory bundles from completed simulations and imports them
into new simulations, enabling agents to carry learned knowledge across runs.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.memory_transfer')


class MemoryFilterType:
    ALL = "all"
    DECISIONS_ONLY = "decisions_only"
    RELATIONSHIPS_ONLY = "relationships_only"
    FACTS_ONLY = "facts_only"


VALID_FILTERS = {
    MemoryFilterType.ALL,
    MemoryFilterType.DECISIONS_ONLY,
    MemoryFilterType.RELATIONSHIPS_ONLY,
    MemoryFilterType.FACTS_ONLY,
}

# Action types that represent decision-making behavior
DECISION_ACTION_TYPES = {"CREATE_POST", "CREATE_THREAD", "REPLY", "COMMENT"}
# Action types that represent relationship-building behavior
RELATIONSHIP_ACTION_TYPES = {"LIKE", "LIKE_POST", "REPOST", "SHARE", "FOLLOW", "UPVOTE"}


class MemoryTransfer:
    """Manages cross-simulation agent memory export, import, and transfer."""

    BUNDLES_DIR_NAME = "memory_bundles"

    def __init__(self):
        self.sim_data_dir = os.path.join(
            os.path.dirname(__file__), '../../uploads/simulations'
        )
        os.makedirs(self.sim_data_dir, exist_ok=True)

    def _get_bundles_dir(self, simulation_id: str) -> str:
        bundles_dir = os.path.join(self.sim_data_dir, simulation_id, self.BUNDLES_DIR_NAME)
        os.makedirs(bundles_dir, exist_ok=True)
        return bundles_dir

    def _load_run_state(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        run_state_path = os.path.join(self.sim_data_dir, simulation_id, "run_state.json")
        if not os.path.exists(run_state_path):
            return None
        with open(run_state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_profiles(self, simulation_id: str) -> List[Dict[str, Any]]:
        profiles_path = os.path.join(self.sim_data_dir, simulation_id, "profiles.json")
        if not os.path.exists(profiles_path):
            return []
        with open(profiles_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("profiles", data.get("agents", []))

    def _load_state(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        state_path = os.path.join(self.sim_data_dir, simulation_id, "state.json")
        if not os.path.exists(state_path):
            return None
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract_agent_actions(
        self, run_state: Dict[str, Any], agent_id: int
    ) -> List[Dict[str, Any]]:
        """Pull all actions for a specific agent from run state rounds + recent_actions."""
        actions = []
        for round_data in run_state.get("rounds", []):
            for action in round_data.get("actions", []):
                if action.get("agent_id") == agent_id:
                    actions.append(action)
        for action in run_state.get("recent_actions", []):
            if action.get("agent_id") == agent_id:
                if not any(
                    a.get("timestamp") == action.get("timestamp")
                    and a.get("action_type") == action.get("action_type")
                    for a in actions
                ):
                    actions.append(action)
        return actions

    def _build_facts(self, actions: List[Dict[str, Any]], agent_name: str) -> List[Dict[str, Any]]:
        """Extract facts/knowledge from agent actions."""
        facts = []
        for action in actions:
            content = action.get("action_args", {}).get("content", "")
            if not content:
                content = action.get("action_args", {}).get("post_content", "")
            if content and action.get("action_type") in DECISION_ACTION_TYPES:
                facts.append({
                    "content": content,
                    "confidence": 0.8,
                    "source": f"round_{action.get('round_num', 0)}",
                    "platform": action.get("platform", "unknown"),
                    "timestamp": action.get("timestamp", ""),
                })
        return facts

    def _build_decisions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract decisions from agent actions."""
        decisions = []
        for action in actions:
            if action.get("action_type") not in DECISION_ACTION_TYPES:
                continue
            content = action.get("action_args", {}).get("content", "")
            if not content:
                content = action.get("action_args", {}).get("post_content", "")
            decisions.append({
                "action_type": action["action_type"],
                "content": content,
                "round": action.get("round_num", 0),
                "platform": action.get("platform", "unknown"),
                "context": {
                    "post_author": action.get("action_args", {}).get("post_author_name", ""),
                    "result": action.get("result", ""),
                },
                "timestamp": action.get("timestamp", ""),
            })
        return decisions

    def _build_relationships(self, actions: List[Dict[str, Any]], agent_name: str) -> List[Dict[str, Any]]:
        """Extract relationship data from interactions."""
        relationship_map: Dict[str, Dict[str, Any]] = {}
        for action in actions:
            target = action.get("action_args", {}).get("post_author_name", "")
            if not target or target == agent_name:
                continue
            if target not in relationship_map:
                relationship_map[target] = {
                    "entity": target,
                    "type": "interacted_with",
                    "strength": 0.0,
                    "interactions": 0,
                    "platforms": set(),
                }
            rel = relationship_map[target]
            rel["interactions"] += 1
            rel["platforms"].add(action.get("platform", "unknown"))
            if action.get("action_type") in RELATIONSHIP_ACTION_TYPES:
                rel["strength"] = min(1.0, rel["strength"] + 0.15)
            else:
                rel["strength"] = min(1.0, rel["strength"] + 0.1)

        return [
            {**r, "platforms": list(r["platforms"])}
            for r in relationship_map.values()
        ]

    def _build_temporal_memory(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build temporal event sequence for the agent."""
        events = []
        for action in actions:
            content = action.get("action_args", {}).get("content", "")
            if not content:
                content = action.get("action_args", {}).get("post_content", "")
            events.append({
                "round": action.get("round_num", 0),
                "event": f"{action.get('action_type', 'UNKNOWN')}: {content[:120]}" if content else action.get('action_type', 'UNKNOWN'),
                "platform": action.get("platform", "unknown"),
                "timestamp": action.get("timestamp", ""),
            })
        return events

    def export_agent_memory(
        self,
        agent_id: int,
        simulation_id: str,
        filter_type: str = MemoryFilterType.ALL,
    ) -> Dict[str, Any]:
        """
        Export an agent's memory from a simulation as a portable bundle.

        Args:
            agent_id: The agent's numeric ID within the simulation.
            simulation_id: Source simulation ID.
            filter_type: One of 'all', 'decisions_only', 'relationships_only', 'facts_only'.

        Returns:
            Serialized memory bundle dict.
        """
        if filter_type not in VALID_FILTERS:
            raise ValueError(f"Invalid filter_type: {filter_type}. Must be one of {VALID_FILTERS}")

        run_state = self._load_run_state(simulation_id)
        profiles = self._load_profiles(simulation_id)
        sim_state = self._load_state(simulation_id)

        # Find agent profile
        profile = None
        for p in profiles:
            pid = p.get("agent_id", p.get("id"))
            if pid == agent_id:
                profile = p
                break

        agent_name = profile.get("name", f"Agent_{agent_id}") if profile else f"Agent_{agent_id}"

        actions = self._extract_agent_actions(run_state, agent_id) if run_state else []

        # Build memory sections based on filter
        memory: Dict[str, Any] = {}

        if filter_type in (MemoryFilterType.ALL, MemoryFilterType.FACTS_ONLY):
            memory["facts"] = self._build_facts(actions, agent_name)

        if filter_type in (MemoryFilterType.ALL, MemoryFilterType.DECISIONS_ONLY):
            memory["decisions"] = self._build_decisions(actions)

        if filter_type in (MemoryFilterType.ALL, MemoryFilterType.RELATIONSHIPS_ONLY):
            memory["relationships"] = self._build_relationships(actions, agent_name)

        if filter_type == MemoryFilterType.ALL:
            memory["temporal_memory"] = self._build_temporal_memory(actions)
            memory["actions_summary"] = {
                "total": len(actions),
                "by_type": {},
                "by_platform": {},
            }
            for a in actions:
                at = a.get("action_type", "UNKNOWN")
                memory["actions_summary"]["by_type"][at] = memory["actions_summary"]["by_type"].get(at, 0) + 1
                pl = a.get("platform", "unknown")
                memory["actions_summary"]["by_platform"][pl] = memory["actions_summary"]["by_platform"].get(pl, 0) + 1

        if profile:
            memory["profile"] = {
                "name": agent_name,
                "agent_id": agent_id,
                "role": profile.get("role", profile.get("description", "")),
                "persona": profile.get("persona", ""),
            }

        bundle = {
            "bundle_id": str(uuid.uuid4()),
            "source_simulation_id": simulation_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "filter_type": filter_type,
            "created_at": datetime.now().isoformat(),
            "source_scenario": sim_state.get("graph_id", "") if sim_state else "",
            "memory": memory,
        }

        # Persist bundle to disk
        bundles_dir = self._get_bundles_dir(simulation_id)
        bundle_path = os.path.join(bundles_dir, f"{bundle['bundle_id']}.json")
        with open(bundle_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Exported memory bundle {bundle['bundle_id']} for agent {agent_id} "
            f"from simulation {simulation_id} (filter={filter_type})"
        )
        return bundle

    def import_agent_memory(
        self,
        agent_id: int,
        simulation_id: str,
        memory_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Import a memory bundle into a simulation for a specific agent.

        Saves the bundle into the target simulation's memory_bundles directory
        and returns an import receipt.
        """
        import_id = str(uuid.uuid4())
        receipt = {
            "import_id": import_id,
            "target_simulation_id": simulation_id,
            "target_agent_id": agent_id,
            "source_bundle_id": memory_bundle.get("bundle_id", "unknown"),
            "source_simulation_id": memory_bundle.get("source_simulation_id", "unknown"),
            "source_agent_name": memory_bundle.get("agent_name", "unknown"),
            "filter_type": memory_bundle.get("filter_type", "all"),
            "imported_at": datetime.now().isoformat(),
            "memory_sections": list(memory_bundle.get("memory", {}).keys()),
            "status": "imported",
        }

        # Save imported bundle into target simulation
        bundles_dir = self._get_bundles_dir(simulation_id)
        import_path = os.path.join(bundles_dir, f"imported_{import_id}.json")
        import_data = {
            **memory_bundle,
            "import_receipt": receipt,
        }
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Imported memory bundle into simulation {simulation_id} "
            f"for agent {agent_id} (import_id={import_id})"
        )
        return receipt

    def selective_transfer(
        self,
        agent_id: int,
        from_simulation_id: str,
        to_simulation_id: str,
        filter_type: str = MemoryFilterType.ALL,
    ) -> Dict[str, Any]:
        """
        Export from one simulation and import into another in one step.

        Returns both the exported bundle and the import receipt.
        """
        bundle = self.export_agent_memory(agent_id, from_simulation_id, filter_type)
        receipt = self.import_agent_memory(agent_id, to_simulation_id, bundle)

        logger.info(
            f"Transferred memory for agent {agent_id}: "
            f"{from_simulation_id} -> {to_simulation_id} (filter={filter_type})"
        )
        return {
            "bundle": bundle,
            "import_receipt": receipt,
        }

    def list_bundles(self, simulation_id: str) -> List[Dict[str, Any]]:
        """List all memory bundles (exported and imported) for a simulation."""
        bundles_dir = self._get_bundles_dir(simulation_id)
        bundles = []
        for filename in sorted(os.listdir(bundles_dir)):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(bundles_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                bundles.append({
                    "bundle_id": data.get("bundle_id", filename.replace('.json', '')),
                    "agent_id": data.get("agent_id"),
                    "agent_name": data.get("agent_name", "Unknown"),
                    "filter_type": data.get("filter_type", "all"),
                    "source_simulation_id": data.get("source_simulation_id", ""),
                    "created_at": data.get("created_at", ""),
                    "is_import": filename.startswith("imported_"),
                    "import_receipt": data.get("import_receipt"),
                    "memory_sections": list(data.get("memory", {}).keys()),
                })
            except (json.JSONDecodeError, OSError):
                logger.warning(f"Skipping malformed bundle file: {filepath}")
        return bundles

    def get_bundle(self, simulation_id: str, bundle_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory bundle by ID."""
        bundles_dir = self._get_bundles_dir(simulation_id)
        for filename in os.listdir(bundles_dir):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(bundles_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get("bundle_id") == bundle_id:
                    return data
            except (json.JSONDecodeError, OSError):
                continue
        return None

    def delete_bundle(self, simulation_id: str, bundle_id: str) -> bool:
        """Delete a memory bundle by ID."""
        bundles_dir = self._get_bundles_dir(simulation_id)
        for filename in os.listdir(bundles_dir):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(bundles_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get("bundle_id") == bundle_id:
                    os.remove(filepath)
                    logger.info(f"Deleted bundle {bundle_id} from simulation {simulation_id}")
                    return True
            except (json.JSONDecodeError, OSError):
                continue
        return False


def generate_demo_bundles() -> List[Dict[str, Any]]:
    """Generate mock memory bundles for demo/no-LLM mode."""
    agents = [
        {"id": 0, "name": "Sarah Chen, VP Support @ Acme SaaS"},
        {"id": 1, "name": "James Wright, CX Director @ Retail Plus"},
        {"id": 2, "name": "Robert Williams, IT Director @ EduSpark"},
    ]
    bundles = []
    for agent in agents:
        bundle = {
            "bundle_id": str(uuid.uuid4()),
            "source_simulation_id": "demo-sim-001",
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "filter_type": "all",
            "created_at": datetime.now().isoformat(),
            "source_scenario": "demo-graph",
            "memory": {
                "profile": {
                    "name": agent["name"],
                    "agent_id": agent["id"],
                    "role": "GTM Simulation Participant",
                    "persona": "Industry professional evaluating support platforms",
                },
                "facts": [
                    {"content": "AI-first resolution reduces ticket volume by 30-40%", "confidence": 0.85, "source": "round_2", "platform": "twitter", "timestamp": ""},
                    {"content": "Migration from legacy platforms typically takes 30-90 days", "confidence": 0.7, "source": "round_3", "platform": "reddit", "timestamp": ""},
                    {"content": "Mid-market companies spend $10K-20K/mo on support tools", "confidence": 0.9, "source": "round_1", "platform": "twitter", "timestamp": ""},
                ],
                "decisions": [
                    {"action_type": "CREATE_POST", "content": "Shared analysis of AI support platform comparison", "round": 2, "platform": "twitter", "context": {}, "timestamp": ""},
                    {"action_type": "REPLY", "content": "Responded to migration timeline concerns with data", "round": 4, "platform": "reddit", "context": {}, "timestamp": ""},
                ],
                "relationships": [
                    {"entity": "James Wright", "type": "interacted_with", "strength": 0.6, "interactions": 4, "platforms": ["twitter"]},
                    {"entity": "Robert Williams", "type": "interacted_with", "strength": 0.3, "interactions": 2, "platforms": ["reddit"]},
                ],
                "temporal_memory": [
                    {"round": 1, "event": "CREATE_POST: Initial market analysis shared", "platform": "twitter", "timestamp": ""},
                    {"round": 2, "event": "REPLY: Engaged with competitor pricing discussion", "platform": "reddit", "timestamp": ""},
                    {"round": 3, "event": "LIKE: Endorsed peer's migration guide", "platform": "twitter", "timestamp": ""},
                ],
                "actions_summary": {
                    "total": 12,
                    "by_type": {"CREATE_POST": 3, "REPLY": 4, "LIKE": 3, "REPOST": 2},
                    "by_platform": {"twitter": 7, "reddit": 5},
                },
            },
        }
        bundles.append(bundle)
    return bundles
