"""
SWE-Bench Evaluation Suite and Metrics Engine.
Runs Aegis-SWE against standardized benchmark tasks and outputs Pass@1 metrics.
"""

import asyncio
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from aegis.benchmarks.fixtures import BENCHMARK_TASKS, BenchmarkTask
from aegis.core.mcts.tree_search import MCTSSearchEngine
from aegis.sandbox.local_runner import LocalSandboxRunner

PYTEST_CMD = f"{sys.executable} -m pytest"


class BenchmarkSuiteRunner:
    """Automated benchmark runner for SWE evaluation."""

    def __init__(self, tasks: List[BenchmarkTask] = BENCHMARK_TASKS):
        self.tasks = tasks
        self.console = Console(legacy_windows=False) if sys.platform == "win32" else Console()

    async def run_task(self, task: BenchmarkTask) -> Dict[str, any]:
        """Sets up a clean workspace for a benchmark task and runs Aegis."""
        temp_dir = Path(tempfile.mkdtemp(prefix=f"aegis_bench_{task.task_id}_"))
        try:
            # 1. Populate workspace with buggy code and acceptance tests
            target_path = temp_dir / task.target_file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(task.buggy_code, encoding="utf-8")

            test_path = temp_dir / task.test_file
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(task.acceptance_test_code, encoding="utf-8")

            # 2. Run MCTS Agent
            start_time = time.time()
            sandbox = LocalSandboxRunner(temp_dir)
            engine = MCTSSearchEngine(
                repo_path=str(temp_dir),
                issue_description=task.issue_description,
                sandbox=sandbox
            )
            solution = await engine.run_search(max_iterations=8)
            duration = time.time() - start_time

            # 3. Verify ground truth acceptance tests on final sandbox state
            final_test_res = sandbox.run_command(f"{PYTEST_CMD} {task.test_file}")
            is_resolved = (final_test_res.exit_code == 0 and final_test_res.tests_passed > 0 and final_test_res.tests_failed == 0)

            return {
                "task_id": task.task_id,
                "repository": task.repository,
                "resolved": is_resolved,
                "duration_seconds": round(duration, 2),
                "nodes_explored": len(engine._get_all_nodes(engine.root)),
                "git_diff": sandbox.get_git_diff() if is_resolved else None
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def run_all(self) -> List[Dict[str, any]]:
        self.console.print(f"\n[bold cyan][AEGIS] Launching Aegis-SWE Benchmark Suite ({len(self.tasks)} Tasks)...[/bold cyan]\n")
        results = []

        for task in self.tasks:
            self.console.print(f"[yellow]Evaluating {task.task_id}: {task.issue_title[:60]}...[/yellow]")
            res = await self.run_task(task)
            results.append(res)

        self._print_scorecard(results)
        return results

    def _print_scorecard(self, results: List[Dict[str, any]]):
        table = Table(title="[AEGIS] SWE-Bench Evaluation Scorecard", show_header=True, header_style="bold magenta")
        table.add_column("Task ID", style="dim", width=14)
        table.add_column("Repository", width=20)
        table.add_column("Resolved (Pass@1)", justify="center", width=18)
        table.add_column("Duration (s)", justify="right", width=14)
        table.add_column("Nodes Visited", justify="right", width=14)

        resolved_count = 0
        total_time = 0.0

        for r in results:
            status = "[bold green][PASS][/bold green]" if r["resolved"] else "[bold red][FAIL][/bold red]"
            if r["resolved"]:
                resolved_count += 1
            total_time += r["duration_seconds"]
            table.add_row(
                r["task_id"],
                r["repository"],
                status,
                str(r["duration_seconds"]),
                str(r["nodes_explored"])
            )

        pass_rate = (resolved_count / len(results)) * 100 if results else 0
        self.console.print(table)
        self.console.print(f"\n[bold green]Summary: Pass@1 = {pass_rate:.1f}% ({resolved_count}/{len(results)} tasks resolved in {total_time:.2f}s)[/bold green]\n")


if __name__ == "__main__":
    runner = BenchmarkSuiteRunner()
    asyncio.run(runner.run_all())