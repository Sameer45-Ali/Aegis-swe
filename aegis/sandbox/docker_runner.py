"""
Docker Container Execution Sandbox Runner.
Mounts workspace in an ephemeral Linux container with memory/CPU constraints.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional
from aegis.sandbox.base import BaseSandbox, ExecutionResult
from aegis.sandbox.test_parser import TestOutputParser


class DockerSandboxRunner(BaseSandbox):
    """Executes code inside an ephemeral isolated Docker container."""

    def __init__(self, source_repo_path: str | Path, image_name: str = "python:3.11-slim"):
        self.source_repo = Path(source_repo_path).resolve()
        self.image_name = image_name
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aegis_docker_"))
        self._copy_repo()
        self._init_docker()

    def _init_docker(self):
        try:
            import docker
            self.client = docker.from_env()
            self.docker_available = True
        except Exception:
            self.client = None
            self.docker_available = False

    def _copy_repo(self):
        for item in self.source_repo.iterdir():
            if item.name in {".git", ".venv", "venv", "__pycache__", "node_modules"}:
                continue
            dest = self.temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    def run_command(self, command: str, timeout_seconds: Optional[int] = 45) -> ExecutionResult:
        if not self.docker_available or not self.client:
            # Fallback to local execution if Docker daemon is not active
            from aegis.sandbox.local_runner import LocalSandboxRunner
            local = LocalSandboxRunner(self.source_repo)
            res = local.run_command(command, timeout_seconds)
            local.cleanup()
            return res

        start_time = time.time()
        timed_out = False
        container = None
        try:
            container = self.client.containers.run(
                image=self.image_name,
                command=f"bash -c 'export PYTHONPATH=/workspace && cd /workspace && {command}'",
                volumes={str(self.temp_dir): {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                detach=True,
                mem_limit="1g",
                network_disabled=False
            )
            res = container.wait(timeout=timeout_seconds)
            exit_code = res.get("StatusCode", 1)
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        except Exception as e:
            exit_code = 124
            timed_out = True
            stdout = ""
            stderr = f"Docker execution error or timeout: {str(e)}"
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

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
        res = self.run_command(f"echo '{patch_content}' | git apply - || patch -p1 < aegis.patch")
        return res.exit_code == 0

    def write_file(self, relative_path: str, content: str) -> bool:
        try:
            target = self.temp_dir / relative_path.replace("\\", "/").lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def read_file(self, relative_path: str) -> Optional[str]:
        try:
            target = self.temp_dir / relative_path.replace("\\", "/").lstrip("/")
            if target.exists() and target.is_file():
                return target.read_text(encoding="utf-8", errors="replace")
            return None
        except Exception:
            return None

    def get_git_diff(self) -> str:
        res = self.run_command("git diff")
        return res.stdout if res.exit_code == 0 else ""

    def reset_workspace(self) -> bool:
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aegis_docker_"))
        self._copy_repo()
        return True

    def cleanup(self) -> None:
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
