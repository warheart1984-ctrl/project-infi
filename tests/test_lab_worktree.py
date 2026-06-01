"""Worktree and project init tests for lab console."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from lab.project import init_project
from lab.worktree import WorktreeError, create_workspace, find_git_root, get_head_rev

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = REPO_ROOT / "lab" / "fixtures" / "sample-repo"


def _git(args: list[str], *, cwd: Path) -> None:
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip())


@pytest.fixture()
def bare_fixture_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo for isolation tests."""
    repo = tmp_path / "fixture"
    repo.mkdir()
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(["init"], cwd=repo)
    _git(["config", "user.email", "lab@test"], cwd=repo)
    _git(["config", "user.name", "Lab Test"], cwd=repo)
    _git(["add", "."], cwd=repo)
    _git(["commit", "-m", "init"], cwd=repo)
    return repo


def test_find_git_root_fixture(bare_fixture_repo: Path) -> None:
    root = find_git_root(bare_fixture_repo)
    assert root.resolve() == bare_fixture_repo.resolve()


def test_create_workspace_worktree(bare_fixture_repo: Path, tmp_path: Path) -> None:
    host = tmp_path / "host"
    host.mkdir()
    _git(["init"], cwd=host)
    _git(["config", "user.email", "lab@test"], cwd=host)
    _git(["config", "user.name", "Lab Test"], cwd=host)
    (host / ".gitkeep").write_text("", encoding="utf-8")
    _git(["add", "."], cwd=host)
    _git(["commit", "-m", "host"], cwd=host)

    workspace = tmp_path / "lab-runtime" / "workspace"
    info = create_workspace(source_path=bare_fixture_repo, workspace_path=workspace)
    assert info["isolation_mode"] == "clone"
    assert (workspace / "README.md").is_file()
    assert get_head_rev(workspace)


def test_init_project_from_fixture(bare_fixture_repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    result = init_project(
        project_id="test-lab",
        source=bare_fixture_repo,
        runtime_root=runtime,
        ledger_path=runtime / "lab_ledger.jsonl",
    )
    assert result["project_id"] == "test-lab"
    ws = Path(result["workspace_path"])
    assert ws.is_dir()
    assert (ws / "README.md").is_file()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="full-repo worktree hits Windows MAX_PATH on this checkout",
)
def test_init_runtime_inside_repo_uses_worktree(tmp_path: Path) -> None:
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("parent repo is not a git checkout")
    runtime = REPO_ROOT / ".runtime" / "lab" / f"pytest-{tmp_path.name}"
    project_id = "infi-bench-wt"
    try:
        result = init_project(
            project_id=project_id,
            source=REPO_ROOT,
            runtime_root=runtime,
            ledger_path=runtime / "lab_ledger.jsonl",
        )
        assert result["isolation_mode"] == "worktree"
        assert Path(result["workspace_path"]).is_dir()
    finally:
        import shutil

        shutil.rmtree(runtime / project_id, ignore_errors=True)


def test_init_external_runtime_uses_clone(tmp_path: Path, bare_fixture_repo: Path) -> None:
    runtime = tmp_path / "external-runtime"
    result = init_project(
        project_id="external-bench",
        source=bare_fixture_repo,
        runtime_root=runtime,
        ledger_path=runtime / "lab_ledger.jsonl",
    )
    assert result["isolation_mode"] == "clone"
    assert Path(result["workspace_path"]).is_dir()


def test_create_workspace_rejects_nonempty(tmp_path: Path, bare_fixture_repo: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "blocked.txt").write_text("x", encoding="utf-8")
    with pytest.raises(WorktreeError):
        create_workspace(source_path=bare_fixture_repo, workspace_path=workspace)
