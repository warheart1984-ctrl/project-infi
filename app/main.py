"""FastAPI workflow/onboarding shell for AAIS.

This module owns the workflow/onboarding surface and the transition bridge into
the canonical Jarvis runtime. It is a live shell, not a reference prototype,
but `src/api.py` still owns core Jarvis runtime truth and operator semantics.
"""

from __future__ import annotations
import asyncio
import importlib
import json
import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # health will degrade gracefully if missing
from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, Depends, HTTPException, Request, Response as FastAPIResponse, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from app.schemas import (
    ChatRequest, ChatResponse,
    JarvisCompatRequest, JarvisCompatResponse, JarvisMemoryWriteRequest,
    AgentRequest, AgentResponse, AgentStep,
    JobResponse, JobStatusResponse, RagIndexRequest, RagIndexResponse, RagQueryRequest, RagQueryResponse,
    WorkflowApprovalActionRequest, WorkflowDraftRequest, WorkflowRunRequest,
    WorkflowSaveRequest, WorkflowSimulateRequest, OnboardingCompleteRequest,
)
from app.agentic import run_tool_loop, build_messages
from app.workflow import run_goal_workflow
from app.workflow_runtime import build_draft_workflow, simulate_workflow
from app.workflow_recovery import sweep_workflow_runs
from app.workflow_templates import WORKFLOW_TEMPLATES, get_workflow_template
from app.workflow_validation import (
    WorkflowValidationError,
    build_workflow_config_from_graph,
    validate_workflow_config,
)
from app.config import (
    STATIC_DIR,
    REDIS_URL,
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    OPENAI_MAIN_MODEL,
    OPENAI_FAST_MODEL,
    APP_BEARER_TOKEN,
    APP_CORS_ORIGINS,
)
from app.llm import stream_chat, summarize_messages, answer_with_excerpts
from app.memory import store_memory
from app.db import (
    init_db, save_message, load_recent_messages, export_session, load_all_messages,
    get_job, create_job, log_event, add_job_event, get_job_events_since, update_job,
    get_active_workflow_run,
    complete_onboarding, create_workflow, create_workflow_run,
    get_latest_workflow, get_onboarding_state, get_workflow,
    get_workflow_approval, get_workflow_run, list_pending_workflow_approvals,
    list_workflow_runs, list_workflows, now_iso, update_workflow, update_workflow_approval, update_workflow_run,
)
from app.auth import require_token, check_sse_token, check_ws_token
from app.tasks import run_agent_job, run_workflow_job
from app.rag import index_project, query_project
from src.cisiv import normalize_cisiv_stage
from src.project_infi_law import PROJECT_INFI_CONTRACT_VERSION, ProjectInfiLaw

logger = logging.getLogger(__name__)
# The workflow shell stays on its own mount path and bridges into the canonical
# Flask operator runtime instead of redefining Jarvis authority locally.
LEGACY_API_MOUNT_PATH = "/legacy_api"
PROJECT_INFI_SHELL_SURFACE = "workflow_shell"
PROJECT_INFI_SHELL_ACTOR_ID = "workflow_shell"
PROJECT_INFI_SHELL_ACTOR_ROLE = "system"
EXTERNAL_SUGGESTION_DETAIL_KEYS = (
    "external_suggestion",
    "external_suggestion_usage",
    "law_filter_applied",
    "admitted_external_form",
)


def _normalize_app_shell_base_path(value: str | None) -> str:
    normalized = str(value or "/app").strip()
    if not normalized or normalized == "/":
        return "/app"
    return "/" + normalized.strip("/")


APP_SHELL_BASE_PATH = _normalize_app_shell_base_path(os.getenv("AAIS_APP_BASE"))


class LegacyFlaskApiBridge:
    def __init__(self) -> None:
        self.loaded = False
        self.load_error: str | None = None
        self._app = None

    def _load_app(self):
        if self._app is not None:
            return self._app
        if self.load_error is not None:
            raise RuntimeError(self.load_error)

        try:
            import importlib
            from pathlib import Path

            # Defense-in-depth: ensure project root is on path for src.* / app.* imports.
            # This helps when people run uvicorn directly instead of `python -m aais start`.
            try:
                here = Path(__file__).resolve()
                # Walk up until we see both app/ and src/ (or pyproject.toml)
                root = here
                for _ in range(6):
                    if (root / "app" / "main.py").exists() and (root / "src" / "api.py").exists():
                        root_str = str(root)
                        if root_str not in sys.path:
                            sys.path.insert(0, root_str)
                        break
                    root = root.parent
            except Exception:
                pass

            importlib.import_module("src.operator_api_routes")
            from src.api import app as legacy_flask_app, bootstrap_ai_runtime
        except Exception as exc:  # pragma: no cover - only exercised in misconfigured envs
            self.load_error = str(exc)
            logger.warning("Legacy Flask API could not be loaded: %s", exc)
            raise

        bootstrap_ai_runtime(reason="legacy_bridge_load")
        self._app = legacy_flask_app
        self.loaded = True
        return self._app

    def __call__(self, environ, start_response):
        app = self._load_app()
        return app(environ, start_response)


legacy_api_bridge = LegacyFlaskApiBridge()
legacy_api_mounted = True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    try:
        from src.firetiger_otel import init_firetiger_otel

        flask_app = None
        try:
            flask_app = legacy_api_bridge._load_app()
        except Exception as exc:
            model_mode = os.getenv("AAIS_MODEL_MODE", "").strip().lower()
            allow_fallback = model_mode in ("mock", "") or os.getenv("AAIS_ALLOW_BRIDGE_FALLBACK", "0").lower() in ("1", "true", "yes")
            if not allow_fallback:
                # Stricter startup for MVP: surface mis-wiring immediately instead of silent degraded
                logger.error("Legacy Jarvis bridge failed to load in strict mode (preset=%s): %s", model_mode or "default", exc)
                raise RuntimeError(f"Legacy bridge required but failed to load: {exc}") from exc
            flask_app = None
            logger.warning("Legacy Jarvis bridge load failed (allowed fallback for mock/default): %s", exc)
        if init_firetiger_otel(
            service_name=os.getenv("OTEL_SERVICE_NAME", "aais-workflow-shell"),
            fastapi_app=_app,
            flask_app=flask_app,
        ):
            logger.info("Firetiger OpenTelemetry export enabled")
    except Exception as exc:
        logger.warning("Firetiger OpenTelemetry bootstrap skipped: %s", exc)
    try:
        from src.governance_organs import Alt4Runtime

        Alt4Runtime.boot_validate()
    except Exception as exc:
        if os.getenv("AAIS_GENOME_BOOT", "fail").strip().lower() not in {
            "warn",
            "warning",
            "skip",
        }:
            raise
        logger.warning("Alt-4 genome boot validation (workflow shell): %s", exc)
    yield


