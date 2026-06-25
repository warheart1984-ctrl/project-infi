"""Shell and test execution tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(workspace_root: Path, command: str, timeout: int = 120) -> dict:
    completed = subprocess.run(
        command,
        cwd=str(workspace_root),
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": _clip(completed.stdout),
        "stderr": _clip(completed.stderr),
        "ok": completed.returncode == 0,
    }


def run_tests(workspace_root: Path, target: str = "") -> dict:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if target.strip():
        cmd.append(target.strip())
    completed = subprocess.run(
        cmd,
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return {
        "command": " ".join(cmd),
        "exit_code": completed.returncode,
        "stdout": _clip(completed.stdout),
        "stderr": _clip(completed.stderr),
        "ok": completed.returncode == 0,
    }


def _clip(text: str, limit: int = 8000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
