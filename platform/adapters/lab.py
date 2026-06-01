"""Lab session adapter (minimal governed session open/close)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.project import project_dir
from lab.session import LabSession
from lab.spec import load_lab_spec


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
    spec = load_lab_spec(spec_path)
    session = LabSession.open(project_id=project_id, agent=agent, runtime_root=root)
    with session:
        readme = session.workspace / "README.md"
        if readme.is_file():
            session.invoke_tool("read_file", path="README.md")
    receipt_path = session.session_dir / "LAB_SESSION_RECEIPT.json"
    return {
        "project_id": project_id,
        "session_id": session.session_id,
        "receipt_path": str(receipt_path),
        "artifact_dir": str(session.session_dir),
    }
