"""Tests for Lab ↔ Forge bridge."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lab.forge_bridge import build_lab_workspace_context, create_lab_patch_plan, create_lab_patch_review
from lab.project import init_project
from lab.session import LabSession
from lab.spec import InstrumentSpec, LabProjectSpec, ProhibitionsSpec, default_instruments
from lab.tools import invoke_tool

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git_init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "lab@test"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Lab Test"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(path), check=True, capture_output=True)


@pytest.fixture()
def lab_project(tmp_path: Path) -> dict[str, str]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("lab forge bridge\n", encoding="utf-8")
    (source / "module.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    _git_init_repo(source)

    runtime = tmp_path / "runtime"
    spec = LabProjectSpec(
        project_id="forge-bridge-lab",
        intent_summary="forge bridge test",
        source_repo=str(source),
        prohibitions=ProhibitionsSpec(forbidden_commands=["rm -rf"], network_allowed=False),
        instruments=[
            *default_instruments(),
            InstrumentSpec(name="forge_patch_plan", kind="forge_bridge"),
            InstrumentSpec(name="create_patch_review", kind="forge_bridge"),
        ],
    )
    spec_path = tmp_path / "spec.yaml"
    import yaml

    spec_path.write_text(yaml.dump(spec.to_dict()), encoding="utf-8")
    init_project(
        spec_path=spec_path,
        source=source,
        runtime_root=runtime,
        ledger_path=runtime / "lab_ledger.jsonl",
    )
    return {"runtime": str(runtime), "project_id": "forge-bridge-lab"}


def test_build_lab_workspace_context(lab_project: dict[str, str]) -> None:
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="coding-agent-v1",
        runtime_root=Path(lab_project["runtime"]),
    )
    try:
        ctx = build_lab_workspace_context(session, goal="update module hello")
        assert ctx["lab_session_id"] == session.session_id
        assert any(item.get("relative_path") == "module.py" for item in ctx["files"])
    finally:
        if not session._closed:
            session.close(status="ok")


def test_create_lab_patch_review_links_session(lab_project: dict[str, str]) -> None:
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="coding-agent-v1",
        runtime_root=Path(lab_project["runtime"]),
    )
    try:
        payload = create_lab_patch_review(session, goal="Improve module hello")
        review_id = (payload.get("review") or {}).get("id") or (payload.get("review") or {}).get("review_id")
        assert review_id
        assert review_id in payload.get("review_ids", [])
        plan = payload.get("patch_plan") or {}
        assert plan.get("lab_session_id") == session.session_id
    finally:
        if not session._closed:
            session.close(status="ok")


def test_forge_bridge_instruments(lab_project: dict[str, str]) -> None:
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="coding-agent-v1",
        runtime_root=Path(lab_project["runtime"]),
    )
    try:
        plan_receipt = invoke_tool(session, "forge_patch_plan", args={"goal": "Document README"})
        assert plan_receipt.status == "ok"
        review_receipt = invoke_tool(session, "create_patch_review", args={"goal": "Document README"})
        assert review_receipt.status == "ok"
        receipt = session.close()
        assert receipt.get("patch_review_ids")
        assert "stage2_metrics" in receipt
    finally:
        if session._closed is False:
            pass
