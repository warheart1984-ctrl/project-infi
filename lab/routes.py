"""Lab Console HTTP routes (v2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from lab.experiment import list_experiments, show_experiment
from lab.forge_bridge import create_lab_patch_plan
from lab.project import ProjectError, init_project, project_status
from lab.session import LabSession, SessionError

router = APIRouter(prefix="/v1/lab", tags=["lab"])


class LabInitRequest(BaseModel):
    project_id: str | None = None
    spec_path: str | None = Field(default=None, alias="spec")
    source: str = "."
    branch: str | None = None
    runtime_root: str | None = None


class LabSessionStartRequest(BaseModel):
    project_id: str
    agent: str = "coding-agent-v1"
    session_id: str | None = None
    runtime_root: str | None = None


class LabToolInvokeRequest(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


class LabPatchPlanRequest(BaseModel):
    goal: str
    paths: list[str] = Field(default_factory=list)


def _runtime_root(value: str | None) -> Path | None:
    return Path(value) if value else None


@router.post("/projects")
def create_lab_project(body: LabInitRequest) -> dict[str, Any]:
    try:
        result = init_project(
            spec_path=body.spec_path,
            project_id=body.project_id,
            source=body.source,
            branch=body.branch,
            runtime_root=_runtime_root(body.runtime_root),
        )
    except ProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/projects/{project_id}/status")
def get_lab_project_status(project_id: str, runtime_root: str | None = None) -> dict[str, Any]:
    try:
        return project_status(project_id, runtime_root=_runtime_root(runtime_root))
    except ProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions")
def start_lab_session(body: LabSessionStartRequest) -> dict[str, Any]:
    try:
        session = LabSession.open(
            project_id=body.project_id,
            agent=body.agent,
            session_id=body.session_id,
            runtime_root=_runtime_root(body.runtime_root),
        )
        return {
            "ok": True,
            "project_id": session.project_id,
            "session_id": session.session_id,
            "tools": session.list_tools(),
        }
    except (ProjectError, SessionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/tools")
def invoke_lab_tool(session_id: str, body: LabToolInvokeRequest, project_id: str) -> dict[str, Any]:
    try:
        session = LabSession.resume(project_id=project_id, session_id=session_id)
        receipt = session.invoke_tool(body.tool, args=body.args)
        return {"ok": True, "receipt": receipt.to_dict() if hasattr(receipt, "to_dict") else receipt}
    except (ProjectError, SessionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/close")
def close_lab_session(session_id: str, project_id: str, status: str = "completed") -> dict[str, Any]:
    try:
        session = LabSession.resume(project_id=project_id, session_id=session_id)
        receipt = session.close(status=status)
        return {"ok": True, "receipt": receipt}
    except (ProjectError, SessionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/experiments")
def get_lab_experiments(project_id: str, runtime_root: str | None = None) -> dict[str, Any]:
    root = _runtime_root(runtime_root)
    return {"project_id": project_id, "experiments": list_experiments(project_id, runtime_root=root)}


@router.get("/projects/{project_id}/experiments/{experiment_id}")
def get_lab_experiment(project_id: str, experiment_id: str, runtime_root: str | None = None) -> dict[str, Any]:
    root = _runtime_root(runtime_root)
    try:
        return show_experiment(project_id, experiment_id, runtime_root=root)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/patch-plan")
def create_lab_patch_plan_route(session_id: str, body: LabPatchPlanRequest, project_id: str) -> dict[str, Any]:
    try:
        session = LabSession.resume(project_id=project_id, session_id=session_id)
        result = create_lab_patch_plan(session, goal=body.goal)
        return {"ok": True, **result}
    except (ProjectError, SessionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
