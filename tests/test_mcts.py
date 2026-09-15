"""
Tests for MCTS Tree and UCT Selection Algorithm.
"""

import pytest
from aegis.core.mcts.node import ActionType, MCTSNode


def test_mcts_uct_calculation():
    root = MCTSNode(action_type=ActionType.ROOT, action_payload={"name": "root"})
    root.visit_count = 10
    
    child1 = root.add_child(ActionType.AST_SEARCH, {"summary": "child 1"})
    child1.visit_count = 5
    child1.total_reward = 3.5  # mean = 0.7

    child2 = root.add_child(ActionType.GENERATE_PATCH, {"summary": "child 2"})
    child2.visit_count = 0  # unvisited should have infinite UCT

    assert child2.compute_uct() == float("inf")
    assert child1.compute_uct() > 0.7
