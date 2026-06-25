"""Workspace tree listing tests."""

from __future__ import annotations

from pathlib import Path

from operator_kernel.governance_gate import GovernanceGate
from operator_kernel.tools.workspace import WorkspaceTools


def test_list_files_includes_root_file(tmp_path: Path) -> None:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "hello.py").write_text("print('Hello World')\n", encoding="utf-8")
    tools = WorkspaceTools(ws, GovernanceGate(ws))
    out = tools.list_files()
    assert "hello.py" in out["files"]
    assert out["count"] >= 1
    assert any(n["path"] == "hello.py" for n in out["nodes"])


def test_list_files_under_runtime_workspace_root(tmp_path: Path) -> None:
    """E2E workspace lives under .runtime/; must not filter by ancestor path segment."""
    ws = tmp_path / ".runtime" / "e2e-operator-workspace"
    ws.mkdir(parents=True)
    (ws / "hello.py").write_text("print('Hello Jon')\n", encoding="utf-8")
    tools = WorkspaceTools(ws, GovernanceGate(ws))
    out = tools.list_files()
    assert "hello.py" in out["files"]


def test_list_files_skips_ignored_subdirs(tmp_path: Path) -> None:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "app.py").write_text("x\n", encoding="utf-8")
    node_modules = ws / "node_modules" / "pkg"
    node_modules.mkdir(parents=True)
    (node_modules / "index.js").write_text("x\n", encoding="utf-8")
    tools = WorkspaceTools(ws, GovernanceGate(ws))
    out = tools.list_files()
    assert "app.py" in out["files"]
    assert not any("node_modules" in p for p in out["files"])
