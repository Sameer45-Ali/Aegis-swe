"""
MCTS Node and State Representation.
Tracks exploration path, action payload, visit counts, rewards, and UCT score.
"""

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionType(str, Enum):
    ROOT = "root"
    AST_SEARCH = "ast_search"
    WRITE_REPRO_TEST = "write_repro_test"
    GENERATE_PATCH = "generate_patch"
    RUN_TESTS = "run_tests"
    REFLECT_AND_REPAIR = "reflect_and_repair"


@dataclass
class MCTSNode:
    action_type: ActionType
    action_payload: Dict[str, Any]  # e.g., {"target_file": "...", "patch": "...", "test_code": "..."}
    parent: Optional["MCTSNode"] = None
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    children: List["MCTSNode"] = field(default_factory=list)
    
    # MCTS Statistics
    visit_count: int = 0
    total_reward: float = 0.0
    best_reward: float = 0.0
    
    # State snapshots
    depth: int = 0
    stdout_snippet: Optional[str] = None
    tests_passed: int = 0
    tests_failed: int = 0
    is_terminal: bool = False
    is_solution: bool = False
    git_diff: Optional[str] = None
    reflection: Optional[str] = None

    @property
    def mean_reward(self) -> float:
        if self.visit_count == 0:
            return 0.0
        return self.total_reward / self.visit_count

    def compute_uct(self, exploration_constant: float = 1.414) -> float:
        """Computes Upper Confidence Bound for Trees (UCT)."""
        if self.visit_count == 0:
            return float("inf")  # Encourage exploring unvisited nodes
        
        if self.parent is None or self.parent.visit_count == 0:
            parent_visits = self.visit_count
        else:
            parent_visits = self.parent.visit_count

        exploitation = self.mean_reward
        exploration = exploration_constant * math.sqrt(math.log(parent_visits) / self.visit_count)
        return exploitation + exploration

    def add_child(self, action_type: ActionType, payload: Dict[str, Any]) -> "MCTSNode":
        child = MCTSNode(
            action_type=action_type,
            action_payload=payload,
            parent=self,
            depth=self.depth + 1
        )
        self.children.append(child)
        return child

    def to_dict(self) -> Dict[str, Any]:
        """Serializes node for UI visualization and WebSocket streaming."""
        return {
            "id": self.node_id,
            "action_type": self.action_type.value,
            "depth": self.depth,
            "visits": self.visit_count,
            "mean_reward": round(self.mean_reward, 3),
            "best_reward": round(self.best_reward, 3),
            "uct": round(self.compute_uct(), 3) if self.visit_count > 0 else 999.0,
            "is_solution": self.is_solution,
            "is_terminal": self.is_terminal,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "summary": self.action_payload.get("summary", self.action_type.value),
            "children_ids": [c.node_id for c in self.children],
            "git_diff": self.git_diff,
            "reflection": self.reflection
        }
