"""
Monte Carlo Tree Search (MCTS) Engine for Autonomous Bug Resolution.
Executes iterative Selection, Expansion, Simulation (Sandbox Execution), and Backpropagation.
"""

import asyncio
import sys
from typing import Any, Callable, Dict, List, Optional
from aegis.agent.critic import AgenticCritic
from aegis.agent.llm_client import LLMClient
from aegis.agent.prompts import (
    CRITIC_REFLECTION_PROMPT,
    PATCH_GENERATION_PROMPT,
    REPRO_TEST_PROMPT,
    SYSTEM_PROMPT,
)
from aegis.config import settings
from aegis.core.ast_graph.navigator import ASTCodeGraphNavigator
from aegis.core.mcts.node import ActionType, MCTSNode
from aegis.sandbox.base import BaseSandbox, ExecutionResult
from aegis.sandbox.local_runner import LocalSandboxRunner

PYTEST_CMD = f"{sys.executable} -m pytest"


class MCTSSearchEngine:
    """Orchestrates MCTS tree exploration, sandbox code generation, and verification."""

    def __init__(
        self,
        repo_path: str,
        issue_description: str,
        sandbox: Optional[BaseSandbox] = None,
        llm_client: Optional[LLMClient] = None,
        on_node_event: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.repo_path = repo_path
        self.issue_description = issue_description
        self.sandbox = sandbox or LocalSandboxRunner(repo_path)
        self.llm = llm_client or LLMClient()
        self.navigator = ASTCodeGraphNavigator(repo_path)
        self.on_node_event = on_node_event

        self.root = MCTSNode(
            action_type=ActionType.ROOT,
            action_payload={"summary": "Root Issue Definition", "issue": issue_description}
        )
        self.best_solution_node: Optional[MCTSNode] = None
        self.repro_test_file: Optional[str] = None

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        if self.on_node_event:
            self.on_node_event({"type": event_type, "data": data})

    async def run_search(self, max_iterations: int = 10) -> Optional[MCTSNode]:
        """Runs MCTS search iterations to solve the issue."""
        self._emit_event("search_started", {
            "max_iterations": max_iterations,
            "issue": self.issue_description,
            "root_id": self.root.node_id
        })

        keywords = self.issue_description.split()
        relevant_context = self.navigator.search_relevant_context(keywords)

        # Synthesize initial bug-reproduction unit test
        await self._create_reproduction_test(relevant_context)

        # Main MCTS Loop
        for iteration in range(1, max_iterations + 1):
            if self.best_solution_node:
                break

            self._emit_event("iteration_start", {"iteration": iteration, "total": max_iterations})

            # 1. Selection
            leaf_node = self._select(self.root)

            # 2. Expansion
            expanded_nodes = await self._expand(leaf_node, relevant_context)

            # 3. Simulation & 4. Backpropagation
            for child in expanded_nodes:
                reward, is_solution = await self._simulate_and_evaluate(child)
                self._backpropagate(child, reward)

                self._emit_event("node_updated", child.to_dict())

                if is_solution:
                    self.best_solution_node = child
                    self._emit_event("solution_found", child.to_dict())
                    break

        self._emit_event("search_completed", {
            "solution_found": self.best_solution_node is not None,
            "best_node": self.best_solution_node.to_dict() if self.best_solution_node else None,
            "total_nodes": len(self._get_all_nodes(self.root))
        })

        return self.best_solution_node

    def _select(self, node: MCTSNode) -> MCTSNode:
        curr = node
        while curr.children:
            unvisited = [c for c in curr.children if c.visit_count == 0]
            if unvisited:
                return unvisited[0]
            curr = max(curr.children, key=lambda c: c.compute_uct(settings.mcts_exploration_constant))
        return curr

    async def _create_reproduction_test(self, codebase_context: str):
        prompt = REPRO_TEST_PROMPT.format(
            issue_description=self.issue_description,
            codebase_context=codebase_context
        )
        response = await self.llm.generate_json(prompt, SYSTEM_PROMPT)
        test_file = response.get("test_file_path", "tests/test_aegis_repro.py")
        test_code = response.get("test_code", "")

        if test_code:
            self.repro_test_file = test_file
            self.sandbox.write_file(test_file, test_code)
            
            exec_res = self.sandbox.run_command(f"{PYTEST_CMD} {test_file}")
            repro_reward = AgenticCritic.evaluate_repro_test(exec_res)

            repro_child = self.root.add_child(
                action_type=ActionType.WRITE_REPRO_TEST,
                payload={
                    "summary": f"Reproduction Test: {test_file}",
                    "test_file": test_file,
                    "test_code": test_code,
                    "initial_status": "RED (Failing)" if repro_reward > 0.5 else "Passed",
                    "stdout": exec_res.stdout
                }
            )
            repro_child.visit_count = 1
            repro_child.total_reward = repro_reward
            self._emit_event("node_created", repro_child.to_dict())

    async def _expand(self, node: MCTSNode, codebase_context: str) -> List[MCTSNode]:
        if node.depth >= settings.mcts_max_depth:
            return []

        prompt = PATCH_GENERATION_PROMPT.format(
            issue_description=self.issue_description,
            codebase_context=codebase_context,
            test_failure_traceback=node.stdout_snippet or "Initial reproduction failure",
            previous_attempt=node.action_payload.get("explanation", "None")
        )

        response = await self.llm.generate_json(prompt, SYSTEM_PROMPT)
        target_file = response.get("target_file", "")
        updated_content = response.get("updated_content", "")
        explanation = response.get("explanation", "Fix bug in target file")

        if not target_file or not updated_content:
            return []

        patch_node = node.add_child(
            action_type=ActionType.GENERATE_PATCH,
            payload={
                "summary": f"Patch for {target_file}",
                "target_file": target_file,
                "updated_content": updated_content,
                "explanation": explanation
            }
        )
        self._emit_event("node_created", patch_node.to_dict())
        return [patch_node]

    async def _simulate_and_evaluate(self, node: MCTSNode) -> tuple[float, bool]:
        target_file = node.action_payload.get("target_file")
        updated_content = node.action_payload.get("updated_content")

        if not target_file or not updated_content:
            return 0.0, False

        write_ok = self.sandbox.write_file(target_file, updated_content)
        if not write_ok:
            return 0.0, False

        # Run reproduction test
        repro_cmd = f"{PYTEST_CMD} {self.repro_test_file}" if self.repro_test_file else PYTEST_CMD
        exec_res = self.sandbox.run_command(repro_cmd)
        
        # Run full regression suite
        reg_res = self.sandbox.run_command(PYTEST_CMD)

        eval_result = AgenticCritic.evaluate_patch_execution(
            repro_result=exec_res,
            regression_result=reg_res,
            patch_applied=True
        )

        reward = eval_result["reward"]
        is_solution = eval_result["is_solution"]

        node.stdout_snippet = exec_res.stdout[:500] if exec_res.stdout else exec_res.stderr[:500]
        node.tests_passed = exec_res.tests_passed
        node.tests_failed = exec_res.tests_failed
        node.is_solution = is_solution
        node.is_terminal = is_solution or (node.depth >= settings.mcts_max_depth)
        node.git_diff = self.sandbox.get_git_diff()

        if not is_solution:
            reflection_prompt = CRITIC_REFLECTION_PROMPT.format(
                command=repro_cmd,
                exit_code=exec_res.exit_code,
                test_summary=exec_res.test_summary or "Failed",
                failure_tracebacks="\n".join(exec_res.test_summary or []),
                patch_diff=node.git_diff or "No git diff recorded"
            )
            reflection_json = await self.llm.generate_json(reflection_prompt, SYSTEM_PROMPT)
            node.reflection = reflection_json.get("root_cause_of_failure", "Tests did not pass.")

        return reward, is_solution

    def _backpropagate(self, node: MCTSNode, reward: float):
        curr: Optional[MCTSNode] = node
        while curr is not None:
            curr.visit_count += 1
            curr.total_reward += reward
            if reward > curr.best_reward:
                curr.best_reward = reward
            curr = curr.parent

    def _get_all_nodes(self, root: MCTSNode) -> List[MCTSNode]:
        nodes = []
        queue = [root]
        while queue:
            curr = queue.pop(0)
            nodes.append(curr)
            queue.extend(curr.children)
        return nodes