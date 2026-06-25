"""Lawful agent task loop: brain ask, governance gate, tool execution."""

from __future__ import annotations

import asyncio
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from operator_kernel.config import OperatorKernelConfig, load_config, patch_require_approval_enabled
from operator_kernel.constitutional_task import register_operator_task
from operator_kernel.contracts import CreateTaskRequest, TaskConstraints
from operator_kernel.csr import CSR
from operator_kernel.events import TaskEventStore
from operator_kernel.observer_packet import emit_observer_packet_if_closed
from operator_kernel.status_mapping import sync_operator_status_to_csr
from operator_kernel.governance_gate import GovernanceGate
from operator_kernel.agent_profiles import merge_constraints
from operator_kernel.lawful_brain.planner_fallback import enrich_parsed_plan
from operator_kernel.tools.executor import ToolExecutor
from operator_kernel.tools.registry import filter_tools_for_constraints
from operator_kernel.memory.project_memory import ProjectMemory, _project_id
from operator_kernel.memory.semantic_store import SemanticStore
from operator_kernel.memory.task_context import update_task_summary

_running: set[str] = set()
_cancel_tokens: dict[str, threading.Event] = {}
_lock = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_title(goal: str, title: str | None = None) -> str:
    if title and title.strip():
        return title.strip()[:120]
    g = goal.strip().replace("\n", " ")
    return (g[:77] + "…") if len(g) > 80 else g


def is_task_running(task_id: str) -> bool:
    with _lock:
        return task_id in _running


def _ensure_cancel_token(task_id: str) -> None:
    """Register cancel slot when a task is created (before the loop thread starts)."""
    with _lock:
        if task_id not in _cancel_tokens:
            _cancel_tokens[task_id] = threading.Event()


def _reset_cancel_token(task_id: str) -> None:
    """Fresh cancel event for a follow-up run on an existing task."""
    with _lock:
        _cancel_tokens[task_id] = threading.Event()


def _set_running(task_id: str, running: bool) -> None:
    with _lock:
        if running:
            _running.add(task_id)
            # Preserve an early cancel signal — do not replace an existing token.
            if task_id not in _cancel_tokens:
                _cancel_tokens[task_id] = threading.Event()
        else:
            _running.discard(task_id)
            _cancel_tokens.pop(task_id, None)


def request_cancel(task_id: str) -> bool:
    """Signal a task to stop cooperatively (queued or running)."""
    with _lock:
        if task_id not in _cancel_tokens:
            _cancel_tokens[task_id] = threading.Event()
        _cancel_tokens[task_id].set()
        return True


def is_cancel_requested(task_id: str) -> bool:
    with _lock:
        token = _cancel_tokens.get(task_id)
        return token is not None and token.is_set()


async def _cancellable_sleep(task_id: str, seconds: float) -> None:
    if seconds <= 0:
        return
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if is_cancel_requested(task_id):
            return
        await asyncio.sleep(min(0.25, max(0.0, deadline - time.monotonic())))


async def _e2e_cancel_yield(task_id: str, goal: str) -> None:
    """Optional long yield for E2E cancel tests (OPERATOR_E2E_CANCEL_WINDOW=1)."""
    if os.environ.get("OPERATOR_E2E_CANCEL_WINDOW") != "1":
        return
    g = goal.lower()
    if "analyze" not in g and "file walk" not in g:
        return
    for _ in range(80):
        if is_cancel_requested(task_id):
            return
        await asyncio.sleep(0.25)


def _log_tool_memory(
    *,
    task_id: str,
    project_id: str,
    name: str,
    args: dict[str, Any],
    result_ok: bool,
    result_data: dict[str, Any] | None,
    result_error: str | None,
    steps: list[Any] | None = None,
) -> None:
    project = ProjectMemory()
    semantic = SemanticStore()
    if name in {"read_file", "write_patch"}:
        path = str(args.get("path") or "")
        if path:
            project.log_event(project_id, "file", path, {"tool": name}, task_id=task_id)
    if name in {"run_command", "run_tests"} and not result_ok:
        label = str(args.get("command") or args.get("target") or name)
        project.log_event(
            project_id,
            "failure",
            label,
            {"error": result_error, "data": result_data},
            task_id=task_id,
        )
        semantic.write(project_id, f"Failure running {label}: {result_error or 'unknown'}", task_id=task_id, item_type="failure")
    if steps:
        for step in steps[:3]:
            text = str(step).strip()
            if text:
                project.log_event(project_id, "decision", text, task_id=task_id)


