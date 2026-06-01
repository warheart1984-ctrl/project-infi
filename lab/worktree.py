"""Git worktree / clone isolation for lab workspaces."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

IsolationMode = Literal["worktree", "clone"]


class WorktreeError(RuntimeError):
    """Raised when git worktree operations fail."""


def _run_git(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


def find_git_root(path: Path) -> Path:
    """Resolve path to repository root containing .git."""
    candidate = path.expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    proc = _run_git(["rev-parse", "--show-toplevel"], cwd=candidate)
    if proc.returncode != 0:
        raise WorktreeError(f"not a git repository: {path} ({proc.stderr.strip()})")
    return Path(proc.stdout.strip())


def get_head_rev(repo_root: Path) -> str:
    proc = _run_git(["rev-parse", "HEAD"], cwd=repo_root)
    if proc.returncode != 0:
        raise WorktreeError(proc.stderr.strip() or "git rev-parse HEAD failed")
    return proc.stdout.strip()


def _git_common_dir(repo_root: Path) -> Path:
    proc = _run_git(["rev-parse", "--git-common-dir"], cwd=repo_root)
    if proc.returncode != 0:
        return (repo_root / ".git").resolve()
    raw = proc.stdout.strip()
    common = Path(raw)
    if not common.is_absolute():
        common = repo_root / common
    return common.resolve()


def _same_git_repository(source_root: Path, other_path: Path) -> bool:
    try:
        other_root = find_git_root(other_path)
    except WorktreeError:
        return False
    return _git_common_dir(source_root) == _git_common_dir(other_root)


def create_workspace(
    *,
    source_path: Path,
    workspace_path: Path,
    branch: str | None = None,
) -> dict[str, Any]:
    """
    Create isolated workspace under workspace_path.

    Same-repo sources use ``git worktree add``; external repos use ``git clone``.
    """
    source_root = find_git_root(source_path)
    workspace_path = workspace_path.resolve()
    if workspace_path.exists() and any(workspace_path.iterdir()):
        raise WorktreeError(f"workspace already exists and is non-empty: {workspace_path}")

    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    ref = branch or "HEAD"
    init_head = get_head_rev(source_root)

    lab_host_root = find_git_root(workspace_path.parent)
    use_worktree = _same_git_repository(source_root, lab_host_root)

    if use_worktree:
        # worktree from same repository
        if workspace_path.exists():
            if workspace_path.is_dir() and not list(workspace_path.iterdir()):
                workspace_path.rmdir()
            else:
                raise WorktreeError(f"workspace path blocked: {workspace_path}")
        proc = _run_git(
            ["worktree", "add", "--detach", str(workspace_path), ref],
            cwd=source_root,
        )
        if proc.returncode != 0:
            raise WorktreeError(
                f"git worktree add failed: {(proc.stderr or proc.stdout).strip()}"
            )
        mode: IsolationMode = "worktree"
    else:
        # external repo — local clone
        if workspace_path.exists():
            raise WorktreeError(f"workspace path exists: {workspace_path}")
        proc = _run_git(
            ["clone", "--local", str(source_root), str(workspace_path)],
        )
        if proc.returncode != 0:
            proc = _run_git(["clone", str(source_root), str(workspace_path)])
        if proc.returncode != 0:
            raise WorktreeError(f"git clone failed: {(proc.stderr or proc.stdout).strip()}")
        mode = "clone"
        init_head = get_head_rev(workspace_path)

    return {
        "source_path": str(source_root.resolve()),
        "workspace_path": str(workspace_path.resolve()),
        "init_head": init_head,
        "isolation_mode": mode,
        "branch": branch or "",
    }


def git_snapshot(workspace: Path) -> dict[str, Any]:
    """Capture HEAD and porcelain status for session snapshots."""
    head = get_head_rev(workspace)
    status_proc = _run_git(["status", "--porcelain"], cwd=workspace)
    diff_proc = _run_git(["diff", "--stat"], cwd=workspace)
    return {
        "head": head,
        "porcelain": (status_proc.stdout or "").strip(),
        "diff_stat": (diff_proc.stdout or "").strip(),
    }


def git_diff(workspace: Path) -> str:
    proc = _run_git(["diff"], cwd=workspace)
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def revert_workspace(workspace: Path) -> None:
    """Reset tracked files and remove untracked files inside workspace only."""
    checkout = _run_git(["checkout", "--", "."], cwd=workspace)
    if checkout.returncode != 0:
        raise WorktreeError(f"git checkout failed: {checkout.stderr.strip()}")
    clean = _run_git(["clean", "-fd"], cwd=workspace)
    if clean.returncode != 0:
        raise WorktreeError(f"git clean failed: {clean.stderr.strip()}")


def python_executable() -> str:
    return sys.executable
