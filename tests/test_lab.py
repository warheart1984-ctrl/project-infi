"""Tests for Lab-Grade Coding Console v1."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lab.governance import GovernanceDenied, resolve_workspace_path
from lab.ledger import append_ledger_entry, read_ledger
from lab.project import init_project, project_dir
from lab.session import LabSession
from lab.spec import LabProjectSpec, ProhibitionsSpec, load_lab_spec, default_instruments
from lab.spine import build_lab_spine_profile
from lab.tools import invoke_tool

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = REPO_ROOT / "lab" / "specs" / "default.yaml"


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
    (source / "README.md").write_text("source\n", encoding="utf-8")
    (source / "protected.txt").write_text("do not edit\n", encoding="utf-8")
    _git_init_repo(source)

    runtime = tmp_path / "runtime"
    spec = LabProjectSpec(
        project_id="unit-lab",
        intent_summary="unit test bench",
        source_repo=str(source),
        prohibitions=ProhibitionsSpec(
            forbidden_commands=["rm -rf"],
            network_allowed=False,
            read_only_paths=["protected.txt"],
            high_impact_patterns=["secret/**"],
        ),
        instruments=default_instruments(),
    )
    spec_path = tmp_path / "spec.yaml"
    import yaml

    spec_path.write_text(yaml.dump(spec.to_dict()), encoding="utf-8")

    result = init_project(
        spec_path=spec_path,
        source=source,
        runtime_root=runtime,
        ledger_path=runtime / "lab_ledger.jsonl",
    )
    return {"runtime": str(runtime), "project_id": result["project_id"], "source": str(source)}


def test_load_default_spec() -> None:
    if not DEFAULT_SPEC.is_file():
        pytest.skip("default spec missing")
    spec = load_lab_spec(DEFAULT_SPEC)
    assert spec.project_id == "nova-ai-factory"
    assert spec.spec_version == "lab.lab_project_spec.v1"


def test_spine_profile_shape() -> None:
    spec = LabProjectSpec(project_id="spine-test", intent_summary="test")
    profile = build_lab_spine_profile(spec)
    assert profile["stages"]["rls_substrate"]["network_allowed"] is False
    assert "jarvis_authorize" in profile["stages"]


def test_path_jail_escape(lab_project: dict[str, str]) -> None:
    ws = project_dir(lab_project["project_id"], runtime_root=Path(lab_project["runtime"])) / "workspace"
    with pytest.raises(GovernanceDenied):
        resolve_workspace_path(ws, "../outside.txt")


def test_read_only_write_denied(lab_project: dict[str, str]) -> None:
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="test-agent",
        runtime_root=Path(lab_project["runtime"]),
        ledger_path=Path(lab_project["runtime"]) / "lab_ledger.jsonl",
    )
    try:
        receipt = session.invoke_tool(
            "write_file",
            args={"path": "protected.txt", "content": "nope"},
        )
        assert receipt.status == "denied"
    finally:
        if not session._closed:
            session.close(status="ok")


def test_read_write_and_receipt(lab_project: dict[str, str]) -> None:
    runtime = Path(lab_project["runtime"])
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="test-agent",
        runtime_root=runtime,
        ledger_path=runtime / "lab_ledger.jsonl",
    )
    read_r = session.invoke_tool("read_file", args={"path": "README.md"})
    assert read_r.status == "ok"
    write_r = session.invoke_tool(
        "write_file",
        args={"path": "notes.txt", "content": "experiment note"},
    )
    assert write_r.status == "ok"
    receipt = session.close(status="ok")

    assert receipt["status"] == "ok"
    assert "README.md" in receipt["files_read"]
    assert "notes.txt" in receipt["files_written"]
    receipt_path = (
        project_dir(lab_project["project_id"], runtime_root=runtime)
        / "sessions"
        / receipt["session_id"]
        / "LAB_SESSION_RECEIPT.json"
    )
    assert receipt_path.is_file()


def test_ledger_append(lab_project: dict[str, str]) -> None:
    ledger = Path(lab_project["runtime"]) / "lab_ledger.jsonl"
    append_ledger_entry({"event": "test", "project_id": lab_project["project_id"]}, ledger_path=ledger)
    rows = read_ledger(ledger_path=ledger)
    assert any(row.get("event") == "init" for row in rows)


def test_list_tools_schema(lab_project: dict[str, str]) -> None:
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="test-agent",
        runtime_root=Path(lab_project["runtime"]),
    )
    try:
        tools = session.list_tools()
        names = {item["name"] for item in tools}
        assert "read_file" in names
        assert "run_pytest" in names
    finally:
        if not session._closed:
            session.close(status="ok")


def test_invoke_unknown_tool(lab_project: dict[str, str]) -> None:
    session = LabSession.open(
        project_id=lab_project["project_id"],
        agent="test-agent",
        runtime_root=Path(lab_project["runtime"]),
    )
    try:
        receipt = invoke_tool(session, "nonexistent_tool")
        assert receipt.status == "denied"
    finally:
        if not session._closed:
            session.close(status="ok")