app = FastAPI(title="AAIS Workflow Shell", version="11.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=APP_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount(LEGACY_API_MOUNT_PATH, WSGIMiddleware(legacy_api_bridge))


def _static_file_path(relative_path: str) -> Path | None:
    requested_path = (STATIC_DIR / relative_path).resolve()
    static_root = STATIC_DIR.resolve()

    try:
        requested_path.relative_to(static_root)
    except ValueError:
        return None

    if requested_path.is_file():
        return requested_path
    return None


def _has_modern_frontend_bundle() -> bool:
    return (STATIC_DIR / "index.html").exists() and (STATIC_DIR / "assets").is_dir()


def _serve_frontend_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def _probe_contractor(name: str, port: int, path: str = "/health") -> dict:
    """Lightweight probe for optional contractors. Short timeout so health stays snappy."""
    url = f"http://127.0.0.1:{port}{path}"
    if requests is None:
        return {"name": name, "url": url, "reachable": False, "error": "requests not installed"}
    try:
        r = requests.get(url, timeout=1.0)
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        out = {
            "name": name,
            "url": url,
            "reachable": r.status_code < 500,
            "status": data.get("status"),
        }
        if "forge_eval_reachable" in data:
            out["forge_eval_reachable"] = data["forge_eval_reachable"]
        return out
    except Exception as exc:
        return {"name": name, "url": url, "reachable": False, "error": str(exc)[:120]}


def _build_operator_health_payload() -> dict:
    legacy_ok = legacy_api_bridge.loaded and not legacy_api_bridge.load_error
    model_mode = os.getenv("AAIS_MODEL_MODE", "").strip().lower()
    strict_startup = model_mode not in ("mock", "") and os.getenv("AAIS_ALLOW_STARTUP_FALLBACK", "1").lower() not in ("1", "true", "yes", "on")
    payload = {
        "status": "healthy" if legacy_ok else "degraded",
        "service": "AAIS Workflow Shell",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "legacy_api_mount_path": LEGACY_API_MOUNT_PATH,
        "legacy_api_mounted": legacy_api_mounted,
        "legacy_api_loaded": legacy_api_bridge.loaded,
        "legacy_api_mount_error": legacy_api_bridge.load_error,
        "requested_model_mode": None,
        "active_model_mode": None,
        "ai_status": "not_initialized",
        "ai_init_error": None,
        "ai_bootstrap_status": "not_initialized",
        "ai_bootstrap_reason": None,
        "ai_fallback_active": False,
        "mock_mode_active": model_mode == "mock",
        "strict_startup": strict_startup,
        "contractors": [
            _probe_contractor("forge", 6060),
            _probe_contractor("forge_eval", 6061),
            _probe_contractor("evolve", 6062),
        ],
    }

    try:
        legacy_api = importlib.import_module("src.api")
        bootstrap = getattr(legacy_api, "bootstrap_ai_runtime", None)
        if callable(bootstrap):
            bootstrap(reason="canonical_health")
        runtime_status = legacy_api._build_ai_runtime_status()
        # Only pull lightweight ai status for the compact health.
        # Heavy snapshots (system_guard, dreamspace, full law traces)
        # live in /health/details to keep the happy-path response small.
        payload.update(
            {
                k: runtime_status.get(k)
                for k in (
                    "requested_model_mode",
                    "active_model_mode",
                    "ai_status",
                    "ai_init_error",
                    "ai_bootstrap_status",
                    "ai_bootstrap_reason",
                    "ai_fallback_active",
                    "mock_mode_active",
                )
            }
        )
        # Ensure overall status reflects legacy bridge health
        if legacy_ok:
            payload["status"] = "healthy"
            payload["service"] = payload.get("service") or "AAIS"
    except Exception as exc:  # pragma: no cover - only exercised when the bridge env is broken
        logger.warning("Legacy runtime health unavailable: %s", exc)
        payload["ai_init_error"] = str(exc)
        payload["legacy_api_mount_error"] = payload["legacy_api_mount_error"] or str(exc)

    return payload


def _build_project_infi_shell_envelope(
    *,
    action_id: str,
    target: str,
    cisiv_stage: str | None,
    summary: str,
    action_status: str = "completed",
    run_id: str | None = None,
    details: dict | None = None,
    session_id: str | None = None,
    surface: str = PROJECT_INFI_SHELL_SURFACE,
) -> dict:
    law = ProjectInfiLaw()
    normalized_action_id = str(action_id or "").strip() or "workflow_shell_action"
    normalized_target = str(target or normalized_action_id).strip() or normalized_action_id
    contract, ul_snapshot, _ = law.require_contract(
        surface=surface,
        action_id=normalized_action_id,
        actor_id=PROJECT_INFI_SHELL_ACTOR_ID,
        actor_role=PROJECT_INFI_SHELL_ACTOR_ROLE,
        session_id=session_id,
        target=normalized_target,
        repo_change=False,
        verification_plan=None,
        run_id=run_id,
        cisiv_stage=cisiv_stage,
        details=dict(details or {}),
    )
    law_enforcement, law_event_log = law.finalize_runtime_action(
        contract,
        action_status=action_status,
        summary=summary,
        actor_id=PROJECT_INFI_SHELL_ACTOR_ID,
        actor_role=PROJECT_INFI_SHELL_ACTOR_ROLE,
        run_id=run_id,
        details=dict(details or {}),
    )
    return {
        "law_enforcement": law_enforcement,
        "ul_snapshot": ul_snapshot,
        "law_event_log": law_event_log,
    }


def _extract_external_suggestion_details(*sources) -> dict:
    details: dict = {}
    for source in sources:
        if source is None:
            continue
        if hasattr(source, "model_dump"):
            payload = source.model_dump()
        elif isinstance(source, dict):
            payload = source
        else:
            continue
        for key in EXTERNAL_SUGGESTION_DETAIL_KEYS:
            value = payload.get(key)
            if value in (None, "", [], {}):
                continue
            if key == "law_filter_applied" and value is not True:
                continue
            details[key] = value
    return details


def _merge_project_law_details(base: dict | None = None, *sources) -> dict:
    details = dict(base or {})
    details.update(_extract_external_suggestion_details(*sources))
    return details


def _ensure_project_law_admission(
    *,
    action_id: str,
    target: str,
    cisiv_stage: str | None,
    summary: str,
    action_status: str = "completed",
    run_id: str | None = None,
    details: dict | None = None,
    session_id: str | None = None,
    surface: str = PROJECT_INFI_SHELL_SURFACE,
) -> None:
    try:
        _build_project_infi_shell_envelope(
            action_id=action_id,
            target=target,
            cisiv_stage=cisiv_stage,
            summary=summary,
            action_status=action_status,
            run_id=run_id,
            details=details,
            session_id=session_id,
            surface=surface,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _govern_project_wide_payload(
    payload: dict,
    *,
    action_id: str,
    target: str,
    cisiv_stage: str | None,
    summary: str,
    action_status: str = "completed",
    run_id: str | None = None,
    details: dict | None = None,
    session_id: str | None = None,
    surface: str = PROJECT_INFI_SHELL_SURFACE,
) -> dict:
    envelope = _build_project_infi_shell_envelope(
        action_id=action_id,
        target=target,
        cisiv_stage=cisiv_stage,
        summary=summary,
        action_status=action_status,
        run_id=run_id,
        details=details,
        session_id=session_id,
        surface=surface,
    )
    return {
        **dict(payload or {}),
        **envelope,
    }


def _enqueue_workflow_recovery(workflow_run_id: str, workflow_id: str) -> None:
    run_workflow_job.delay(workflow_run_id, workflow_id, None, True)


def maybe_sweep_workflow_runs() -> None:
    try:
        sweep_workflow_runs(_enqueue_workflow_recovery)
    except Exception as exc:
        log_event("workflow_sweeper_failed", {"error": str(exc)})


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    return ""


def _authorize_workflow_webhook(request: Request, workflow: dict) -> None:
    trigger = (workflow.get("config") or {}).get("trigger") or {}
    trigger_config = trigger.get("config") or {}
    secret = str(trigger_config.get("secret") or "").strip()
    if secret:
        provided_secret = (
            request.headers.get("x-workflow-secret", "").strip()
            or request.query_params.get("secret", "").strip()
        )
        if provided_secret != secret:
            raise HTTPException(status_code=401, detail="Invalid workflow webhook secret")
        return

    if APP_BEARER_TOKEN and _extract_bearer_token(request) != APP_BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _queue_workflow_run_record(
    workflow: dict,
    trigger_data: dict | None,
    queued_message: str,
    source: str,
    cisiv_stage: str | None = None,
) -> dict:
    try:
        validate_workflow_config(workflow.get("config") or {})
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    active_run = get_active_workflow_run(workflow["id"])
    if active_run:
        raise HTTPException(
            status_code=409,
            detail=f"Workflow already has an active run ({active_run['status']}).",
        )

    normalized_trigger_data = trigger_data if isinstance(trigger_data, dict) else {}
    normalized_trigger_data = {
        **normalized_trigger_data,
        "source": normalized_trigger_data.get("source") or source,
    }
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="implementation")
    normalized_trigger_data["cisiv_stage"] = normalize_cisiv_stage(
        normalized_trigger_data.get("cisiv_stage"),
        default=normalized_cisiv_stage,
    )
    queue_law_details = _merge_project_law_details(
        {
            "workflow_id": workflow["id"],
            "source": source,
            "trigger_keys": sorted(normalized_trigger_data.keys()),
        },
        normalized_trigger_data,
    )
    _ensure_project_law_admission(
        action_id="workflow_queue",
        target=workflow["id"],
        cisiv_stage=normalized_cisiv_stage,
        summary=queued_message,
        action_status="queued",
        details=queue_law_details,
    )
    queue_output = {
        "message": queued_message,
        "queuedAt": now_iso(),
        "triggerData": normalized_trigger_data,
        "source": source,
        "cisiv_stage": normalized_cisiv_stage,
    }
    workflow_run = create_workflow_run(
        workflow_id=workflow["id"],
        status="queued",
        output=queue_output,
        cisiv_stage=normalized_cisiv_stage,
    )
    governed_queue_output = _govern_project_wide_payload(
        queue_output,
        action_id="workflow_queue",
        target=workflow["id"],
        cisiv_stage=normalized_cisiv_stage,
        summary=queued_message,
        action_status="queued",
        run_id=workflow_run["id"],
        details={
            **queue_law_details,
            "workflow_run_id": workflow_run["id"],
        },
    )
    update_workflow_run(workflow_run["id"], output=governed_queue_output)
    try:
        run_workflow_job.delay(workflow_run["id"], workflow["id"], normalized_trigger_data, False)
    except Exception as exc:
        failed_output = _govern_project_wide_payload(
            {
                "message": "Workflow queue failed",
                "error": str(exc),
                "triggerData": normalized_trigger_data,
                "source": source,
                "cisiv_stage": normalized_cisiv_stage,
            },
            action_id="workflow_queue",
            target=workflow["id"],
            cisiv_stage=normalized_cisiv_stage,
            summary="Workflow queue failed before execution could begin.",
            action_status="failed",
            run_id=workflow_run["id"],
            details={
                **queue_law_details,
                "workflow_run_id": workflow_run["id"],
                "error": str(exc),
            },
        )
        update_workflow_run(
            workflow_run["id"],
            status="failed",
            output=failed_output,
        )
        log_event("workflow_queue_failed", {"workflow_run_id": workflow_run["id"], "error": str(exc)})
        raise HTTPException(status_code=503, detail="Could not queue workflow run") from exc

    return _govern_project_wide_payload(
        {
            "ok": True,
            "queued": True,
            "workflow_run_id": workflow_run["id"],
            "workflow_id": workflow["id"],
            "status": "queued",
            "source": source,
            "cisiv_stage": normalized_cisiv_stage,
        },
        action_id="workflow_queue",
        target=workflow["id"],
        cisiv_stage=normalized_cisiv_stage,
        summary=queued_message,
        action_status="queued",
        run_id=workflow_run["id"],
        details={
            **queue_law_details,
            "workflow_run_id": workflow_run["id"],
        },
    )


def _forward_legacy_jarvis_request(payload: dict) -> tuple[int, dict]:
    """Send one shell-owned Jarvis request through the shared runtime service layer."""
    try:
        from src.jarvis_runtime_service import invoke_jarvis_compat

        return invoke_jarvis_compat(payload)
    except Exception as exc:  # pragma: no cover - only exercised when the legacy runtime is broken
        raise HTTPException(status_code=503, detail=f"Jarvis runtime unavailable: {exc}") from exc


def _forward_legacy_runtime_json_request(path: str, payload: dict) -> tuple[int, dict]:
    """Forward one shell-owned JSON request through the shared runtime service layer."""
    try:
        from src.jarvis_runtime_service import invoke_legacy_json_post

        return invoke_legacy_json_post(path, payload)
    except Exception as exc:  # pragma: no cover - only exercised when the legacy runtime is broken
        raise HTTPException(status_code=503, detail=f"Jarvis runtime unavailable: {exc}") from exc

@app.get("/")
def index():
    if _has_modern_frontend_bundle():
        return RedirectResponse(APP_SHELL_BASE_PATH)
    return _serve_frontend_index()

@app.get("/health")
def health(request: Request):
    """Compact, operator-friendly health for MVP happy path.

    Returns a small, fast summary. The full governed law/UL trace
    and internal snapshots (dreamspace, system_guard, etc.) live in
    /health/details or ?full=1.
    """
    payload = _build_operator_health_payload()

    # Compact summary for daily use (MVP-friendly, low noise)
    compact = {
        "status": payload.get("status"),
        "service": "AAIS",
        "legacy_api_loaded": bool(payload.get("legacy_api_loaded")),
        "active_model_mode": payload.get("active_model_mode"),
        "mock_mode_active": payload.get("mock_mode_active"),
        "strict_startup": payload.get("strict_startup"),
        "contractors": payload.get("contractors", []),
    }
    # Only include ai_fallback_active in compact if it's a real fallback (not explicit mock)
    if payload.get("ai_fallback_active") and not payload.get("mock_mode_active"):
        compact["ai_fallback_active"] = True

    if request.query_params.get("full"):
        # Opt-in to the full governed view
        return _govern_project_wide_payload(
            payload,
            action_id="workflow_shell_health_snapshot",
            target="operator_health",
            cisiv_stage="verification",
            summary="Workflow shell health snapshot served (full).",
            action_status="completed" if payload.get("status") == "healthy" else "degraded",
        )

    return compact

@app.get("/health/details")
def health_details():
    """Rich, fully governed health details (the previous /health behavior).

    Includes law enforcement, UL snapshots, dreamspace, system_guard, etc.
    Use this when you need the full trace for debugging or compliance.
    """
    base = {
        "status": "ok",
        "redis_url": REDIS_URL,
        "celery_broker_url": CELERY_BROKER_URL,
        "celery_result_backend": CELERY_RESULT_BACKEND,
        "main_model": OPENAI_MAIN_MODEL,
        "fast_model": OPENAI_FAST_MODEL,
        "legacy_api_mount_path": LEGACY_API_MOUNT_PATH,
        "legacy_api_mounted": legacy_api_mounted,
        "legacy_api_loaded": legacy_api_bridge.loaded,
        "legacy_api_mount_error": legacy_api_bridge.load_error,
    }

    # Pull the heavy internal snapshots that used to bloat the top-level health
    try:
        legacy_api = importlib.import_module("src.api")
        bootstrap = getattr(legacy_api, "bootstrap_ai_runtime", None)
        if callable(bootstrap):
            bootstrap(reason="health_details")
        runtime_status = legacy_api._build_ai_runtime_status()
        base.update(runtime_status)
        base.update({
            "system_guard": legacy_api.system_guard.snapshot(limit_events=8),
            "dreamspace": legacy_api.dreamspace.snapshot(limit_dreams=4),
        })
    except Exception as exc:
        base["internal_snapshot_error"] = str(exc)[:200]

    return _govern_project_wide_payload(
        base,
        action_id="workflow_shell_health_details",
        target="operator_health_details",
        cisiv_stage="verification",
        summary="Workflow shell health details served.",
        details={"contract_version": PROJECT_INFI_CONTRACT_VERSION},
    )

@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_token)], include_in_schema=False)
def chat(req: ChatRequest):
    history = load_recent_messages(req.session_id, limit=20)
    response, used_tool, tool_result, cache_hit, route = run_tool_loop(req.message, history, session_id=req.session_id)
    save_message(req.session_id, "user", req.message)
    save_message(req.session_id, "assistant", response)

    all_messages = load_all_messages(req.session_id)
    if len(all_messages) and len(all_messages) % 12 == 0:
        summary = summarize_messages([{"role": m["role"], "content": m["content"]} for m in all_messages[-20:]])
        if summary:
            store_memory(f"Conversation summary: {summary}", session_id=req.session_id)

    return ChatResponse(
        response=response,
        used_tool=used_tool,
        tool_result=tool_result,
        session_id=req.session_id,
        cache_hit=cache_hit,
        route=route,
    )


