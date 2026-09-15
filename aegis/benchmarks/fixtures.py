"""
Realistic SWE-Bench Mini Benchmark Fixtures for Evaluation.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BenchmarkTask:
    task_id: str
    repository: str
    issue_title: str
    issue_description: str
    target_file: str
    buggy_code: str
    solution_code: str
    test_file: str
    acceptance_test_code: str


BENCHMARK_TASKS: List[BenchmarkTask] = [
    BenchmarkTask(
        task_id="SWE-LITE-001",
        repository="aegis-http-client",
        issue_title="Query parameters with list values are incorrectly serialized as string representations",
        issue_description=(
            "When passing list values in query parameters dictionary e.g. {'tags': ['ai', 'ml']}, "
            "the URL builder formats it as '?tags=[ai, ml]' instead of the standard RFC-compliant "
            "repeated keys format '?tags=ai&tags=ml'."
        ),
        target_file="http_client/url_builder.py",
        buggy_code=(
            "def build_query_string(params: dict) -> str:\n"
            "    \"\"\"Serializes dictionary into URL query string.\"\"\"\n"
            "    if not params:\n"
            "        return ''\n"
            "    parts = []\n"
            "    for k, v in sorted(params.items()):\n"
            "        parts.append(f'{k}={v}')\n"
            "    return '?' + '&'.join(parts)\n"
        ),
        solution_code=(
            "def build_query_string(params: dict) -> str:\n"
            "    \"\"\"Serializes dictionary into URL query string.\"\"\"\n"
            "    if not params:\n"
            "        return ''\n"
            "    parts = []\n"
            "    for k, v in sorted(params.items()):\n"
            "        if isinstance(v, (list, tuple, set)):\n"
            "            for item in v:\n"
            "                parts.append(f'{k}={item}')\n"
            "        else:\n"
            "            parts.append(f'{k}={v}')\n"
            "    return '?' + '&'.join(parts)\n"
        ),
        test_file="tests/test_url_builder.py",
        acceptance_test_code=(
            "from http_client.url_builder import build_query_string\n\n"
            "def test_list_query_serialization():\n"
            "    res = build_query_string({'tags': ['ai', 'ml'], 'page': 1})\n"
            "    assert res == '?page=1&tags=ai&tags=ml'\n\n"
            "def test_single_value_query():\n"
            "    assert build_query_string({'key': 'val'}) == '?key=val'\n"
        )
    ),
    BenchmarkTask(
        task_id="SWE-LITE-002",
        repository="aegis-tokenizer",
        issue_title="Zero-length or whitespace-only token batches trigger ZeroDivisionError in sliding window",
        issue_description=(
            "The sliding window tokenizer crashes with ZeroDivisionError when encountering empty or "
            "all-whitespace text chunks instead of returning an empty list of windows."
        ),
        target_file="tokenizer/sliding_window.py",
        buggy_code=(
            "def create_windows(tokens: list, window_size: int, stride: int) -> list:\n"
            "    \"\"\"Splits token stream into overlapping windows.\"\"\"\n"
            "    if not tokens:\n"
            "        return []\n"
            "    windows = []\n"
            "    for i in range(0, len(tokens), stride):\n"
            "        chunk = tokens[i : i + window_size]\n"
            "        if chunk:\n"
            "            windows.append(chunk)\n"
            "    return windows\n"
        ),
        solution_code=(
            "def create_windows(tokens: list, window_size: int, stride: int) -> list:\n"
            "    \"\"\"Splits token stream into overlapping windows.\"\"\"\n"
            "    if not tokens or window_size <= 0 or stride <= 0:\n"
            "        return []\n"
            "    windows = []\n"
            "    for i in range(0, len(tokens), stride):\n"
            "        chunk = tokens[i : i + window_size]\n"
            "        if chunk:\n"
            "            windows.append(chunk)\n"
            "    return windows\n"
        ),
        test_file="tests/test_sliding_window.py",
        acceptance_test_code=(
            "from tokenizer.sliding_window import create_windows\n\n"
            "def test_zero_window_bounds():\n"
            "    assert create_windows(['a', 'b'], 0, 0) == []\n\n"
            "def test_valid_windows():\n"
            "    assert len(create_windows(['a', 'b', 'c'], 2, 1)) == 3\n"
        )
    )
]
