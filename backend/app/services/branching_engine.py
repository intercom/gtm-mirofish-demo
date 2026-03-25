"""
Scenario Branching Engine

Allows forking simulations at any round, creating what-if branches
with modifications (change agent, change constraint, inject event).
Maintains parent-child relationships and enables branch comparison.
"""

import os
import json
import uuid
import shutil
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('mirofish.branching')


class ModificationType(str, Enum):
    CHANGE_AGENT = "change_agent"
    CHANGE_CONSTRAINT = "change_constraint"
    INJECT_EVENT = "inject_event"


@dataclass
class BranchModification:
    type: str
    value: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "value": self.value, "description": self.description}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BranchModification":
        return cls(
            type=data.get("type", ""),
            value=data.get("value", {}),
            description=data.get("description", ""),
        )


@dataclass
class BranchMeta:
    branch_id: str
    simulation_id: str
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    fork_round: int = 0
    label: str = ""
    modifications: List[BranchModification] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "created"
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "simulation_id": self.simulation_id,
            "parent_id": self.parent_id,
            "root_id": self.root_id,
            "fork_round": self.fork_round,
            "label": self.label,
            "modifications": [m.to_dict() for m in self.modifications],
            "created_at": self.created_at,
            "status": self.status,
            "metrics_snapshot": self.metrics_snapshot,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BranchMeta":
        return cls(
            branch_id=data.get("branch_id", ""),
            simulation_id=data.get("simulation_id", ""),
            parent_id=data.get("parent_id"),
            root_id=data.get("root_id"),
            fork_round=data.get("fork_round", 0),
            label=data.get("label", ""),
            modifications=[
                BranchModification.from_dict(m) for m in data.get("modifications", [])
            ],
            created_at=data.get("created_at", datetime.now().isoformat()),
            status=data.get("status", "created"),
            metrics_snapshot=data.get("metrics_snapshot", {}),
        )


def _generate_label(modifications: List[BranchModification], fork_round: int) -> str:
    """Generate a human-readable label from the modifications."""
    if not modifications:
        return f"Branch at round {fork_round}"
    parts = []
    for mod in modifications:
        if mod.description:
            parts.append(mod.description)
        elif mod.type == ModificationType.CHANGE_AGENT:
            agent = mod.value.get("agent_name", "agent")
            change = mod.value.get("change", "modified")
            parts.append(f"{agent} {change}")
        elif mod.type == ModificationType.CHANGE_CONSTRAINT:
            constraint = mod.value.get("name", "constraint")
            parts.append(f"Changed {constraint}")
        elif mod.type == ModificationType.INJECT_EVENT:
            event = mod.value.get("event", "event")
            parts.append(f"Injected: {event}")
        else:
            parts.append(mod.type)
    return " + ".join(parts) if parts else f"Branch at round {fork_round}"