def _finalize_task_summary(store: TaskEventStore, task_id: str, summary: str) -> None:
    update_task_summary(store, task_id, summary)
    project_id = _project_id(str(load_config().resolved_workspace_root()))
    SemanticStore().write(project_id, summary, task_id=task_id, item_type="task_message")


def _enrich_tool_calls(
    brain: dict[str, Any],
    intent: str,
    *,
    read_only: bool,
) -> list[dict[str, Any]]:
    tool_calls = brain.get("tool_calls") or []
    if not load_config().planner_fallback_enabled:
        return [tc if isinstance(tc, dict) else tc for tc in tool_calls]
    cfg = load_config()
    parsed = enrich_parsed_plan(
        {
            "tool_calls": tool_calls,
            "steps": brain.get("steps") or [],
            "explanations": brain.get("explanations") or [],
        },
        intent,
        read_only=read_only,
        workspace_root=Path(cfg.resolved_workspace_root()),
    )
    enriched = parsed.get("tool_calls") or []
    return [tc if isinstance(tc, dict) else tc for tc in enriched]


def _ensure_csr_task(task_id: str, store: TaskEventStore, goal: str) -> None:
    try:
        CSR.get_state(task_id)
    except KeyError:
        CSR.load_task_persisted(task_id, store.task_dir(task_id))
        try:
            CSR.get_state(task_id)
        except KeyError:
            register_operator_task(CSR, task_id, goal=goal)


