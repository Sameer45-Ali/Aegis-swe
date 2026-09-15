"""
Base Sandbox Interface and Execution Data Models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    tests_passed: int = 0
    tests_failed: int = 0
    tests_errored: int = 0
    test_summary: Optional[str] = None


class BaseSandbox(ABC):
    """Abstract interface for code execution environments."""

    @abstractmethod
    def run_command(self, command: str, timeout_seconds: Optional[int] = None) -> ExecutionResult:
        """Runs a bash/shell command inside the sandbox."""
        pass

    @abstractmethod
    def apply_patch(self, patch_content: str) -> bool:
        """Applies a unified git diff patch to the sandbox workspace."""
        pass

    @abstractmethod
    def write_file(self, relative_path: str, content: str) -> bool:
        """Writes or updates a file in the sandbox workspace."""
        pass

    @abstractmethod
    def read_file(self, relative_path: str) -> Optional[str]:
        """Reads a file from the sandbox workspace."""
        pass

    @abstractmethod
    def get_git_diff(self) -> str:
        """Returns the current git diff of the workspace."""
        pass

    @abstractmethod
    def reset_workspace(self) -> bool:
        """Resets the workspace back to clean git HEAD."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Tears down sandbox resources (containers, temp dirs)."""
        pass
