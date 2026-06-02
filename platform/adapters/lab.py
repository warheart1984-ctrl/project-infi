"""Lab session adapter — platform job dispatch for governed lab bench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.experiment import list_experiments
from lab.project import ProjectError, init_project, project_dir, project_status
from lab.session import LabSession, SessionError


def run_lab_session(
    *,
    project_id: str,
    agent: str = "platform-agent",
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    root = runtime_root or Path(".runtime/lab")
    spec_path = project_dir(project_id, runtime_root=root) / "LAB_PROJECT_SPEC.json"
    if not spec_path.is_file():
        raise ValueError(f"lab project not initialized: {project_id}")
    session = LabSession.open(project_id=project_id, agent=agent, runtime_root=root)
    with session:
        readme = session.workspace / "README.md"
        if readme.is_file():
            session.invoke_tool("read_file", args={"path": "README.md"})
    receipt_path = session.session_dir / "LAB_SESSION_RECEIPT.json"
    return {
        "project_id": project_id,
        "session_id": session.session_id,
        "receipt_path": str(receipt_path),
        "artifact_dir": str(session.session_dir),
    }


def run_lab_session_start(
    *,
    project_id: str,
    agent: str = "platform-agent",
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    session = LabSession.open(project_id=project_id, agent=agent, runtime_root=runtime_root)
    return {
        "project_id": project_id,
        "session_id": session.session_id,
        "tools": session.list_tools(),
        "artifact_dir": str(session.session_dir),
    }


def run_lab_tool_invoke(
    *,
    project_id: str,
    session_id: str,
    tool: str,
    args: dict[str, Any] | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    session = LabSession.resume(project_id=project_id, session_id=session_id, runtime_root=runtime_root)
    receipt = session.invoke_tool(tool, args=args or {})
    return {"project_id": project_id, "session_id": session_id, "receipt": receipt.to_dict()}


def run_lab_session_close(
    *,
    project_id: str,
    session_id: str,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    session = LabSession.resume(project_id=project_id, session_id=session_id, runtime_root=runtime_root)
    receipt = session.close()
    return {"project_id": project_id, "session_id": session_id, "receipt": receipt}


def run_lab_project_init(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    return init_project(
        spec_path=payload.get("spec_path") or payload.get("spec"),
        project_id=payload.get("project_id"),
        source=payload.get("source") or ".",
        branch=payload.get("branch"),
        runtime_root=runtime_root,
    )


def run_lab_project_status(project_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    return project_status(project_id, runtime_root=runtime_root)


def run_lab_experiments_list(project_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    return {"project_id": project_id, "experiments": list_experiments(project_id, runtime_root=runtime_root)}