@app.post("/api/jarvis", response_model=JarvisCompatResponse)
def jarvis_chat(req: JarvisCompatRequest, response: FastAPIResponse):
    status_code, payload = _forward_legacy_jarvis_request(req.model_dump())
    response.status_code = status_code
    return JarvisCompatResponse(**payload)


@app.post("/api/memory/write")
def write_memory(req: JarvisMemoryWriteRequest, response: FastAPIResponse):
    status_code, payload = _forward_legacy_runtime_json_request("/api/jarvis/memory", req.model_dump())
    response.status_code = status_code
    return payload


@app.post("/chat/stream", dependencies=[Depends(require_token)], include_in_schema=False)
def chat_stream(req: ChatRequest):
    history = load_recent_messages(req.session_id, limit=12)
    messages = build_messages(req.message, history, req.session_id)

    async def event_generator():
        collected = ""
        try:
            for chunk in stream_chat(messages):
                collected += chunk
                yield chunk
                await asyncio.sleep(0)
        finally:
            if collected.strip():
                save_message(req.session_id, "user", req.message)
                save_message(req.session_id, "assistant", collected)
                store_memory(f"User: {req.message}\nAssistant: {collected}", session_id=req.session_id)
                log_event("stream_chat_response", {"session_id": req.session_id, "response": collected[:1000]})

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.websocket("/ws/chat/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str):
    try:
        await check_ws_token(websocket)
    except RuntimeError:
        return
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            history = load_recent_messages(session_id, limit=12)
            messages = build_messages(text, history, session_id)
            collected = ""
            for chunk in stream_chat(messages):
                collected += chunk
                await websocket.send_text(chunk)
                await asyncio.sleep(0)
            if collected.strip():
                save_message(session_id, "user", text)
                save_message(session_id, "assistant", collected)
                store_memory(f"User: {text}\nAssistant: {collected}", session_id=session_id)
                log_event("ws_chat_response", {"session_id": session_id, "response": collected[:1000]})
            await websocket.send_text("\n[END]")
    except WebSocketDisconnect:
        pass

@app.post("/agent/run", response_model=AgentResponse, dependencies=[Depends(require_token)])
def run_agent(req: AgentRequest):
    plan, steps, final_response = run_goal_workflow(req.goal, session_id=req.session_id)
    return AgentResponse(
        plan=plan,
        steps=[AgentStep(**s) for s in steps],
        final_response=final_response,
        session_id=req.session_id,
    )

@app.post("/jobs/agent", response_model=JobResponse, dependencies=[Depends(require_token)])
def start_agent_job(req: AgentRequest):
    job_id = str(uuid.uuid4())
    create_job(job_id, req.session_id, req.goal)
    add_job_event(job_id, "queued", {"goal": req.goal, "session_id": req.session_id})
    run_agent_job.delay(job_id, req.goal, req.session_id)
    return JobResponse(job_id=job_id, status="queued")

@app.post("/jobs/{job_id}/cancel", dependencies=[Depends(require_token)])
def cancel_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] in {"completed", "failed"}:
        return {"job_id": job_id, "status": job["status"], "message": "Job already finished"}
    update_job(job_id, "cancelled")
    add_job_event(job_id, "cancelled", {"message": "Marked cancelled in app state"})
    return {"job_id": job_id, "status": "cancelled"}

