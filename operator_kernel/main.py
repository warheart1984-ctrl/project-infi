"""OperatorKernel FastAPI application."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from operator_kernel.agent_loop import (
    continue_task,
    is_task_running,
    request_cancel,
    start_task,
)
from operator_kernel.agent_profiles import list_profiles
from operator_kernel.config import OperatorKernelConfig, load_config
from operator_kernel.contracts import (
    AgentProfile,
    AppendMessageRequest,
    AppendMessageResponse,
    ApplyPatchBody,
    CancelTaskResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    PatchPreviewBody,
    PatchApprovalResponse,
    RejectPatchRequest,
    TaskDetailResponse,
    TaskSummaryBody,
)
from operator_kernel.patch_approval import approve_pending_patch, reject_pending_patch
from operator_kernel.csr import CSR
from operator_kernel.events import TaskEventStore
from operator_kernel.governance_gate import GovernanceGate
from operator_kernel.tools.executor import ToolExecutor
from operator_kernel.tools.patch import apply_unified_diff, preview_patch
from operator_kernel.tools.workspace import WorkspaceTools
from operator_kernel.memory.project_memory import ProjectMemory, _project_id
from operator_kernel.memory.semantic_store import SemanticStore
from operator_kernel.memory.task_context import update_task_summary

CONFIG: OperatorKernelConfig = load_config()
STORE = TaskEventStore(CONFIG.tasks_dir())
GATE = GovernanceGate(CONFIG.resolved_workspace_root(), CONFIG.command_allowlist_id)
EXECUTOR = ToolExecutor(CONFIG.resolved_workspace_root(), GATE)

app = FastAPI(title="Operator Kernel", version="0.1.0")


@app.on_event("startup")
def _constitutional_boot() -> None:
    from governance_gate import require_constitutional_boot

    require_constitutional_boot()


# WebView2 loads UI from file:// (Origin: null). Do not use credentials with null origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CONFIG.cors_origins),
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _workspace_root(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return CONFIG.resolved_workspace_root()


@app.get("/health")
async def health() -> dict[str, Any]:
    lawful_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{CONFIG.lawful_brain_url.rstrip('/')}/health")
            lawful_ok = r.status_code == 200
    except Exception:
        lawful_ok = False
    return {
        "status": "ok",
        "service": "operator_kernel",
        "lawful_brain_url": CONFIG.lawful_brain_url,
        "lawful_brain_reachable": lawful_ok,
        "workspace_root": str(CONFIG.resolved_workspace_root()),
    }


@app.get("/agent/profiles", response_model=list[AgentProfile])
def agent_profiles() -> list[AgentProfile]:
    return list_profiles()


@app.post("/agent/tasks", response_model=CreateTaskResponse)
async def create_task(body: CreateTaskRequest) -> CreateTaskResponse:
    try:
        task_id = start_task(body, CONFIG, STORE, GATE, EXECUTOR)
    except RuntimeError as exc:
        if "AAIS_UNLAWFUL_AGENTS_DISABLED" in str(exc):
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        raise
    return CreateTaskResponse(task_id=task_id, status="queued")


@app.get("/agent/tasks")
def list_tasks() -> dict[str, Any]:
    return {"tasks": STORE.list_tasks()}


@app.get("/agent/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: str) -> TaskDetailResponse:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    meta = STORE.read_meta(task_id)
    events = STORE.read_all_events(task_id)
    return TaskDetailResponse(task_id=task_id, meta=meta, events=events)


@app.post("/agent/tasks/{task_id}/cancel", response_model=CancelTaskResponse)
def cancel_task(task_id: str) -> CancelTaskResponse:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    meta = STORE.read_meta(task_id)
    if meta.get("status") == "cancelled":
        return CancelTaskResponse(task_id=task_id, status="cancelled")
    if meta.get("status") == "awaiting_approval":
        meta["status"] = "cancelled"
        meta.pop("pending_patch", None)
        STORE.write_meta(task_id, meta)
        STORE.append(task_id, "task_cancelled", {"reason": "user"})
        return CancelTaskResponse(task_id=task_id, status="cancelled")
    if meta.get("status") in ("completed", "failed", "rejected"):
        raise HTTPException(status_code=409, detail=f"task already {meta.get('status')}")
    if not request_cancel(task_id):
        raise HTTPException(status_code=409, detail="cancel not accepted")
    meta["status"] = "cancelling"
    STORE.write_meta(task_id, meta)
    return CancelTaskResponse(task_id=task_id, status="cancelling")


@app.post("/agent/tasks/{task_id}/summary")
def set_task_summary(task_id: str, body: TaskSummaryBody) -> dict[str, Any]:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    meta = update_task_summary(STORE, task_id, body.summary)
    return {"task_id": task_id, "summary": meta.get("summary")}


@app.get("/memory/project/recent")
def memory_project_recent() -> dict[str, Any]:
    project_id = _project_id(str(CONFIG.resolved_workspace_root()))
    project = ProjectMemory()
    events = project.recent_events(project_id, limit=30)
    summary = project.summarize_for_prompt(project_id)
    return {"project_id": project_id, "events": events, "summary": summary}


@app.get("/memory/semantic/search")
def memory_semantic_search(q: str = Query(min_length=1)) -> dict[str, Any]:
    project_id = _project_id(str(CONFIG.resolved_workspace_root()))
    store = SemanticStore()
    hits = store.search(project_id, q, top_k=8)
    summary = store.summarize_for_prompt(project_id, q)
    return {"project_id": project_id, "query": q, "hits": hits, "summary": summary}


@app.post("/agent/tasks/{task_id}/message", response_model=AppendMessageResponse)
async def append_message(task_id: str, body: AppendMessageRequest) -> AppendMessageResponse:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    meta = STORE.read_meta(task_id)
    if meta.get("status") == "awaiting_approval":
        raise HTTPException(status_code=409, detail="task awaiting patch approval")
    if is_task_running(task_id):
        raise HTTPException(status_code=409, detail="task already running")
    try:
        continue_task(task_id, body.text, CONFIG, STORE, GATE, EXECUTOR)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AppendMessageResponse(task_id=task_id, status="running")


@app.post("/agent/tasks/{task_id}/approve_patch", response_model=PatchApprovalResponse)
def approve_patch(task_id: str) -> PatchApprovalResponse:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    return approve_pending_patch(task_id, STORE, GATE, CONFIG)


@app.post("/agent/tasks/{task_id}/reject_patch", response_model=PatchApprovalResponse)
def reject_patch(task_id: str, body: RejectPatchRequest | None = None) -> PatchApprovalResponse:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    reason = body.reason if body else ""
    return reject_pending_patch(task_id, STORE, reason=reason)


@app.get("/agent/tasks/{task_id}/events")
async def stream_events(
    task_id: str,
    after: int = Query(default=0, ge=0),
) -> StreamingResponse:
    if not STORE.task_exists(task_id):
        raise HTTPException(status_code=404, detail="task not found")

    async def event_generator():
        last_seq = after
        idle_ticks = 0
        max_idle = 120 if is_task_running(task_id) else 8
        while True:
            events = STORE.read_since(task_id, last_seq)
            if events:
                idle_ticks = 0
                for event in events:
                    payload = event.model_dump()
                    yield f"data: {json.dumps(payload)}\n\n"
                    last_seq = event.seq
            else:
                idle_ticks += 1

            if is_task_running(task_id):
                await asyncio.sleep(0.25)
                continue

            meta = STORE.read_meta(task_id)
            status = meta.get("status", "")
            if status in {"completed", "failed", "cancelled", "awaiting_approval", "rejected"} and idle_ticks >= 2:
                return
            if idle_ticks >= max_idle:
                return
            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # WebView2 file:// UI sends Origin: null; allow SSE without credentialed cookies.
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.get("/workspace/tree")
def workspace_tree(
    root: str | None = None,
    pattern: str = Query(default="**/*"),
) -> dict[str, Any]:
    ws = _workspace_root(root)
    tools = WorkspaceTools(ws, GATE)
    return tools.list_files(pattern)


@app.get("/workspace/file")
def workspace_file(path: str, root: str | None = None) -> dict[str, Any]:
    ws = _workspace_root(root)
    tools = WorkspaceTools(ws, GATE)
    return tools.read_file(path)


@app.get("/workspace/git-status")
def workspace_git_status_route(root: str | None = None) -> dict[str, Any]:
    from operator_kernel.tools.git_tools import git_status

    ws = _workspace_root(root)
    return git_status(ws)


@app.post("/workspace/patch/preview")
def workspace_patch_preview(body: PatchPreviewBody) -> dict[str, Any]:
    return preview_patch(body.path, body.old_content, body.new_content)


@app.post("/workspace/apply_patch")
def workspace_apply_patch(body: ApplyPatchBody) -> dict[str, Any]:
    from operator_kernel.contracts import TaskConstraints

    ws = _workspace_root(body.root)
    constraints = TaskConstraints(read_only=False, allow_shell=False)
    verdict, receipt = GATE.check_tool(
        "write_patch",
        {"path": body.path, "diff": body.diff},
        constraints,
    )
    if verdict.verdict == "deny":
        raise HTTPException(
            status_code=403,
            detail={"verdict": verdict.verdict, "reason": verdict.reason, "receipt": receipt.model_dump()},
        )
    try:
        return apply_unified_diff(ws, body.path, body.diff)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/constitutional/state/{state_id}")
def constitutional_state_get(state_id: str) -> dict[str, Any]:
    """Current constitutional StateObject for an operator task."""
    try:
        state = CSR.get_state(state_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"state not found: {state_id}") from exc
    return json.loads(state.model_dump_json())


@app.get("/constitutional/state/{state_id}/replay")
def constitutional_state_replay(state_id: str) -> dict[str, Any]:
    """CSR replay result for an operator task."""
    try:
        CSR.get_state(state_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"state not found: {state_id}") from exc
    return json.loads(CSR.replay(state_id).model_dump_json())


@app.get("/survivability/dashboard")
def survivability_dashboard() -> dict[str, Any]:
    """Article S / S-2 survivability cockpit (operator kernel standalone)."""
    from src.survivability_dashboard_api import build_survivability_dashboard_payload

    return build_survivability_dashboard_payload(CSR, refresh=False)


@app.post("/survivability/dashboard/refresh")
def survivability_dashboard_refresh() -> dict[str, Any]:
    from src.survivability_dashboard_api import build_survivability_dashboard_payload

    return build_survivability_dashboard_payload(CSR, refresh=True)


def main() -> None:
    import uvicorn

    from governance_gate import require_constitutional_boot
    from runtime_law_spine.runtime_law_spine.startup import ensure_rls_sealed

    ensure_rls_sealed()
    require_constitutional_boot()
    uvicorn.run(
        "operator_kernel.main:app",
        host=CONFIG.host,
        port=CONFIG.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