class BranchingEngine:
    """
    Manages forking simulations at arbitrary rounds.

    Each branch is a new simulation directory that contains:
    - Copied state/profiles up to the fork round
    - Truncated action logs (only actions up to fork_round)
    - branch_meta.json tracking lineage
    - Optionally, mock continuation data for demo mode
    """

    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), '../../uploads/simulations'
    )

    def __init__(self):
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)

    def _sim_dir(self, simulation_id: str) -> str:
        return os.path.join(self.SIMULATION_DATA_DIR, simulation_id)

    def _branch_meta_path(self, simulation_id: str) -> str:
        return os.path.join(self._sim_dir(simulation_id), "branch_meta.json")

    def _load_branch_meta(self, simulation_id: str) -> Optional[BranchMeta]:
        path = self._branch_meta_path(simulation_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return BranchMeta.from_dict(json.load(f))

    def _save_branch_meta(self, meta: BranchMeta):
        sim_dir = self._sim_dir(meta.simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        with open(os.path.join(sim_dir, "branch_meta.json"), 'w', encoding='utf-8') as f:
            json.dump(meta.to_dict(), f, ensure_ascii=False, indent=2)

    def _read_actions(self, simulation_id: str, platform: str) -> List[Dict[str, Any]]:
        """Read all actions from a platform's actions.jsonl file."""
        actions_path = os.path.join(
            self._sim_dir(simulation_id), platform, "actions.jsonl"
        )
        if not os.path.exists(actions_path):
            return []
        actions = []
        with open(actions_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        actions.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return actions

    def _write_actions(self, simulation_id: str, platform: str, actions: List[Dict[str, Any]]):
        """Write actions to a platform's actions.jsonl file."""
        platform_dir = os.path.join(self._sim_dir(simulation_id), platform)
        os.makedirs(platform_dir, exist_ok=True)
        with open(os.path.join(platform_dir, "actions.jsonl"), 'w', encoding='utf-8') as f:
            for action in actions:
                f.write(json.dumps(action, ensure_ascii=False) + "\n")

    def _truncate_actions_at_round(
        self, actions: List[Dict[str, Any]], at_round: int
    ) -> List[Dict[str, Any]]:
        """Keep only actions from rounds <= at_round."""
        return [a for a in actions if a.get("round_num", 0) <= at_round]

    def _compute_metrics(self, simulation_id: str) -> Dict[str, Any]:
        """Compute summary metrics from a simulation's action logs."""
        metrics: Dict[str, Any] = {
            "total_actions": 0,
            "total_rounds": 0,
            "actions_by_type": {},
            "actions_by_agent": {},
            "platform_counts": {"twitter": 0, "reddit": 0},
        }

        for platform in ("twitter", "reddit"):
            actions = self._read_actions(simulation_id, platform)
            metrics["platform_counts"][platform] = len(actions)
            metrics["total_actions"] += len(actions)

            for action in actions:
                round_num = action.get("round_num", 0)
                if round_num > metrics["total_rounds"]:
                    metrics["total_rounds"] = round_num

                action_type = action.get("action_type", "unknown")
                metrics["actions_by_type"][action_type] = (
                    metrics["actions_by_type"].get(action_type, 0) + 1
                )

                agent_name = action.get("agent_name", "unknown")
                metrics["actions_by_agent"][agent_name] = (
                    metrics["actions_by_agent"].get(agent_name, 0) + 1
                )

        return metrics

    def _generate_mock_continuation(
        self,
        simulation_id: str,
        source_actions: Dict[str, List[Dict[str, Any]]],
        fork_round: int,
        total_rounds: int,
        modifications: List[BranchModification],
    ):
        """
        Generate mock divergent actions for rounds after fork_round.
        Uses a deterministic seed so results are reproducible.
        """
        seed_str = f"{simulation_id}:{fork_round}:{len(modifications)}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

        import random
        rng = random.Random(seed)

        action_types_twitter = [
            "CREATE_POST", "LIKE_POST", "REPOST", "FOLLOW", "QUOTE_POST"
        ]
        action_types_reddit = [
            "CREATE_POST", "CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST", "SEARCH_POSTS"
        ]

        mod_context = ""
        for mod in modifications:
            if mod.type == ModificationType.INJECT_EVENT:
                mod_context = mod.value.get("event", "")
            elif mod.type == ModificationType.CHANGE_CONSTRAINT:
                mod_context = mod.value.get("name", "")
            elif mod.type == ModificationType.CHANGE_AGENT:
                mod_context = mod.value.get("change", "")

        for platform in ("twitter", "reddit"):
            existing = source_actions.get(platform, [])
            agents = list({
                a.get("agent_name", f"Agent_{a.get('agent_id', 0)}")
                for a in existing if a.get("agent_name")
            })
            if not agents:
                agents = [f"Agent_{i}" for i in range(5)]

            agent_ids = {}
            for a in existing:
                name = a.get("agent_name", "")
                if name and name not in agent_ids:
                    agent_ids[name] = a.get("agent_id", 0)

            types = action_types_twitter if platform == "twitter" else action_types_reddit

            new_actions = list(existing)

            for round_num in range(fork_round + 1, total_rounds + 1):
                num_actions = rng.randint(1, max(2, len(agents) // 2))
                active = rng.sample(agents, min(num_actions, len(agents)))

                for agent_name in active:
                    action_type = rng.choice(types)
                    content = ""
                    if action_type in ("CREATE_POST", "CREATE_COMMENT"):
                        if mod_context:
                            content = f"[Branch divergence] Reacting to: {mod_context}"
                        else:
                            content = f"[Branch round {round_num}] Continuing discussion"

                    new_actions.append({
                        "round_num": round_num,
                        "timestamp": datetime.now().isoformat(),
                        "platform": platform,
                        "agent_id": agent_ids.get(agent_name, 0),
                        "agent_name": agent_name,
                        "action_type": action_type,
                        "action_args": {"content": content} if content else {},
                        "result": None,
                        "success": True,
                    })

            self._write_actions(simulation_id, platform, new_actions)

    def fork(
        self,
        simulation_id: str,
        at_round: int,
        modifications: Optional[List[Dict[str, Any]]] = None,
        label: Optional[str] = None,
        generate_continuation: bool = True,
        continuation_rounds: int = 0,
    ) -> str:
        """
        Fork a simulation at a specific round, creating a new branch.

        Args:
            simulation_id: Source simulation to fork from
            at_round: Round number to fork at (actions up to this round are copied)
            modifications: List of modification dicts [{type, value, description}]
            label: Optional label; auto-generated from modifications if omitted
            generate_continuation: Whether to generate mock data after the fork point
            continuation_rounds: How many additional rounds to generate (0 = same as source)

        Returns:
            New simulation_id for the branch
        """
        source_dir = self._sim_dir(simulation_id)
        if not os.path.isdir(source_dir):
            raise ValueError(f"Simulation not found: {simulation_id}")

        parsed_mods = [
            BranchModification.from_dict(m) for m in (modifications or [])
        ]

        # Determine root: if source is itself a branch, inherit its root
        source_meta = self._load_branch_meta(simulation_id)
        root_id = simulation_id
        if source_meta and source_meta.root_id:
            root_id = source_meta.root_id
        elif source_meta and source_meta.parent_id:
            root_id = source_meta.root_id or simulation_id

        branch_sim_id = f"sim_{uuid.uuid4().hex[:12]}"
        branch_dir = self._sim_dir(branch_sim_id)
        os.makedirs(branch_dir, exist_ok=True)

        # Copy state.json with updated simulation_id
        state_src = os.path.join(source_dir, "state.json")
        if os.path.exists(state_src):
            with open(state_src, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            state_data["simulation_id"] = branch_sim_id
            state_data["current_round"] = at_round
            state_data["updated_at"] = datetime.now().isoformat()
            with open(os.path.join(branch_dir, "state.json"), 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)

        # Copy simulation config
        config_src = os.path.join(source_dir, "simulation_config.json")
        if os.path.exists(config_src):
            shutil.copy2(config_src, os.path.join(branch_dir, "simulation_config.json"))

        # Copy profile files
        for profile_file in ("reddit_profiles.json", "twitter_profiles.csv"):
            src = os.path.join(source_dir, profile_file)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(branch_dir, profile_file))

        # Truncate actions at fork_round and write to new sim
        source_actions: Dict[str, List[Dict[str, Any]]] = {}
        source_total_rounds = 0
        for platform in ("twitter", "reddit"):
            actions = self._read_actions(simulation_id, platform)
            truncated = self._truncate_actions_at_round(actions, at_round)
            source_actions[platform] = truncated
            self._write_actions(branch_sim_id, platform, truncated)

            for a in actions:
                r = a.get("round_num", 0)
                if r > source_total_rounds:
                    source_total_rounds = r

        # Resolve total rounds for continuation
        total_rounds = source_total_rounds
        if continuation_rounds > 0:
            total_rounds = at_round + continuation_rounds

        # Generate label
        branch_label = label or _generate_label(parsed_mods, at_round)

        # Save branch metadata
        meta = BranchMeta(
            branch_id=branch_sim_id,
            simulation_id=branch_sim_id,
            parent_id=simulation_id,
            root_id=root_id,
            fork_round=at_round,
            label=branch_label,
            modifications=parsed_mods,
            status="forked",
        )
        self._save_branch_meta(meta)

        # Also ensure the source has branch metadata (marks it as a root if not already)
        if not source_meta:
            source_root_meta = BranchMeta(
                branch_id=simulation_id,
                simulation_id=simulation_id,
                parent_id=None,
                root_id=simulation_id,
                fork_round=0,
                label="Root simulation",
                status="root",
            )
            self._save_branch_meta(source_root_meta)

        # Generate mock continuation if requested and there are rounds remaining
        if generate_continuation and total_rounds > at_round:
            self._generate_mock_continuation(
                branch_sim_id, source_actions, at_round, total_rounds, parsed_mods
            )

        # Compute and store metrics snapshot
        meta.metrics_snapshot = self._compute_metrics(branch_sim_id)
        self._save_branch_meta(meta)

        logger.info(
            f"Forked simulation {simulation_id} at round {at_round} → {branch_sim_id} "
            f"(label={branch_label!r}, mods={len(parsed_mods)})"
        )
        return branch_sim_id

    def get_branch_meta(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get branch metadata for a simulation, or None if not a branch."""
        meta = self._load_branch_meta(simulation_id)
        return meta.to_dict() if meta else None

    def get_branch_tree(self, root_simulation_id: str) -> Dict[str, Any]:
        """
        Build the full branch tree starting from a root simulation.

        Returns a nested tree structure:
        {
            "id": "sim_xxx",
            "label": "Root simulation",
            "fork_round": 0,
            "children": [
                {"id": "sim_yyy", "label": "...", "fork_round": 5, "children": [...]}
            ]
        }
        """
        # Collect all branch metas by scanning simulation directories
        all_metas: Dict[str, BranchMeta] = {}

        if not os.path.exists(self.SIMULATION_DATA_DIR):
            return self._build_tree_node(root_simulation_id, {})

        for entry in os.listdir(self.SIMULATION_DATA_DIR):
            if entry.startswith('.') or not entry.startswith('sim_'):
                continue
            entry_path = os.path.join(self.SIMULATION_DATA_DIR, entry)
            if not os.path.isdir(entry_path):
                continue
            meta = self._load_branch_meta(entry)
            if meta:
                all_metas[entry] = meta

        # Find all branches belonging to this root
        relevant: Dict[str, BranchMeta] = {}
        for sim_id, meta in all_metas.items():
            if (
                meta.root_id == root_simulation_id
                or meta.simulation_id == root_simulation_id
                or meta.parent_id == root_simulation_id
            ):
                relevant[sim_id] = meta

        # Also do a transitive pass: if parent is in relevant, add this too
        changed = True
        while changed:
            changed = False
            for sim_id, meta in all_metas.items():
                if sim_id not in relevant and meta.parent_id in relevant:
                    relevant[sim_id] = meta
                    changed = True

        return self._build_tree_node(root_simulation_id, relevant)

    def _build_tree_node(
        self, simulation_id: str, all_metas: Dict[str, "BranchMeta"]
    ) -> Dict[str, Any]:
        meta = all_metas.get(simulation_id)
        children_metas = [
            m for m in all_metas.values()
            if m.parent_id == simulation_id and m.simulation_id != simulation_id
        ]
        children_metas.sort(key=lambda m: m.fork_round)

        node: Dict[str, Any] = {
            "id": simulation_id,
            "label": meta.label if meta else "Root simulation",
            "fork_round": meta.fork_round if meta else 0,
            "status": meta.status if meta else "root",
            "created_at": meta.created_at if meta else None,
            "modifications": [m.to_dict() for m in meta.modifications] if meta else [],
            "metrics_snapshot": meta.metrics_snapshot if meta else {},
            "children": [
                self._build_tree_node(c.simulation_id, all_metas)
                for c in children_metas
            ],
        }
        return node

    def compare_branches(self, branch_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple branches side by side.

        Returns structured comparison with per-branch metrics and divergence analysis.
        """
        branches = []
        all_action_types: set = set()
        all_agents: set = set()

        for sim_id in branch_ids:
            meta = self._load_branch_meta(sim_id)
            metrics = self._compute_metrics(sim_id)
            all_action_types.update(metrics.get("actions_by_type", {}).keys())
            all_agents.update(metrics.get("actions_by_agent", {}).keys())

            branches.append({
                "simulation_id": sim_id,
                "label": meta.label if meta else sim_id,
                "fork_round": meta.fork_round if meta else 0,
                "parent_id": meta.parent_id if meta else None,
                "modifications": [m.to_dict() for m in meta.modifications] if meta else [],
                "metrics": metrics,
            })

        # Find common ancestor fork point
        fork_rounds = [b["fork_round"] for b in branches]
        common_fork = min(fork_rounds) if fork_rounds else 0

        # Build divergence summary
        divergence: Dict[str, Any] = {
            "common_fork_round": common_fork,
            "action_type_comparison": {},
            "agent_activity_comparison": {},
            "total_actions_comparison": {},
        }

        for action_type in sorted(all_action_types):
            divergence["action_type_comparison"][action_type] = {
                b["simulation_id"]: b["metrics"].get("actions_by_type", {}).get(action_type, 0)
                for b in branches
            }

        for agent in sorted(all_agents):
            divergence["agent_activity_comparison"][agent] = {
                b["simulation_id"]: b["metrics"].get("actions_by_agent", {}).get(agent, 0)
                for b in branches
            }

        for b in branches:
            divergence["total_actions_comparison"][b["simulation_id"]] = (
                b["metrics"].get("total_actions", 0)
            )

        return {
            "branches": branches,
            "divergence": divergence,
            "branch_count": len(branches),
        }

    def delete_branch(
        self, simulation_id: str, delete_descendants: bool = False
    ) -> List[str]:
        """
        Delete a branch (and optionally its descendants).

        Returns list of deleted simulation_ids.
        """
        deleted = []

        if delete_descendants:
            tree = self.get_branch_tree(simulation_id)
            to_delete = self._collect_tree_ids(tree)
        else:
            to_delete = [simulation_id]

        for sim_id in to_delete:
            sim_dir = self._sim_dir(sim_id)
            if os.path.isdir(sim_dir):
                shutil.rmtree(sim_dir, ignore_errors=True)
                deleted.append(sim_id)
                logger.info(f"Deleted branch: {sim_id}")

        return deleted

    def _collect_tree_ids(self, node: Dict[str, Any]) -> List[str]:
        """Collect all simulation IDs from a tree node recursively."""
        ids = [node["id"]]
        for child in node.get("children", []):
            ids.extend(self._collect_tree_ids(child))
        return ids

    def list_branches(self, root_simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all branches, optionally filtered by root simulation."""
        results = []
        if not os.path.exists(self.SIMULATION_DATA_DIR):
            return results

        for entry in os.listdir(self.SIMULATION_DATA_DIR):
            if entry.startswith('.') or not entry.startswith('sim_'):
                continue
            meta = self._load_branch_meta(entry)
            if not meta:
                continue
            if root_simulation_id and meta.root_id != root_simulation_id:
                continue
            results.append(meta.to_dict())

        results.sort(key=lambda m: m.get("created_at", ""))
        return results