@app.get("/jobs/{job_id}", response_model=JobStatusResponse, dependencies=[Depends(require_token)])
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job["job_id"], status=job["status"], result=job["result"], error=job["error"])

@app.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str, request: Request):
    check_sse_token(request)
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def generator():
        last_id = 0
        while True:
            if await request.is_disconnected():
                break

            events = get_job_events_since(job_id, last_id)
            for event in events:
                last_id = event["id"]
                payload = {
                    "id": event["id"],
                    "event_type": event["event_type"],
                    "payload": event["payload"],
                    "created_at": event["created_at"],
                }
                yield f"data: {json.dumps(payload)}\n\n"

            job_now = get_job(job_id)
            if job_now and job_now["status"] in {"completed", "failed", "cancelled"}:
                final_events = get_job_events_since(job_id, last_id)
                for event in final_events:
                    last_id = event["id"]
                    payload = {
                        "id": event["id"],
                        "event_type": event["event_type"],
                        "payload": event["payload"],
                        "created_at": event["created_at"],
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(generator(), media_type="text/event-stream")

@app.post("/rag/index", response_model=RagIndexResponse, dependencies=[Depends(require_token)])
def rag_index(req: RagIndexRequest):
    indexed_files, indexed_chunks = index_project(req.path)
    return RagIndexResponse(indexed_files=indexed_files, indexed_chunks=indexed_chunks)

@app.post("/rag/query", response_model=RagQueryResponse, dependencies=[Depends(require_token)])
def rag_query(req: RagQueryRequest):
    chunks = query_project(req.question, n_results=4)
    answer = answer_with_excerpts(req.question, chunks)
    store_memory(f"RAG question: {req.question}\nAnswer: {answer}", session_id=req.session_id)
    return RagQueryResponse(answer=answer, chunks_used=chunks)

@app.get("/sessions/{session_id}/export", dependencies=[Depends(require_token)])
def export_session_history(session_id: str):
    return export_session(session_id)

@app.get("/sessions/{session_id}/summary", dependencies=[Depends(require_token)])
def session_summary(session_id: str):
    history = load_all_messages(session_id)
    compact = [{"role": m["role"], "content": m["content"]} for m in history[-30:]]
    return {"session_id": session_id, "summary": summarize_messages(compact) if compact else ""}


@app.get("/workflows", dependencies=[Depends(require_token)])
def workflows(request: Request):
    latest = request.query_params.get("latest", "").lower() == "true"
    workflow_id = request.query_params.get("workflow_id", "")

    if workflow_id:
        workflow = get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return _govern_project_wide_payload(
            {"workflow": workflow},
            action_id="workflow_read",
            target=workflow_id,
            cisiv_stage=(workflow or {}).get("cisiv_stage"),
            summary="Workflow detail served.",
            details={"workflow_id": workflow_id},
        )

    if latest:
        workflow = get_latest_workflow()
        return _govern_project_wide_payload(
            {"workflow": workflow},
            action_id="workflow_latest_read",
            target=(workflow or {}).get("id") or "latest_workflow",
            cisiv_stage=(workflow or {}).get("cisiv_stage"),
            summary="Latest workflow served.",
            details={"workflow_id": (workflow or {}).get("id")},
        )

    workflows_payload = list_workflows()
    return _govern_project_wide_payload(
        {"workflows": workflows_payload},
        action_id="workflow_catalog_read",
        target="workflow_catalog",
        cisiv_stage="verification",
        summary="Workflow catalog served.",
        details={"workflow_count": len(workflows_payload)},
    )


@app.post("/workflows", dependencies=[Depends(require_token)])
def create_workflow_route(req: WorkflowSaveRequest):
    create_law_details = _merge_project_law_details(
        {
            "workflow_name": req.name,
        },
        req,
    )
    _ensure_project_law_admission(
        action_id="workflow_create",
        target=req.name,
        cisiv_stage=req.cisiv_stage or "structure",
        summary="Workflow creation request admitted.",
        details=create_law_details,
    )
    try:
        normalized_config = build_workflow_config_from_graph(req.name, req.nodes, req.edges)
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workflow = create_workflow(
        name=req.name,
        nodes=req.nodes,
        edges=normalized_config["edges"],
        config=normalized_config,
        active=True,
        cisiv_stage=req.cisiv_stage,
    )
    log_event(
        "workflow_created",
        {"workflow_id": workflow["id"], "name": workflow["name"], "cisiv_stage": workflow["cisiv_stage"]},
    )
    return _govern_project_wide_payload(
        {"workflow": workflow},
        action_id="workflow_create",
        target=workflow["id"],
        cisiv_stage=workflow["cisiv_stage"],
        summary=f"Workflow {workflow['name']} created.",
        details={
            **create_law_details,
            "workflow_id": workflow["id"],
            "workflow_name": workflow["name"],
        },
    )


@app.put("/workflows", dependencies=[Depends(require_token)])
def update_workflow_route(req: WorkflowSaveRequest):
    if not req.id:
        raise HTTPException(status_code=400, detail="Missing workflow id")
    update_law_details = _merge_project_law_details(
        {
            "workflow_id": req.id,
            "workflow_name": req.name,
        },
        req,
    )
    _ensure_project_law_admission(
        action_id="workflow_update",
        target=req.id,
        cisiv_stage=req.cisiv_stage or "structure",
        summary="Workflow update request admitted.",
        details=update_law_details,
    )

    workflow = get_workflow(req.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        normalized_config = build_workflow_config_from_graph(req.name, req.nodes, req.edges)
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated = update_workflow(
        workflow_id=req.id,
        name=req.name,
        nodes=req.nodes,
        edges=normalized_config["edges"],
        config=normalized_config,
        cisiv_stage=req.cisiv_stage or workflow.get("cisiv_stage"),
    )
    log_event(
        "workflow_updated",
        {
            "workflow_id": req.id,
            "name": req.name,
            "cisiv_stage": (updated or {}).get("cisiv_stage") or workflow.get("cisiv_stage"),
        },
    )
    return _govern_project_wide_payload(
        {"workflow": updated},
        action_id="workflow_update",
        target=(updated or {}).get("id") or req.id,
        cisiv_stage=(updated or {}).get("cisiv_stage") or workflow.get("cisiv_stage"),
        summary=f"Workflow {req.name} updated.",
        details=update_law_details,
    )


@app.post("/workflows/generate", dependencies=[Depends(require_token)])
def generate_workflow_route(req: WorkflowDraftRequest):
    generate_law_details = _merge_project_law_details(
        {
            "workflow_name": req.name,
        },
        req,
    )
    _ensure_project_law_admission(
        action_id="workflow_generate",
        target=req.name or "draft_workflow",
        cisiv_stage=req.cisiv_stage or "concept",
        summary="Workflow generation request admitted.",
        details=generate_law_details,
    )
    workflow = build_draft_workflow(req.prompt, req.name, req.cisiv_stage)
    return _govern_project_wide_payload(
        {"workflow": workflow},
        action_id="workflow_generate",
        target=(workflow or {}).get("name") or "draft_workflow",
        cisiv_stage=(workflow or {}).get("cisiv_stage"),
        summary="Draft workflow generated.",
        details={
            **generate_law_details,
            "workflow_name": (workflow or {}).get("name"),
        },
    )


@app.post("/workflows/simulate", dependencies=[Depends(require_token)])
def simulate_workflow_route(req: WorkflowSimulateRequest):
    simulate_law_details = _merge_project_law_details(
        {
            "workflow_id": req.id,
        },
        req,
    )
    _ensure_project_law_admission(
        action_id="workflow_simulate",
        target=req.id or "simulation_preview",
        cisiv_stage=req.cisiv_stage or "verification",
        summary="Workflow simulation request admitted.",
        action_status="simulated",
        details=simulate_law_details,
    )
    try:
        normalized_config = validate_workflow_config(req.workflow.model_dump())
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    simulation_cisiv_stage = normalize_cisiv_stage(req.cisiv_stage, default="verification")
    result = simulate_workflow(normalized_config, simulation_cisiv_stage)
    saved_run = None

    if req.id:
        workflow = get_workflow(req.id)
        if workflow:
            saved_run = create_workflow_run(req.id, "simulated", result, cisiv_stage=simulation_cisiv_stage)
            governed_simulation_output = _govern_project_wide_payload(
                result,
                action_id="workflow_simulate",
                target=req.id,
                cisiv_stage=simulation_cisiv_stage,
                summary="Workflow simulation recorded.",
                action_status="simulated",
                run_id=saved_run["id"],
                details={
                    **simulate_law_details,
                    "workflow_id": req.id,
                    "workflow_run_id": saved_run["id"],
                },
            )
            update_workflow_run(saved_run["id"], output=governed_simulation_output)

    return _govern_project_wide_payload(
        {
            **result,
            "workflow_run_id": saved_run["id"] if saved_run else None,
        },
        action_id="workflow_simulate",
        target=req.id or "simulation_preview",
        cisiv_stage=simulation_cisiv_stage,
        summary="Workflow simulation completed.",
        action_status="simulated",
        run_id=saved_run["id"] if saved_run else None,
        details={
            **simulate_law_details,
            "workflow_id": req.id,
            "workflow_run_id": saved_run["id"] if saved_run else None,
        },
    )


@app.post("/workflows/run", dependencies=[Depends(require_token)])
def run_workflow_route(req: WorkflowRunRequest):
    maybe_sweep_workflow_runs()
    workflow = get_workflow(req.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return _queue_workflow_run_record(
        workflow,
        req.trigger_data or {"text": "Manual queued run", "source": "builder"},
        "Workflow queued",
        "builder",
        req.cisiv_stage or "implementation",
    )


@app.post("/integrations/webhooks/{workflow_id}", status_code=202)
async def workflow_webhook_trigger(workflow_id: str, request: Request):
    maybe_sweep_workflow_runs()
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        normalized_config = validate_workflow_config(workflow.get("config") or {})
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    trigger = normalized_config.get("trigger") or {}
    if trigger.get("type") != "webhook.received":
        raise HTTPException(status_code=409, detail="Workflow is not configured for webhook triggers")

    _authorize_workflow_webhook(request, workflow)

    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Webhook payload must be valid JSON") from exc

    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        payload = {"payload": payload}

    trigger_data = {
        **payload,
        "source": request.headers.get("x-webhook-source") or "webhook",
        "receivedAt": now_iso(),
        "workflowId": workflow_id,
    }
    log_event(
        "workflow_webhook_received",
        {"workflow_id": workflow_id, "trigger_data_keys": sorted(trigger_data.keys())},
    )
    return _queue_workflow_run_record(
        workflow,
        trigger_data,
        "Workflow queued from webhook",
        "webhook",
        "implementation",
    )


@app.get("/workflows/runs", dependencies=[Depends(require_token)])
def workflow_runs():
    maybe_sweep_workflow_runs()
    runs = list_workflow_runs()
    return _govern_project_wide_payload(
        {"runs": runs},
        action_id="workflow_run_list",
        target="workflow_runs",
        cisiv_stage="verification",
        summary="Workflow run list served.",
        details={"run_count": len(runs)},
    )


@app.get("/workflows/runs/{workflow_run_id}", dependencies=[Depends(require_token)])
def workflow_run_detail(workflow_run_id: str):
    maybe_sweep_workflow_runs()
    workflow_run = get_workflow_run(workflow_run_id)
    if not workflow_run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return _govern_project_wide_payload(
        {"run": workflow_run},
        action_id="workflow_run_read",
        target=workflow_run_id,
        cisiv_stage=(workflow_run or {}).get("cisiv_stage"),
        summary="Workflow run detail served.",
        run_id=workflow_run_id,
        details={"workflow_run_id": workflow_run_id, "workflow_id": (workflow_run or {}).get("workflow_id")},
    )


@app.get("/workflows/approvals", dependencies=[Depends(require_token)])
def workflow_approvals():
    maybe_sweep_workflow_runs()
    approvals = list_pending_workflow_approvals()
    return _govern_project_wide_payload(
        {"approvals": approvals},
        action_id="workflow_approval_list",
        target="workflow_approvals",
        cisiv_stage="verification",
        summary="Pending workflow approvals served.",
        details={"approval_count": len(approvals)},
    )


@app.post("/workflows/approvals/{approval_id}", dependencies=[Depends(require_token)])
def workflow_approval_action(approval_id: str, req: WorkflowApprovalActionRequest):
    from src.otem_execution_approval_bridge import (
        is_otem_execution_approval,
        resolve_otem_execution_approval,
    )

    approval = get_workflow_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Approval already {approval['status']}")

    run_record = get_workflow_run(approval["workflow_run_id"])
    if not run_record:
        raise HTTPException(status_code=404, detail="Workflow run not found for this approval")
    if run_record["status"] != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Workflow run is not waiting for approval")

    if is_otem_execution_approval(approval):
        if req.action not in {"approve", "reject"}:
            raise HTTPException(status_code=400, detail="Unsupported approval action")
        try:
            result = resolve_otem_execution_approval(approval, req.action)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        action_status = "approved" if result.get("status") == "approved" else "failed"
        return _govern_project_wide_payload(
            {"ok": True, "status": result.get("status")},
            action_id="workflow_approval_action",
            target=approval["workflow_id"],
            cisiv_stage=run_record.get("cisiv_stage"),
            summary=(
                f"OTEM execution approved for {approval['step_label']}."
                if result.get("status") == "approved"
                else f"OTEM execution rejected for {approval['step_label']}."
            ),
            action_status=action_status,
            run_id=approval["workflow_run_id"],
            details={
                "approval_id": approval_id,
                "workflow_id": approval["workflow_id"],
                "workflow_run_id": approval["workflow_run_id"],
                "step_id": approval["step_id"],
                "approval_action": req.action,
                "step_type": approval["step_type"],
                "substrate_stage": (result.get("substrate") or {}).get("stage"),
            },
        )

    run_output = run_record.get("output") or {}
    next_step_index = run_output.get("nextStepIndex")
    planned_steps = run_output.get("plannedSteps") or []
    current_step = (
        planned_steps[next_step_index]
        if isinstance(next_step_index, int) and 0 <= next_step_index < len(planned_steps)
        else None
    )
    if not current_step:
        raise HTTPException(status_code=409, detail="Workflow run is missing its paused approval target")
    if current_step and current_step.get("stepId") != approval["step_id"]:
        raise HTTPException(status_code=409, detail="Approval target does not match the paused workflow step")

    if req.action == "reject":
        update_workflow_approval(approval_id, "rejected")
        output = run_record["output"] if run_record else {}
        output = _govern_project_wide_payload(
            {
            **(output or {}),
            "error": f"Approval rejected for step: {approval['step_label']}",
            "message": f"Approval rejected for step: {approval['step_label']}",
            "rejectedAt": output.get("rejectedAt") or now_iso(),
            },
            action_id="workflow_approval_action",
            target=approval["workflow_id"],
            cisiv_stage=run_record.get("cisiv_stage"),
            summary=f"Workflow approval rejected for {approval['step_label']}.",
            action_status="failed",
            run_id=approval["workflow_run_id"],
            details={
                "approval_id": approval_id,
                "workflow_id": approval["workflow_id"],
                "workflow_run_id": approval["workflow_run_id"],
                "step_id": approval["step_id"],
                "approval_action": "reject",
            },
        )
        update_workflow_run(approval["workflow_run_id"], status="failed", output=output)
        return _govern_project_wide_payload(
            {"ok": True, "status": "rejected"},
            action_id="workflow_approval_action",
            target=approval["workflow_id"],
            cisiv_stage=run_record.get("cisiv_stage"),
            summary=f"Workflow approval rejected for {approval['step_label']}.",
            action_status="failed",
            run_id=approval["workflow_run_id"],
            details={
                "approval_id": approval_id,
                "workflow_id": approval["workflow_id"],
                "workflow_run_id": approval["workflow_run_id"],
                "step_id": approval["step_id"],
                "approval_action": "reject",
            },
        )

    update_workflow_approval(approval_id, "approved")
    try:
        run_workflow_job.delay(approval["workflow_run_id"], approval["workflow_id"], None, True)
    except Exception as exc:
        update_workflow_approval(approval_id, "pending")
        log_event("workflow_resume_queue_failed", {"workflow_run_id": approval["workflow_run_id"], "error": str(exc)})
        raise HTTPException(status_code=503, detail="Could not resume workflow") from exc
    return _govern_project_wide_payload(
        {"ok": True, "status": "approved"},
        action_id="workflow_approval_action",
        target=approval["workflow_id"],
        cisiv_stage=run_record.get("cisiv_stage"),
        summary=f"Workflow approval granted for {approval['step_label']}.",
        action_status="approved",
        run_id=approval["workflow_run_id"],
        details={
            "approval_id": approval_id,
            "workflow_id": approval["workflow_id"],
            "workflow_run_id": approval["workflow_run_id"],
            "step_id": approval["step_id"],
            "approval_action": "approve",
        },
    )


@app.get("/workflows/templates", dependencies=[Depends(require_token)])
def workflow_templates():
    return _govern_project_wide_payload(
        {"templates": WORKFLOW_TEMPLATES},
        action_id="workflow_template_list",
        target="workflow_templates",
        cisiv_stage="structure",
        summary="Workflow templates served.",
        details={"template_count": len(WORKFLOW_TEMPLATES)},
    )


@app.post("/workflows/templates/{template_id}/use", dependencies=[Depends(require_token)])
def use_workflow_template(template_id: str):
    template = get_workflow_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        normalized_config = validate_workflow_config(template["workflow"]["config"])
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=f"Template is invalid: {exc}") from exc

    workflow = create_workflow(
        name=template["workflow"]["name"],
        nodes=template["workflow"]["nodes"],
        edges=template["workflow"]["edges"],
        config=normalized_config,
        active=True,
        cisiv_stage="structure",
    )
    return _govern_project_wide_payload(
        {"workflow": workflow},
        action_id="workflow_template_use",
        target=workflow["id"],
        cisiv_stage=workflow["cisiv_stage"],
        summary=f"Workflow template {template_id} instantiated.",
        details={"workflow_id": workflow["id"], "template_id": template_id},
    )


@app.get("/onboarding", dependencies=[Depends(require_token)])
def onboarding_state():
    state = get_onboarding_state()
    return _govern_project_wide_payload(
        state,
        action_id="onboarding_state",
        target="onboarding",
        cisiv_stage=(state or {}).get("cisiv_stage"),
        summary="Onboarding state served.",
        details={"onboarding_done": bool((state or {}).get("onboarding_done"))},
    )


@app.post("/onboarding/complete", dependencies=[Depends(require_token)])
def onboarding_complete(req: OnboardingCompleteRequest):
    onboarding_law_details = _merge_project_law_details(
        {
            "tool_count": len(req.tools or []),
        },
        req,
    )
    _ensure_project_law_admission(
        action_id="onboarding_complete",
        target="onboarding",
        cisiv_stage=req.cisiv_stage or "identity",
        summary="Onboarding completion request admitted.",
        details=onboarding_law_details,
    )
    state = complete_onboarding(req.goal, req.tools, req.cisiv_stage)
    log_event(
        "onboarding_completed",
        {"goal": req.goal, "tools": req.tools, "cisiv_stage": state["cisiv_stage"]},
    )
    return _govern_project_wide_payload(
        {
        "ok": True,
        **state,
        },
        action_id="onboarding_complete",
        target="onboarding",
        cisiv_stage=state["cisiv_stage"],
        summary="Onboarding completion recorded.",
        details={
            **onboarding_law_details,
            "tool_count": len(state.get("tools") or []),
            "onboarding_done": bool(state.get("onboarding_done")),
        },
    )


@app.get(APP_SHELL_BASE_PATH)
@app.get(f"{APP_SHELL_BASE_PATH}/{{full_path:path}}")
def packaged_frontend(full_path: str = ""):
    if not _has_modern_frontend_bundle():
        raise HTTPException(status_code=404, detail="Packaged frontend bundle is not available")

    normalized_path = str(full_path or "").lstrip("/")
    if normalized_path:
        asset_path = _static_file_path(normalized_path)
        if asset_path:
            return FileResponse(asset_path)

    return _serve_frontend_index()
