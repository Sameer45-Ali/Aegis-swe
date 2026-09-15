"""
=============================================================================
  🛡️ Aegis-SWE: Autonomous Coding Agent — Interactive Test Runner
=============================================================================
Run this script to see Aegis-SWE explore, test, and solve bugs autonomously!
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from aegis.core.mcts.tree_search import MCTSSearchEngine
from aegis.sandbox.local_runner import LocalSandboxRunner

# Sample Test Repositories with Real Bugs for You to Test
BUG_CATALOG = {
    "1": {
        "title": "Shopping Cart Calculator (Missing Quantity & Negative Discount)",
        "file_name": "shop/calculator.py",
        "buggy_code": """def calculate_cart_total(items: list, discount_percent: float = 0.0, tax_rate: float = 0.05) -> float:
    if not items:
        return 0.0
    subtotal = 0.0
    for item in items:
        # BUG: Crashes with KeyError if 'quantity' key is missing!
        subtotal += item["price"] * item["quantity"]
    
    # BUG: No check for negative or > 100 discount
    discount_amount = subtotal * (discount_percent / 100.0)
    discounted = subtotal - discount_amount
    return round(discounted * (1.0 + tax_rate), 2)
""",
        "existing_test": """from shop.calculator import calculate_cart_total

def test_basic():
    assert calculate_cart_total([{'name': 'Shirt', 'price': 20.0, 'quantity': 2}]) == 42.0
""",
        "issue": "In shop/calculator.py, calculate_cart_total crashes with KeyError when an item in items list does not specify 'quantity' (default should be 1). Also raise ValueError('Invalid discount percent') if discount is negative or above 100."
    },
    "2": {
        "title": "URL Query Parameter Builder (List Serialization Bug)",
        "file_name": "http_client/url_builder.py",
        "buggy_code": """def build_query_string(params: dict) -> str:
    if not params:
        return ''
    parts = []
    for k, v in sorted(params.items()):
        # BUG: Formats list as '[ai, ml]' instead of repeated keys '?tags=ai&tags=ml'
        parts.append(f'{k}={v}')
    return '?' + '&'.join(parts)
""",
        "existing_test": """from http_client.url_builder import build_query_string

def test_single():
    assert build_query_string({'page': 1}) == '?page=1'
""",
        "issue": "When passing list values in query dictionary e.g. {'tags': ['ai', 'ml']}, build_query_string formats it as '?tags=[ai, ml]' instead of repeated keys '?tags=ai&tags=ml'."
    },
    "3": {
        "title": "Sliding Window Tokenizer (Zero-Division Crash Bug)",
        "file_name": "tokenizer/sliding_window.py",
        "buggy_code": """def create_windows(tokens: list, window_size: int, stride: int) -> list:
    if not tokens:
        return []
    windows = []
    # BUG: If window_size <= 0 or stride <= 0, crashes with ZeroDivision or Infinite loop
    for i in range(0, len(tokens), stride):
        chunk = tokens[i : i + window_size]
        if chunk:
            windows.append(chunk)
    return windows
""",
        "existing_test": """from tokenizer.sliding_window import create_windows

def test_valid():
    assert len(create_windows(['a', 'b', 'c'], 2, 1)) == 3
""",
        "issue": "The sliding window tokenizer crashes when encountering zero or negative window_size/stride instead of safely returning an empty list []."
    }
}


async def run_interactive_test():
    print("=" * 70)
    print("   🛡️  AEGIS-SWE: AUTONOMOUS SOFTWARE ENGINEERING AGENT")
    print("=" * 70)
    print("\nSelect a bug to test:\n")
    for key, val in BUG_CATALOG.items():
        print(f"  [{key}] {val['title']}")
    print("  [4] Custom issue (type your own)")

    choice = input("\nEnter choice (1, 2, 3, or 4) [default: 1]: ").strip() or "1"
    
    if choice in BUG_CATALOG:
        task = BUG_CATALOG[choice]
    else:
        task = BUG_CATALOG["1"]

    # 1. Create temporary sandbox workspace
    temp_dir = Path(tempfile.mkdtemp(prefix="aegis_user_test_"))
    print(f"\n[+] Created isolated test workspace: {temp_dir}")

    target_file = temp_dir / task["file_name"]
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(task["buggy_code"], encoding="utf-8")

    test_file = temp_dir / "tests" / "test_existing.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(task["existing_test"], encoding="utf-8")

    print("\n" + "-" * 70)
    print(f"  BUGGY CODE ({task['file_name']}):")
    print("-" * 70)
    print(task["buggy_code"])
    print("-" * 70)
    print(f"  ISSUE PROMPT:")
    print(f"  {task['issue']}")
    print("-" * 70)

    input("\nPress ENTER to start Aegis-SWE autonomous solver...")

    # 2. Run MCTS Engine
    start_time = time.time()
    sandbox = LocalSandboxRunner(temp_dir)

    def on_event(event):
        t = event.get("type")
        d = event.get("data", {})
        if t == "iteration_start":
            print(f"\n[MCTS] Exploring Branch Iteration {d.get('iteration')}/{d.get('total')}...")
        elif t == "node_created":
            print(f"   -> Node Created: [{d.get('id')}] ({d.get('action_type')}) - {d.get('summary')}")
        elif t == "solution_found":
            print(f"\n[✨ SUCCESS] 100% Verified Solution at Node [{d.get('id')}]! Reward: {d.get('mean_reward')}")

    engine = MCTSSearchEngine(
        repo_path=str(temp_dir),
        issue_description=task["issue"],
        sandbox=sandbox,
        on_node_event=on_event
    )

    solution = await engine.run_search(max_iterations=6)
    elapsed = round(time.time() - start_time, 2)

    if solution and solution.action_payload.get("updated_content"):
        print("\n" + "=" * 70)
        print(f"  ✅ VERIFIED FIXED CODE GENERATED BY AEGIS (Resolved in {elapsed}s):")
        print("=" * 70)
        print(solution.action_payload.get("updated_content"))
        print("=" * 70)
        print(f"Tests Passed: {solution.tests_passed} | Tests Failed: {solution.tests_failed}")
        print("=" * 70)
    else:
        print("\n[-] Could not resolve bug within iteration limit.")

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"\n[+] Sandbox cleaned up successfully.")


if __name__ == "__main__":
    asyncio.run(run_interactive_test())