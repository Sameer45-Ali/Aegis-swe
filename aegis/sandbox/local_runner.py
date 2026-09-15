"""
Isolated Local Subprocess Sandbox Runner.
Creates ephemeral worktrees/temp directories and executes commands with timeout enforcement.
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from aegis.sandbox.base import BaseSandbox, ExecutionResult
from aegis.sandbox.test_parser import TestOutputParser


class LocalSandboxRunner(BaseSandbox):
    """Executes commands and patches inside an isolated local directory copy."""

    def __init__(self, source_repo_path: str | Path):
        self.source_repo = Path(source_repo_path).resolve()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aegis_sandbox_"))
        self._copy_repo()

    def _copy_repo(self):
        """Copies the target repository into the isolated sandbox folder."""
        if not self.source_repo.exists():
            raise FileNotFoundError(f"Source repository not found: {self.source_repo}")
        
        # Copy directory excluding large caches
        def ignore_patterns(path, names):
            return {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}

        for item in self.source_repo.iterdir():
            if item.name in {".git", ".venv", "venv", "__pycache__", "node_modules"}:
                continue
            dest = self.temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=ignore_patterns)
            else:
                shutil.copy2(item, dest)

    def run_command(self, command: str, timeout_seconds: Optional[int] = 30) -> ExecutionResult:
        start_time = time.time()
        timed_out = False
        try:
            res = subprocess.run(
                command,
                cwd=str(self.temp_dir),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=dict(os.environ, PYTHONPATH=str(self.temp_dir))
            )
            stdout = res.stdout or ""
            stderr = res.stderr or ""
            exit_code = res.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            stdout = e.stdout or "" if hasattr(e, "stdout") else ""
            stderr = f"Command timed out after {timeout_seconds} seconds."
            exit_code = 124
        except Exception as e:
            stdout = ""
            stderr = f"Execution error: {str(e)}"
            exit_code = 1

        duration = time.time() - start_time
        test_metrics = TestOutputParser.parse_pytest(stdout, stderr)

        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            timed_out=timed_out,
            tests_passed=test_metrics["passed"],
            tests_failed=test_metrics["failed"],
            tests_errored=test_metrics["errored"],
            test_summary=test_metrics["raw_summary"]
        )

    def apply_patch(self, patch_content: str) -> bool:
        """Applies a patch or unified diff directly."""
        try:
            patch_file = self.temp_dir / "aegis_temp.patch"
            patch_file.write_text(patch_content, encoding="utf-8")
            
            # Try git apply or patch command
            res = subprocess.run(
                f"git apply aegis_temp.patch",
                cwd=str(self.temp_dir),
                shell=True,
                capture_output=True,
                text=True
            )
            if patch_file.exists():
                patch_file.unlink()
            return res.returncode == 0
        except Exception:
            return False

    def write_file(self, relative_path: str, content: str) -> bool:
        try:
            clean_path = relative_path.replace("\\", "/").lstrip("/")
            target = self.temp_dir / clean_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def read_file(self, relative_path: str) -> Optional[str]:
        try:
            clean_path = relative_path.replace("\\", "/").lstrip("/")
            target = self.temp_dir / clean_path
            if target.exists() and target.is_file():
                return target.read_text(encoding="utf-8", errors="replace")
            return None
        except Exception:
            return None

    def get_git_diff(self) -> str:
        """Generates unified diff between original source and current sandbox."""
        try:
            res = subprocess.run(
                f"git diff",
                cwd=str(self.temp_dir),
                shell=True,
                capture_output=True,
                text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass
        return ""

    def reset_workspace(self) -> bool:
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = Path(tempfile.mkdtemp(prefix="aegis_sandbox_"))
            self._copy_repo()
            return True
        except Exception:
            return False

    def cleanup(self) -> None:
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
