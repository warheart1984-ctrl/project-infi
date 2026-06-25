"""Git helpers for operator kernel."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(workspace_root: Path, args: list[str], timeout: int = 60) -> dict:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "args": args,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }


def git_status(workspace_root: Path) -> dict:
    return _run_git(workspace_root, ["status", "--short", "--branch"])


def git_diff(workspace_root: Path, path: str = "") -> dict:
    args = ["diff"]
    if path.strip():
        args.append(path.strip())
    return _run_git(workspace_root, args, timeout=120)


def git_commit(workspace_root: Path, message: str) -> dict:
    if not message.strip():
        raise ValueError("commit message is required")
    add = _run_git(workspace_root, ["add", "-A"])
    if not add["ok"]:
        return {"stage": add, "commit": None, "ok": False}
    commit = _run_git(workspace_root, ["commit", "-m", message.strip()])
    return {"stage": add, "commit": commit, "ok": commit["ok"]}
