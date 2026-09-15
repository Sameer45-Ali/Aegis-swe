"""
Tests for Sandbox Execution and Pytest Output Parser.
"""

from pathlib import Path
import tempfile
import pytest
from aegis.sandbox.local_runner import LocalSandboxRunner
from aegis.sandbox.test_parser import TestOutputParser


def test_pytest_output_parser():
    sample_stdout = "================ 2 passed, 1 failed in 0.45s ================"
    res = TestOutputParser.parse_pytest(sample_stdout, "")
    assert res["passed"] == 2
    assert res["failed"] == 1
    assert res["is_all_passed"] is False


def test_local_sandbox_execution():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "sample.py"
        test_file.write_text("print('hello aegis')", encoding="utf-8")

        runner = LocalSandboxRunner(temp_dir)
        exec_res = runner.run_command("python sample.py")
        assert exec_res.exit_code == 0
        assert "hello aegis" in exec_res.stdout
        runner.cleanup()