def _apply_operator_status(
    task_id: str,
    store: TaskEventStore,
    meta: dict[str, Any],
    status: str,
    *,
    kind: str | None = None,
    legal_basis: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Set meta[\"status\"] and sync constitutional state via the mapping table."""
    meta["status"] = status
    meta["updated_at"] = _utc_now()
    sync_operator_status_to_csr(
        CSR,
        task_id,
        meta,
        kind=kind,
        legal_basis=legal_basis,
        payload=payload,
    )
    store.write_meta(task_id, meta)


def _constitutional_finalize_closed(
    task_id: str,
    store: TaskEventStore,
    meta: dict[str, Any],
    *,
    kind: str,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> None:
    from operator_kernel.observer_packet import constitutional_close_task

    _apply_operator_status(task_id, store, meta, "completed", payload=payload)
    constitutional_close_task(
        task_id,
        meta,
        kind=kind,
        legal_basis=legal_basis,
        payload=payload,
    )
    store.write_meta(task_id, meta)
    store.append(
        task_id,
        "constitutional_closed",
        {
            "constitutional_state": meta.get("constitutional_state"),
            "observer_packet": meta.get("constitutional_observer_packet"),
        },
    )


def _abort_if_cancelled(
    task_id: str,
    store: TaskEventStore,
    meta: dict[str, Any],
    messages: list[dict[str, str]],
) -> bool:
    if not is_cancel_requested(task_id):
        return False
    meta["messages"] = messages
    _apply_operator_status(task_id, store, meta, "cancelled", legal_basis="user_requested_cancel")
    packet_dir = emit_observer_packet_if_closed(task_id, meta)
    if packet_dir:
        meta["constitutional_observer_packet"] = str(packet_dir)
        store.write_meta(task_id, meta)
        store.append(
            task_id,
            "constitutional_closed",
            {
                "constitutional_state": meta.get("constitutional_state"),
                "observer_packet": meta.get("constitutional_observer_packet"),
                "reason": "cancelled",
            },
        )
    store.append(task_id, "task_cancelled", {"reason": "user_requested"})
    return True


def _resolve_constraints(body: CreateTaskRequest) -> TaskConstraints:
    return merge_constraints(body.agent_id, body.constraints)


def _initial_meta(body: CreateTaskRequest, constraints: TaskConstraints) -> dict[str, Any]:
    return {
        "task_id": "",
        "goal": body.goal,
        "title": _task_title(body.goal, body.title),
        "agent_id": body.agent_id or "builder",
        "workspace_root": body.workspace_root,
        "constraints": constraints.model_dump(),
        "status": "queued",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "messages": [{"role": "user", "content": body.goal}],
    }


def start_task(
    body: CreateTaskRequest,
    config: OperatorKernelConfig,
    store: TaskEventStore,
    gate: GovernanceGate,
    executor: ToolExecutor,
) -> str:
    # Lawful operator kernel (governance gate + patch approval) stays available when
    # AAIS_UNLAWFUL_AGENTS_DISABLED blocks ungoverned AAIS /agent/run and plug-class agents.
    task_id = str(uuid.uuid4())
    constraints = _resolve_constraints(body)
    meta = _initial_meta(body, constraints)
    meta["task_id"] = task_id
    store.task_dir(task_id)
    register_operator_task(CSR, task_id, goal=body.goal)
    _apply_operator_status(task_id, store, meta, "queued", legal_basis="task_created")
    store.append(
        task_id,
        "task_created",
        {
            "goal": body.goal,
            "title": meta["title"],
            "agent_id": meta["agent_id"],
            "constraints": constraints.model_dump(),
        },
    )
    _ensure_cancel_token(task_id)

    def _run() -> None:
        asyncio.run(_run_agent_loop(task_id, config, store, gate, executor, is_follow_up=False))

    threading.Thread(target=_run, name=f"agent-task-{task_id[:8]}", daemon=True).start()
    return task_id


def continue_task(
    task_id: str,
    user_text: str,
    config: OperatorKernelConfig,
    store: TaskEventStore,
    gate: GovernanceGate,
    executor: ToolExecutor,
) -> None:
    if is_task_running(task_id):
        raise RuntimeError("task already running")

    meta = store.read_meta(task_id)
    if meta.get("status") == "awaiting_approval":
        raise RuntimeError("task awaiting patch approval")
    messages: list[dict[str, str]] = list(meta.get("messages") or [])
    messages.append({"role": "user", "content": user_text})
    meta["messages"] = messages
    _apply_operator_status(task_id, store, meta, "running", legal_basis="follow_up_message")
    _reset_cancel_token(task_id)
    store.append(task_id, "user_message", {"text": user_text})

    def _run() -> None:
        asyncio.run(_run_agent_loop(task_id, config, store, gate, executor, is_follow_up=True))

    threading.Thread(target=_run, name=f"agent-continue-{task_id[:8]}", daemon=True).start()


class _LawfulAskCancelled(RuntimeError):
    """Raised when lawful_ask is interrupted by a user cancel request."""


def _lawful_ask_local(
    intent: str,
    context: dict[str, Any],
    tools: list[dict[str, Any]],
    constraints: TaskConstraints,
) -> dict[str, Any]:
    """In-process lawful brain when the HTTP service on lawful_brain_url is unreachable."""
    from operator_kernel.contracts import LawfulAskRequest
    from operator_kernel.lawful_brain.adapter import LawfulBrainAdapter

    request = LawfulAskRequest(
        intent=intent,
        context=context,
        tools=tools,
        constraints=constraints.model_dump(),
    )
    response = LawfulBrainAdapter().ask(request)
    return response.model_dump(mode="json")


def _lawful_brain_unreachable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)):
        return True
    if isinstance(exc, (ConnectionRefusedError, ConnectionError)):
        return True
    if isinstance(exc, OSError):
        # WinError 10061 / errno 111 — nothing listening on lawful_brain_url
        errno = getattr(exc, "errno", None)
        winerror = getattr(exc, "winerror", None)
        if errno in (10061, 111) or winerror == 10061:
            return True
    if isinstance(exc, asyncio.TimeoutError):
        return True
    if isinstance(exc, asyncio.CancelledError):
        return False
    cause = getattr(exc, "__cause__", None)
    if cause is not None:
        return _lawful_brain_unreachable(cause)
    return False


async def _lawful_ask(
    config: OperatorKernelConfig,
    intent: str,
    context: dict[str, Any],
    tools: list[dict[str, Any]],
    constraints: TaskConstraints,
    *,
    task_id: str | None = None,
) -> dict[str, Any]:
    url = f"{config.lawful_brain_url.rstrip('/')}/v1/lawful_ask"
    payload = {
        "intent": intent,
        "context": context,
        "tools": tools,
        "constraints": constraints.model_dump(),
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        post_task = asyncio.create_task(client.post(url, json=payload))
        try:
            while not post_task.done():
                if task_id and is_cancel_requested(task_id):
                    post_task.cancel()
                    raise _LawfulAskCancelled("lawful_ask cancelled")
                try:
                    response = await asyncio.wait_for(asyncio.shield(post_task), timeout=0.25)
                    response.raise_for_status()
                    return response.json()
                except asyncio.TimeoutError:
                    continue
            response = await post_task
            response.raise_for_status()
            return response.json()
        except asyncio.CancelledError as exc:
            raise _LawfulAskCancelled("lawful_ask cancelled") from exc
        except httpx.HTTPStatusError:
            raise
        except Exception as exc:
            if isinstance(exc, _LawfulAskCancelled):
                raise
            if _lawful_brain_unreachable(exc):
                return _lawful_ask_local(intent, context, tools, constraints)
            raise


def _intent_from_messages(messages: list[dict[str, str]], is_follow_up: bool) -> str:
    if not messages:
        return "Continue the task."
    if is_follow_up and len(messages) > 1:
        lines = []
        for m in messages[-6:]:
            role = m.get("role", "user")
            content = (m.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "Continue this agent session.\n\n" + "\n".join(lines)
    last = messages[-1].get("content", "")
    return last or "Continue the task."


async def _run_agent_loop(
    task_id: str,
    config: OperatorKernelConfig,
    store: TaskEventStore,
    gate: GovernanceGate,
    executor: ToolExecutor,
    *,
    is_follow_up: bool,
) -> None:
    _set_running(task_id, True)
    meta = store.read_meta(task_id)
    goal = meta.get("goal") or ""
    _ensure_csr_task(task_id, store, goal)
    constraints = TaskConstraints(**(meta.get("constraints") or {}))
    messages: list[dict[str, str]] = list(meta.get("messages") or [{"role": "user", "content": goal}])

    _apply_operator_status(task_id, store, meta, "running", legal_basis="task_started")
    store.append(task_id, "task_started", {"is_follow_up": is_follow_up})

    await _e2e_cancel_yield(task_id, goal)

    tool_catalog = filter_tools_for_constraints(constraints)
    context_base: dict[str, Any] = {
        "task_id": task_id,
        "workspace_root": str(config.resolved_workspace_root()),
        "agent_id": meta.get("agent_id"),
    }

    try:
        for step in range(constraints.max_steps):
            if _abort_if_cancelled(task_id, store, meta, messages):
                return

            await _cancellable_sleep(task_id, config.inter_step_sleep_sec)
            if _abort_if_cancelled(task_id, store, meta, messages):
                return

            intent = _intent_from_messages(messages, is_follow_up and step == 0)
            store.append(task_id, "step_started", {"step": step + 1, "max_steps": constraints.max_steps})

            if _abort_if_cancelled(task_id, store, meta, messages):
                return

            try:
                brain = await _lawful_ask(
                    config,
                    intent=intent,
                    context={**context_base, "step": step + 1, "messages": messages[-8:]},
                    tools=tool_catalog,
                    constraints=constraints,
                    task_id=task_id,
                )
            except _LawfulAskCancelled:
                if _abort_if_cancelled(task_id, store, meta, messages):
                    return
                raise

            steps = brain.get("steps") or []
            if steps:
                store.append(task_id, "plan_updated", {"steps": steps})
                _apply_operator_status(
                    task_id,
                    store,
                    meta,
                    "planned",
                    legal_basis="plan_updated",
                    payload={"steps": steps[:5]},
                )
                _log_tool_memory(
                    task_id=task_id,
                    project_id=_project_id(str(config.resolved_workspace_root())),
                    name="plan_updated",
                    args={},
                    result_ok=True,
                    result_data=None,
                    result_error=None,
                    steps=steps,
                )

            for line in brain.get("explanations") or []:
                if line:
                    store.append(task_id, "assistant_message", {"text": str(line)})

            tool_calls = _enrich_tool_calls(brain, intent, read_only=constraints.read_only)
            if not tool_calls:
                summary = (brain.get("plan") or {}).get("summary") or "No further tool calls."
                store.append(task_id, "assistant_message", {"text": summary})
                messages.append({"role": "assistant", "content": summary})
                meta["messages"] = messages
                meta["updated_at"] = _utc_now()
                _constitutional_finalize_closed(
                    task_id,
                    store,
                    meta,
                    kind="Closure",
                    legal_basis="task_completed_no_tools",
                    payload={"summary": summary},
                )
                _finalize_task_summary(store, task_id, summary)
                store.append(task_id, "task_completed", {"summary": summary, "steps_executed": step + 1})
                return

            _apply_operator_status(task_id, store, meta, "executing", legal_basis="tool_execution")

            for raw_call in tool_calls:
                if _abort_if_cancelled(task_id, store, meta, messages):
                    return

                await _cancellable_sleep(task_id, config.inter_step_sleep_sec)
                if _abort_if_cancelled(task_id, store, meta, messages):
                    return

                if not isinstance(raw_call, dict):
                    raw_call = {
                        "id": getattr(raw_call, "id", None),
                        "name": getattr(raw_call, "name", None),
                        "args": getattr(raw_call, "args", None),
                    }
                name = str(raw_call.get("name") or raw_call.get("tool") or "unknown")
                args = dict(raw_call.get("args") or raw_call.get("arguments") or {})
                call_id = str(raw_call.get("id") or uuid.uuid4())

                store.append(
                    task_id,
                    "tool_called",
                    {"id": call_id, "name": name, "tool": name, "args": args},
                )

                verdict, receipt = gate.check_tool(
                    name, args, constraints, tool_call_id=call_id
                )
                store.append(task_id, "law_receipt", receipt.model_dump())

                if verdict.verdict == "revise" and verdict.revised_args:
                    args = {**args, **verdict.revised_args}

                if verdict.verdict == "deny":
                    err = verdict.reason or "governance denied"
                    store.append(
                        task_id,
                        "tool_result",
                        {"id": call_id, "name": name, "ok": False, "error": err},
                    )
                    store.append(task_id, "error", {"message": err, "tool": name})
                    meta["messages"] = messages
                    _apply_operator_status(task_id, store, meta, "failed", legal_basis="governance_denied")
                    return

                if (
                    name == "write_patch"
                    and patch_require_approval_enabled()
                    and verdict.verdict in {"allow", "revise"}
                ):
                    path = str(args.get("path") or "")
                    diff = str(args.get("diff") or "")
                    store.append(
                        task_id,
                        "patch_preview",
                        {"id": call_id, "path": path, "diff": diff, "args": args},
                    )
                    store.append(
                        task_id,
                        "tool_result",
                        {
                            "id": call_id,
                            "name": name,
                            "ok": True,
                            "data": {
                                "pending_approval": True,
                                "path": path,
                                "patch": diff,
                                "diff": diff,
                            },
                        },
                    )
                    meta["pending_patch"] = {
                        "id": call_id,
                        "path": path,
                        "diff": diff,
                        "args": args,
                    }
                    meta["messages"] = messages
                    _apply_operator_status(
                        task_id,
                        store,
                        meta,
                        "awaiting_approval",
                        legal_basis="patch_pending_approval",
                        payload={"path": path},
                    )
                    store.append(
                        task_id,
                        "task_completed",
                        {
                            "summary": f"Awaiting approval for patch to {path}",
                            "status": "awaiting_approval",
                        },
                    )
                    return

                result = await asyncio.to_thread(
                    executor.execute, name, args, constraints, call_id
                )
                store.append(
                    task_id,
                    "tool_result",
                    {
                        "id": call_id,
                        "name": name,
                        "ok": result.ok,
                        "data": result.data,
                        "error": result.error,
                    },
                )
                _log_tool_memory(
                    task_id=task_id,
                    project_id=_project_id(str(config.resolved_workspace_root())),
                    name=name,
                    args=args,
                    result_ok=result.ok,
                    result_data=result.data,
                    result_error=result.error,
                )
                if not result.ok:
                    store.append(
                        task_id,
                        "error",
                        {"message": result.error or "tool failed", "tool": name},
                    )
                    meta["messages"] = messages
                    _apply_operator_status(
                        task_id,
                        store,
                        meta,
                        "failed",
                        legal_basis="tool_failed",
                        payload={"tool": name, "error": result.error},
                    )
                    from operator_kernel.observer_packet import constitutional_fail_task

                    constitutional_fail_task(
                        task_id,
                        meta,
                        legal_basis="tool_failed",
                        payload={"tool": name, "error": result.error},
                    )
                    store.write_meta(task_id, meta)
                    return

            store.append(task_id, "step_completed", {"step": step + 1})
            if _abort_if_cancelled(task_id, store, meta, messages):
                return
            summary = f"Completed step {step + 1} with {len(tool_calls)} tool call(s)."
            messages.append({"role": "assistant", "content": summary})
            meta["messages"] = messages
            meta["updated_at"] = _utc_now()
            _constitutional_finalize_closed(
                task_id,
                store,
                meta,
                kind="Closure",
                legal_basis="task_completed",
                payload={"summary": summary, "steps_executed": step + 1},
            )
            _finalize_task_summary(store, task_id, summary)
            store.append(task_id, "task_completed", {"summary": summary, "steps_executed": step + 1})
            return

        store.append(task_id, "error", {"message": "max_steps reached"})
        meta["messages"] = messages
        _apply_operator_status(task_id, store, meta, "failed", legal_basis="max_steps_reached")
        from operator_kernel.observer_packet import constitutional_fail_task

        constitutional_fail_task(task_id, meta, legal_basis="max_steps_reached")
        store.write_meta(task_id, meta)
    except Exception as exc:
        store.append(task_id, "error", {"message": str(exc)})
        meta = store.read_meta(task_id)
        _apply_operator_status(
            task_id,
            store,
            meta,
            "failed",
            legal_basis="exception",
            payload={"error": str(exc)},
        )
        from operator_kernel.observer_packet import constitutional_fail_task

        constitutional_fail_task(
            task_id,
            meta,
            legal_basis="exception",
            payload={"error": str(exc)},
        )
        store.write_meta(task_id, meta)
    finally:
        _set_running(task_id, False)
