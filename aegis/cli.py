"""
Aegis-SWE Command Line Interface.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from aegis.benchmarks.benchmark_suite import BenchmarkSuiteRunner
from aegis.core.mcts.tree_search import MCTSSearchEngine

console = Console()


@click.group()
def main():
    """Aegis-SWE: Autonomous Software Engineering Agent with MCTS."""
    pass


@main.command()
@click.option("--repo", required=True, help="Path to target repository.")
@click.option("--issue", required=True, help="Issue or bug description to solve.")
@click.option("--iterations", default=10, help="Max MCTS iterations.")
def solve(repo: str, issue: str, iterations: int):
    """Autonomously investigates and fixes an issue in the target repository."""
    console.print(Panel.fit(
        f"[bold cyan]🛡️ Aegis-SWE Autonomous Solver[/bold cyan]\n"
        f"[yellow]Target Repository:[/yellow] {repo}\n"
        f"[yellow]Issue:[/yellow] {issue}",
        border_style="cyan"
    ))

    def on_event(event):
        event_type = event.get("type")
        data = event.get("data", {})
        if event_type == "iteration_start":
            console.print(f"[dim]• MCTS Iteration {data.get('iteration')}/{data.get('total')}...[/dim]")
        elif event_type == "solution_found":
            console.print(f"[bold green]✨ Solution Verified at Node {data.get('id')}! (Reward = {data.get('mean_reward')})[/bold green]")

    engine = MCTSSearchEngine(repo_path=repo, issue_description=issue, on_node_event=on_event)
    solution = asyncio.run(engine.run_search(max_iterations=iterations))

    if solution and solution.git_diff:
        console.print("\n[bold green]✅ Generated Verified Git Diff Patch:[/bold green]\n")
        console.print(f"```diff\n{solution.git_diff}\n```")
    else:
        console.print("\n[bold red]❌ Could not find a 100% verified passing patch within iteration limit.[/bold red]")


@main.command()
def benchmark():
    """Runs the SWE-Bench mini evaluation suite and outputs metrics."""
    runner = BenchmarkSuiteRunner()
    asyncio.run(runner.run_all())


if __name__ == "__main__":
    main()
