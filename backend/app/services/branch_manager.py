"""
Simulation Branch Manager

Manages forking simulations at specific rounds, creating branch trees,
and comparing branches. Uses in-memory storage with JSON file persistence,
mirroring the pattern from SimulationManager.
"""

import os
import json
import uuid
import hashlib
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger('mirofish.branches')


@dataclass
class SimulationBranch:
    branch_id: str
    simulation_id: str
    parent_branch_id: Optional[str]
    at_round: int
    label: str
    modifications: List[Dict[str, Any]]
    status: str = "created"
    current_round: int = 0
    total_rounds: int = 144
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BranchManager:
    """
    Manages simulation branches (forks at specific rounds).

    Storage: JSON files under uploads/simulations/<sim_id>/branches/
    with an in-memory cache for fast lookups.
    """

    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../uploads/simulations'
    )

    def __init__(self):
        self._branches: Dict[str, SimulationBranch] = {}

    def _branches_dir(self, simulation_id: str) -> str:
        d = os.path.join(self.SIMULATION_DATA_DIR, simulation_id, 'branches')
        os.makedirs(d, exist_ok=True)
        return d

    def _branch_file(self, simulation_id: str, branch_id: str) -> str:
        return os.path.join(self._branches_dir(simulation_id), f'{branch_id}.json')

    def _save_branch(self, branch: SimulationBranch):
        path = self._branch_file(branch.simulation_id, branch.branch_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(branch.to_dict(), f, ensure_ascii=False, indent=2)
        self._branches[branch.branch_id] = branch

    def _load_branch(self, simulation_id: str, branch_id: str) -> Optional[SimulationBranch]:
        if branch_id in self._branches:
            return self._branches[branch_id]

        path = self._branch_file(simulation_id, branch_id)
        if not os.path.exists(path):
            return None

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        branch = SimulationBranch(**data)
        self._branches[branch_id] = branch
        return branch

    def _load_all_branches(self, simulation_id: str) -> List[SimulationBranch]:
        branches_dir = self._branches_dir(simulation_id)
        results = []
        for fname in os.listdir(branches_dir):
            if not fname.endswith('.json'):
                continue
            bid = fname.replace('.json', '')
            branch = self._load_branch(simulation_id, bid)
            if branch:
                results.append(branch)
        return sorted(results, key=lambda b: b.created_at)

    # ── Public API ──────────────────────────────────────────────

    def create_branch(
        self,
        simulation_id: str,
        at_round: int,
        label: str,
        modifications: List[Dict[str, Any]],
        parent_branch_id: Optional[str] = None,
    ) -> SimulationBranch:
        branch_id = f"br_{uuid.uuid4().hex[:12]}"

        # Determine total rounds from parent or default
        total_rounds = 144
        if parent_branch_id:
            parent = self._load_branch(simulation_id, parent_branch_id)
            if parent:
                total_rounds = parent.total_rounds

        branch = SimulationBranch(
            branch_id=branch_id,
            simulation_id=simulation_id,
            parent_branch_id=parent_branch_id,
            at_round=at_round,
            label=label,
            modifications=modifications,
            status="completed",
            current_round=total_rounds,
            total_rounds=total_rounds,
        )
        self._save_branch(branch)
        logger.info(
            f"Created branch {branch_id} on sim {simulation_id} at round {at_round}"
        )
        return branch

    def list_branches(self, simulation_id: str) -> List[SimulationBranch]:
        return self._load_all_branches(simulation_id)

    def get_branch(self, simulation_id: str, branch_id: str) -> Optional[SimulationBranch]:
        return self._load_branch(simulation_id, branch_id)

    def get_branch_tree(self, simulation_id: str) -> Dict[str, Any]:
        """Build a tree structure of all branches for a simulation."""
        branches = self._load_all_branches(simulation_id)

        root = {
            "id": simulation_id,
            "type": "simulation",
            "label": "Main simulation",
            "at_round": 0,
            "children": [],
        }

        # Index branches by parent
        by_parent: Dict[Optional[str], List[SimulationBranch]] = {}
        for b in branches:
            by_parent.setdefault(b.parent_branch_id, []).append(b)

        def _build_children(parent_id: Optional[str]) -> List[Dict]:
            children = []
            for b in by_parent.get(parent_id, []):
                node = {
                    "id": b.branch_id,
                    "type": "branch",
                    "label": b.label,
                    "at_round": b.at_round,
                    "status": b.status,
                    "modifications": b.modifications,
                    "created_at": b.created_at,
                    "children": _build_children(b.branch_id),
                }
                children.append(node)
            return children

        # Top-level branches (parent_branch_id is None) are children of root
        root["children"] = _build_children(None)
        return root

    def compare_branches(
        self, simulation_id: str, branch_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple branches by generating deterministic mock metrics.

        Uses a seeded PRNG per branch so results are stable across calls.
        """
        branches = []
        for bid in branch_ids:
            b = self._load_branch(simulation_id, bid)
            if b:
                branches.append(b)

        if not branches:
            return {"branches": [], "metrics": [], "summary": {}}

        metrics = []
        for b in branches:
            seed = int(hashlib.md5(b.branch_id.encode()).hexdigest()[:8], 16)
            rng = random.Random(seed)

            total_posts = rng.randint(120, 350)
            avg_engagement = round(rng.uniform(0.3, 0.9), 2)
            sentiment = round(rng.uniform(-0.4, 0.8), 2)
            competitive_mentions = rng.randint(5, 60)

            metrics.append({
                "branch_id": b.branch_id,
                "label": b.label,
                "at_round": b.at_round,
                "modifications": b.modifications,
                "metrics": {
                    "total_posts": total_posts,
                    "avg_engagement": avg_engagement,
                    "overall_sentiment": sentiment,
                    "competitive_mentions": competitive_mentions,
                },
            })

        # Determine "winner" per metric
        metric_keys = ["total_posts", "avg_engagement", "overall_sentiment"]
        summary = {}
        for key in metric_keys:
            best = max(metrics, key=lambda m: m["metrics"][key])
            summary[key] = {
                "best_branch": best["branch_id"],
                "best_label": best["label"],
                "value": best["metrics"][key],
            }

        return {
            "branches": [b.to_dict() for b in branches],
            "metrics": metrics,
            "summary": summary,
        }

    def delete_branch(
        self, simulation_id: str, branch_id: str, cascade: bool = False
    ) -> bool:
        """Delete a branch. If cascade=True, also delete descendants."""
        branch = self._load_branch(simulation_id, branch_id)
        if not branch:
            return False

        to_delete = [branch_id]
        if cascade:
            all_branches = self._load_all_branches(simulation_id)
            # BFS to find descendants
            queue = [branch_id]
            while queue:
                parent = queue.pop(0)
                for b in all_branches:
                    if b.parent_branch_id == parent and b.branch_id not in to_delete:
                        to_delete.append(b.branch_id)
                        queue.append(b.branch_id)

        for bid in to_delete:
            path = self._branch_file(simulation_id, bid)
            if os.path.exists(path):
                os.remove(path)
            self._branches.pop(bid, None)

        logger.info(
            f"Deleted {'(cascade) ' if cascade else ''}branch(es) {to_delete} "
            f"from sim {simulation_id}"
        )
        return True
