"""
Agentic Reward Critic and Reflection Engine.
Computes mathematically grounded rewards for MCTS backpropagation.
"""

from typing import Any, Dict, Optional
from aegis.sandbox.base import ExecutionResult


class AgenticCritic:
    """Evaluates sandbox execution feedback and assigns normalized reward R in [0.0, 1.0]."""

    @staticmethod
    def evaluate_repro_test(result: ExecutionResult) -> float:
        """Rewards writing a reproduction test that successfully triggers a failure (RED test)."""
        if result.exit_code != 0 and (result.tests_failed > 0 or result.tests_errored > 0):
            # Perfect: The test actually reproduces a bug
            return 0.8
        elif result.exit_code == 0 and result.tests_passed > 0:
            # Flaw: The test passed on unfixed buggy code, so it doesn't reproduce the issue
            return 0.2
        else:
            return 0.0

    @staticmethod
    def evaluate_patch_execution(
        repro_result: ExecutionResult,
        regression_result: Optional[ExecutionResult] = None,
        patch_applied: bool = True
    ) -> Dict[str, Any]:
        """
        Computes composite reward for a generated patch:
        - Patch clean application (+0.2)
        - Repro test passes (+0.6)
        - Full regression suite passes (+0.2)
        - Syntax/compiler error (-0.3)
        """
        if not patch_applied:
            return {
                "reward": 0.0,
                "is_solution": False,
                "reason": "Patch failed to apply cleanly to workspace."
            }

        reward = 0.2  # baseline for clean patch application

        if repro_result.timed_out:
            return {"reward": 0.1, "is_solution": False, "reason": "Execution timed out."}

        # Check repro test
        if repro_result.exit_code == 0 and repro_result.tests_passed > 0 and repro_result.tests_failed == 0:
            reward += 0.5
            repro_passed = True
        else:
            repro_passed = False

        # Check regression suite if provided
        reg_passed = True
        if regression_result:
            if regression_result.exit_code == 0 and regression_result.tests_failed == 0:
                reward += 0.3
            else:
                reward = max(0.1, reward - 0.3)
                reg_passed = False

        is_solution = repro_passed and reg_passed
        if is_solution:
            reward = 1.0

        return {
            "reward": min(1.0, max(0.0, reward)),
            "is_solution": is_solution,
            "repro_passed": repro_passed,
            "reg_passed": reg_passed,
            "reason": "All verification tests passed cleanly." if is_solution else f"Tests: {repro_result.test_summary}"
        }
