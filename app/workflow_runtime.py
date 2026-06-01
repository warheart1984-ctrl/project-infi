from __future__ import annotations

import json
import threading
import uuid
from copy import deepcopy
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import SLACK_WEBHOOK_URL, WORKFLOW_HEARTBEAT_INTERVAL_SECONDS, WORKFLOW_LEASE_SECONDS
from app.db import (
    claim_workflow_run_lease,
    create_workflow_approval,
    get_latest_workflow_approval_for_step,
    get_workflow,
    get_workflow_run,
    now_iso,
    renew_workflow_run_lease,
    update_workflow_run,
)
from app.llm import chat
from app.workflow_validation import WorkflowValidationError, validate_workflow_config
from src.cisiv import normalize_cisiv_stage


def build_draft_workflow(prompt: str, name: str | None = None, cisiv_stage: str | None = None) -> dict:
    lowered = (prompt or "").lower()
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="concept")

    trigger_subtype = (
        "slack.message"
        if "slack" in lowered
        else "webhook.received"
        if "webhook" in lowered
        else "schedule.tick"
        if "schedule" in lowered or "daily" in lowered
        else "email.received"
    )

    final_action_type = "email.send" if "email" in lowered else "slack.send"
    final_action_label = "Send Email" if final_action_type == "email.send" else "Send Slack Message"
    final_action_config = (
        {"to": "user@example.com", "subject": "AAIS Workflow Result"}
        if final_action_type == "email.send"
        else {"channel": "#alerts"}
    )

    nodes = [
        {
            "id": "trigger-generated",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {
                "label": "Incoming Trigger",
                "kind": "trigger",
                "subtype": trigger_subtype,
                "config": {"source": "default"},
            },
        },
        {
            "id": "action-generated-1",
            "type": "actionNode",
            "position": {"x": 380, "y": 140},
            "data": {
                "label": "Analyze with AI",
                "kind": "action",
                "subtype": "ai.analyze",
                "config": {"goal": prompt or "Analyze input"},
            },
        },
        {
            "id": "action-generated-2",
            "type": "actionNode",
            "position": {"x": 720, "y": 140},
            "data": {
                "label": final_action_label,
                "kind": "action",
                "subtype": final_action_type,
                "config": final_action_config,
            },
        },
    ]

    edges = [
        {"id": "g1", "source": "trigger-generated", "target": "action-generated-1"},
        {"id": "g2", "source": "action-generated-1", "target": "action-generated-2"},
    ]

    config = {
        "schemaVersion": 1,
        "name": name or "Generated Workflow",
        "trigger": {
            "type": trigger_subtype,
            "label": "Incoming Trigger",
            "config": {"source": "default"},
        },
        "steps": [
            {
                "id": "action-generated-1",
                "order": 1,
                "type": "ai.analyze",
                "label": "Analyze with AI",
                "config": {"goal": prompt or "Analyze input"},
            },
            {
                "id": "action-generated-2",
                "order": 2,
                "type": final_action_type,
                "label": final_action_label,
                "config": final_action_config,
            },
        ],
        "edges": [
            {"id": "g1", "source": "trigger-generated", "sourceHandle": None, "target": "action-generated-1"},
            {"id": "g2", "source": "action-generated-1", "sourceHandle": None, "target": "action-generated-2"},
        ],
    }

    return {
        "name": name or "Generated Workflow",
        "nodes": nodes,
        "edges": edges,
        "config": config,
        "cisiv_stage": normalized_cisiv_stage,
    }


def simulate_workflow(workflow: dict, cisiv_stage: str | None = None) -> dict:
    workflow = validate_workflow_config(workflow)
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="verification")
    steps = [
        {
            "step": index + 1,
            "label": step["label"],
            "type": step["type"],
            "status": "simulated",
            "output": f"Simulated {step['type']}",
            "cisiv_stage": normalized_cisiv_stage,
        }
        for index, step in enumerate(workflow.get("steps", []))
    ]
    return {
        "ok": True,
        "workflow_name": workflow.get("name") or "Untitled workflow",
        "trigger": workflow.get("trigger"),
        "steps": steps,
        "summary": f"Simulated {len(steps)} step(s).",
        "cisiv_stage": normalized_cisiv_stage,
    }


def is_risky_step(step: dict) -> bool:
    step_type = step.get("type")
    if step_type == "slack.send":
        return _slack_delivery_mode(step) != "fake"

    risky_types = {"email.send", "api.call"}
    if step_type in risky_types:
        return True

    lowered = json.dumps(step.get("config") or {}).lower()
    return any(token in lowered for token in ("delete", "payment", "invoice", "customer"))


def risk_reason(step: dict) -> str:
    step_type = step.get("type")
    if step_type == "email.send":
        return "This step prepares or sends an email to a recipient."
    if step_type == "slack.send":
        delivery_mode = _slack_delivery_mode(step)
        if delivery_mode == "webhook":
            return "This step posts a live message to Slack through an incoming webhook."
        return "This step prepares a Slack message and still requires human approval."
    if step_type == "api.call":
        return "This step calls an external API."
    return "This step was flagged as potentially sensitive."


def _extract_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("text") or value.get("content") or value.get("summary") or json.dumps(value))
    return json.dumps(value)


def _coerce_step_delay_ms(*values) -> int:
    for value in values:
        if value in (None, ""):
            continue
        try:
            delay_ms = int(value)
        except (TypeError, ValueError):
            continue
        if delay_ms > 0:
            return max(0, min(delay_ms, 60000))
    return 0


def _maybe_sleep_for_step(step: dict, input_data) -> None:
    config = step.get("config") or {}
    input_delay = input_data.get("simulateDelayMs") if isinstance(input_data, dict) else None
    delay_ms = _coerce_step_delay_ms(
        config.get("simulateDelayMs"),
        config.get("delayMs"),
        input_delay,
    )
    if delay_ms:
        sleep(delay_ms / 1000)


def _analysis_mode(step: dict) -> str:
    config = step.get("config") or {}
    mode = str(config.get("mode") or "live").strip().lower()
    if mode in {"fake", "live"}:
        return mode
    return "live"


def _slack_delivery_mode(step: dict) -> str:
    config = step.get("config") or {}
    mode = str(config.get("deliveryMode") or "manual").strip().lower()
    if mode in {"fake", "webhook"}:
        return mode
    return "manual"


def _run_ai_analysis(step: dict, input_data):
    text = _extract_text(input_data)
    goal = (step.get("config") or {}).get("goal") or "Analyze input"
    analysis_mode = _analysis_mode(step)
    if analysis_mode == "fake":
        summary = f"Summary of: {text[:200]}"
    else:
        try:
            prompt = (
                f"Analyze this input for the workflow goal below.\n\n"
                f"Goal: {goal}\n\n"
                f"Input:\n{text}\n\n"
                f"Return a concise summary and any important signals."
            )
            summary = chat([{"role": "user", "content": prompt}], temperature=0.2, fast=True).strip()
        except Exception:
            summary = f"Summary of: {text[:200]}"

    return {
        "ok": True,
        "step_id": step["id"],
        "type": step["type"],
        "label": step["label"],
        "output": (
            f"Simulated AI analysis for goal: {goal}"
            if analysis_mode == "fake"
            else f"AI analyzed input for goal: {goal}"
        ),
        "data": {
            "text": text,
            "goal": goal,
            "summary": summary or f"Summary of: {text[:200]}",
            "mode": analysis_mode,
        },
    }


def _run_condition(step: dict, input_data):
    config = step.get("config") or {}
    condition_type = step.get("type", "").split(".", 1)[-1]
    text = _extract_text(input_data).lower()
    passed = True

    if condition_type == "contains_text":
        needle = str(config.get("value") or config.get("text") or "").lower()
        passed = bool(needle) and needle in text
    elif condition_type == "high_priority":
        passed = any(token in text for token in ("urgent", "important", "asap", "priority"))
    elif condition_type == "from_domain":
        domain = str(config.get("value") or config.get("domain") or "").lower()
        passed = bool(domain) and domain in text
    elif condition_type == "confidence_above":
        threshold = float(config.get("threshold") or 0.5)
        passed = threshold <= 0.7

    return {
        "ok": True,
        "step_id": step["id"],
        "type": step["type"],
        "label": step["label"],
        "output": "Condition passed" if passed else "Condition failed",
        "data": {
            "passed": passed,
            "condition": condition_type,
            "input": input_data,
        },
    }


def _perform_api_call(step: dict, input_data):
    config = step.get("config") or {}
    method = str(config.get("method") or "GET").upper()
    url = config.get("url")
    if not url:
        raise RuntimeError(f"Step '{step['label']}' is missing config.url")

    body = None if method == "GET" else json.dumps(input_data or {}).encode("utf-8")
    request = Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
            data = json.loads(raw) if "application/json" in content_type else raw
            return {
                "ok": 200 <= response.status < 300,
                "step_id": step["id"],
                "type": step["type"],
                "label": step["label"],
                "output": f"API {method} {url} -> {response.status}",
                "data": data,
            }
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="ignore")
        return {
            "ok": False,
            "step_id": step["id"],
            "type": step["type"],
            "label": step["label"],
            "output": f"API {method} {url} -> {exc.code}",
            "data": body_text,
        }
    except URLError as exc:
        raise RuntimeError(f"API call failed: {exc.reason}") from exc


def _deliver_slack_message(step: dict, input_data):
    config = step.get("config") or {}
    message = _extract_text(input_data)
    channel = config.get("channel") or "#general"
    delivery_mode = _slack_delivery_mode(step)

    if delivery_mode == "fake":
        return {
            "ok": True,
            "step_id": step["id"],
            "type": step["type"],
            "label": step["label"],
            "output": f"Simulated Slack message for {channel}",
            "data": {
                "channel": channel,
                "message": message,
                "deliveryMode": delivery_mode,
            },
        }

    if delivery_mode == "webhook":
        webhook_url = str(config.get("webhookUrl") or SLACK_WEBHOOK_URL or "").strip()
        if not webhook_url:
            raise RuntimeError("Slack webhook URL is not configured for live delivery.")

        request = Request(
            webhook_url,
            data=json.dumps({"text": message}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                response.read()
                return {
                    "ok": 200 <= response.status < 300,
                    "step_id": step["id"],
                    "type": step["type"],
                    "label": step["label"],
                    "output": f"Slack message sent to {channel}",
                    "data": {
                        "channel": channel,
                        "message": message,
                        "deliveryMode": delivery_mode,
                        "status": response.status,
                    },
                }
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="ignore")
            return {
                "ok": False,
                "step_id": step["id"],
                "type": step["type"],
                "label": step["label"],
                "output": f"Slack webhook failed with status {exc.code}",
                "data": {
                    "channel": channel,
                    "message": message,
                    "deliveryMode": delivery_mode,
                    "error": body_text,
                },
            }
        except URLError as exc:
            raise RuntimeError(f"Slack webhook failed: {exc.reason}") from exc

    return {
        "ok": True,
        "step_id": step["id"],
        "type": step["type"],
        "label": step["label"],
        "output": f"Prepared Slack message for {channel}",
        "data": {
            "channel": channel,
            "message": message,
            "deliveryMode": delivery_mode,
        },
    }


def run_workflow_step(step: dict, input_data):
    step_type = step.get("type", "")
    config = step.get("config") or {}
    _maybe_sleep_for_step(step, input_data)

    if step_type == "ai.analyze":
        return _run_ai_analysis(step, input_data)

    if step_type.startswith("condition."):
        return _run_condition(step, input_data)

    if step_type == "slack.send":
        return _deliver_slack_message(step, input_data)

    if step_type == "email.send":
        body = _extract_text(input_data)
        return {
            "ok": True,
            "step_id": step["id"],
            "type": step_type,
            "label": step["label"],
            "output": f"Prepared email for {config.get('to') or 'user@example.com'}",
            "data": {
                "to": config.get("to") or "user@example.com",
                "subject": config.get("subject") or "AAIS Workflow Result",
                "body": body,
            },
        }

    if step_type == "api.call":
        return _perform_api_call(step, input_data)

    if step_type == "task.create":
        return {
            "ok": True,
            "step_id": step["id"],
            "type": step_type,
            "label": step["label"],
            "output": f"Created task draft: {config.get('title') or 'Untitled task'}",
            "data": {
                "title": config.get("title") or "Untitled task",
                "payload": input_data,
            },
        }

    return {
        "ok": True,
        "step_id": step["id"],
        "type": step_type,
        "label": step["label"],
        "output": f"Skipped unsupported step type: {step_type}",
        "data": input_data,
    }


def _append_ledger(output: dict, event_type: str, message: str, **extra) -> dict:
    ledger = list(output.get("ledger") or [])
    cisiv_stage = normalize_cisiv_stage(
        extra.pop("cisiv_stage", None) or output.get("cisiv_stage"),
        default="implementation",
    )
    ledger.append({"type": event_type, "message": message, "at": now_iso(), "cisiv_stage": cisiv_stage, **extra})
    output["ledger"] = ledger[-25:]
    output["cisiv_stage"] = cisiv_stage
    return output


def _planned_step_template(step: dict, index: int, cisiv_stage: str) -> dict:
    return {
        "stepId": step["id"],
        "label": step["label"],
        "type": step["type"],
        "order": step.get("order", index + 1),
        "cisiv_stage": cisiv_stage,
        "status": "pending",
        "output": None,
        "error": None,
        "attempt": 0,
        "startedAt": None,
        "completedAt": None,
        "resultRef": None,
    }


def _normalize_planned_steps(
    ordered_steps: list[dict],
    raw_steps: list[dict] | None,
    *,
    cisiv_stage: str = "implementation",
) -> list[dict]:
    raw_steps = raw_steps or []
    raw_by_id = {
        step.get("stepId"): step
        for step in raw_steps
        if isinstance(step, dict) and step.get("stepId")
    }
    normalized = []
    for index, step in enumerate(ordered_steps):
        base = _planned_step_template(step, index, normalize_cisiv_stage(cisiv_stage, default="implementation"))
        existing = raw_by_id.get(step["id"], {})
        normalized.append(
            {
                **base,
                "cisiv_stage": normalize_cisiv_stage(existing.get("cisiv_stage"), default=base["cisiv_stage"]),
                "status": existing.get("status") or base["status"],
                "output": existing.get("output"),
                "error": existing.get("error"),
                "attempt": int(existing.get("attempt") or 0),
                "startedAt": existing.get("startedAt"),
                "completedAt": existing.get("completedAt"),
                "resultRef": existing.get("resultRef"),
            }
        )
    return normalized


def _normalize_completed_steps(raw_steps: list[dict] | None, *, cisiv_stage: str = "implementation") -> list[dict]:
    steps = []
    for step in raw_steps or []:
        if not isinstance(step, dict):
            continue
        steps.append(
            {
                "stepId": step.get("stepId"),
                "label": step.get("label"),
                "type": step.get("type"),
                "cisiv_stage": normalize_cisiv_stage(step.get("cisiv_stage"), default=cisiv_stage),
                "ok": bool(step.get("ok", True)),
                "output": step.get("output"),
                "data": step.get("data"),
                "attempt": int(step.get("attempt") or 0),
                "resultRef": step.get("resultRef"),
            }
        )
    return steps


def _normalize_ledger(raw_ledger: list[dict] | None) -> list[dict]:
    ledger = []
    for entry in raw_ledger or []:
        if not isinstance(entry, dict):
            continue
        ledger.append(
            {
                "type": entry.get("type"),
                "message": entry.get("message"),
                "at": entry.get("at"),
                **{
                    key: value
                    for key, value in entry.items()
                    if key not in {"type", "message", "at"}
                },
            }
        )
    return ledger


def _resolve_next_step_index(planned_steps: list[dict], suggested_index) -> int:
    if isinstance(suggested_index, int) and 0 <= suggested_index < len(planned_steps):
        if planned_steps[suggested_index].get("status") != "completed":
            return suggested_index
    for index, planned_step in enumerate(planned_steps):
        if planned_step.get("status") != "completed":
            return index
    return len(planned_steps)


def _build_output(
    workflow_name: str,
    trigger: dict | None,
    total_steps: int,
    planned_steps: list[dict],
    completed_steps: list[dict],
    current_data,
    started_at: str,
    ledger: list[dict] | None = None,
    **extra,
) -> dict:
    cisiv_stage = normalize_cisiv_stage(extra.get("cisiv_stage"), default="implementation")
    return {
        "workflowName": workflow_name,
        "trigger": trigger,
        "totalSteps": total_steps,
        "plannedSteps": planned_steps,
        "steps": completed_steps,
        "completedSteps": completed_steps,
        "currentData": current_data,
        "startedAt": started_at,
        "ledger": deepcopy(ledger or []),
        "cisiv_stage": cisiv_stage,
        **extra,
    }


def _start_heartbeat(workflow_run_id: str, lease_owner: str):
    stop_event = threading.Event()

    def heartbeat_loop():
        while not stop_event.wait(WORKFLOW_HEARTBEAT_INTERVAL_SECONDS):
            if not renew_workflow_run_lease(workflow_run_id, lease_owner, WORKFLOW_LEASE_SECONDS):
                break

    thread = threading.Thread(
        target=heartbeat_loop,
        name=f"workflow-heartbeat-{workflow_run_id}",
        daemon=True,
    )
    thread.start()
    return stop_event, thread


def _stop_heartbeat(stop_event: threading.Event | None, thread: threading.Thread | None) -> None:
    if stop_event:
        stop_event.set()
    if thread and thread.is_alive():
        thread.join(timeout=1.0)


def execute_queued_workflow_run(workflow_run_id: str, workflow_id: str, trigger_data=None, resume: bool = False):
    workflow = get_workflow(workflow_id)
    if not workflow:
        update_workflow_run(
            workflow_run_id,
            status="failed",
            output={"error": "Workflow not found", "cisiv_stage": "implementation"},
        )
        return

    existing_run = get_workflow_run(workflow_run_id)
    if not existing_run:
        return

    claim_from_statuses: list[str]
    if resume:
        if existing_run["status"] == "awaiting_approval":
            claim_from_statuses = ["awaiting_approval"]
        elif existing_run["status"] == "recovering":
            claim_from_statuses = ["recovering"]
        else:
            return
    else:
        if existing_run["status"] != "queued":
            return
        claim_from_statuses = ["queued"]

    lease_owner = f"workflow-worker:{uuid.uuid4()}"
    claimed = claim_workflow_run_lease(
        workflow_run_id,
        claim_from_statuses,
        "running",
        lease_owner,
        WORKFLOW_LEASE_SECONDS,
    )
    if not claimed:
        return
    existing_run = claimed

    heartbeat_stop = None
    heartbeat_thread = None

    try:
        heartbeat_stop, heartbeat_thread = _start_heartbeat(workflow_run_id, lease_owner)
        config = validate_workflow_config(workflow["config"] or {})
    except WorkflowValidationError as exc:
        update_workflow_run(
            workflow_run_id,
            status="failed",
            output={"error": str(exc), "message": "Workflow validation failed"},
            expected_lease_owner=lease_owner,
            clear_lease=True,
            recovery_state="validation_failed",
        )
        _stop_heartbeat(heartbeat_stop, heartbeat_thread)
        return

    ordered_steps = sorted(config.get("steps") or [], key=lambda step: step.get("order", 0))
    total_steps = len(ordered_steps)
    cisiv_stage = normalize_cisiv_stage(
        existing_run.get("cisiv_stage") or workflow.get("cisiv_stage"),
        default="implementation",
    )

    workflow_name = config.get("name") or workflow["name"]
    current_data = trigger_data or {"text": "Manual queued run", "source": "builder"}
    completed_steps: list[dict] = []
    planned_steps = _normalize_planned_steps(ordered_steps, None, cisiv_stage=cisiv_stage)
    next_step_index = 0
    started_at = now_iso()
    ledger: list[dict] = []

    if resume:
        output = existing_run.get("output") or {}
        current_data = output.get("currentData", current_data)
        completed_steps = _normalize_completed_steps(
            output.get("completedSteps") or output.get("steps"),
            cisiv_stage=cisiv_stage,
        )
        planned_steps = _normalize_planned_steps(
            ordered_steps,
            deepcopy(output.get("plannedSteps") or []),
            cisiv_stage=cisiv_stage,
        )
        next_step_index = _resolve_next_step_index(planned_steps, output.get("nextStepIndex"))
        started_at = output.get("startedAt") or started_at
        ledger = _normalize_ledger(output.get("ledger"))

    base_output = _build_output(
        workflow_name,
        config.get("trigger"),
        total_steps,
        planned_steps,
        completed_steps,
        current_data,
        started_at,
        ledger=ledger,
        cisiv_stage=cisiv_stage,
        currentStep=min(next_step_index, total_steps),
        currentStepLabel=None,
        nextStepIndex=next_step_index,
        message="Workflow is running",
    )
    base_output = _append_ledger(
        base_output,
        "running",
        "Workflow execution started." if not resume else "Workflow execution resumed.",
        cisiv_stage=cisiv_stage,
        resume=resume,
    )
    ledger = _normalize_ledger(base_output.get("ledger"))
    if not update_workflow_run(
        workflow_run_id,
        status="running",
        output=base_output,
        expected_lease_owner=lease_owner,
        recovery_state="resumed" if resume else "active",
        stale_reason=None,
    ):
        _stop_heartbeat(heartbeat_stop, heartbeat_thread)
        return

    for index in range(next_step_index, len(ordered_steps)):
        step = ordered_steps[index]
        approval = get_latest_workflow_approval_for_step(workflow_run_id, step["id"])

        if is_risky_step(step) and (not approval or approval["status"] == "pending"):
            if not approval:
                create_workflow_approval(
                    workflow_run_id=workflow_run_id,
                    workflow_id=workflow_id,
                    step_id=step["id"],
                    step_label=step["label"],
                    step_type=step["type"],
                    reason=risk_reason(step),
                    payload={"step": step, "currentData": current_data, "cisiv_stage": cisiv_stage},
                    cisiv_stage=cisiv_stage,
                )

            planned_steps[index] = {
                **planned_steps[index],
                "status": "awaiting_approval",
                "output": None,
                "error": None,
                "resultRef": None,
            }
            paused_output = _build_output(
                workflow_name,
                config.get("trigger"),
                total_steps,
                planned_steps,
                completed_steps,
                current_data,
                started_at,
                ledger=ledger,
                cisiv_stage=cisiv_stage,
                currentStep=index + 1,
                currentStepLabel=step["label"],
                nextStepIndex=index,
                message=f"Paused for approval: {step['label']}",
            )
            paused_output = _append_ledger(
                paused_output,
                "awaiting_approval",
                f"Workflow paused for approval on step: {step['label']}",
                cisiv_stage=cisiv_stage,
                stepId=step["id"],
            )
            ledger = _normalize_ledger(paused_output.get("ledger"))
            update_workflow_run(
                workflow_run_id,
                status="awaiting_approval",
                output=paused_output,
                expected_lease_owner=lease_owner,
                clear_lease=True,
                recovery_state=None,
                stale_reason=None,
            )
            _stop_heartbeat(heartbeat_stop, heartbeat_thread)
            return

        if approval and approval["status"] == "rejected":
            planned_steps[index] = {
                **planned_steps[index],
                "status": "failed",
                "output": None,
                "error": f"Approval rejected for step: {step['label']}",
            }
            failure_output = _build_output(
                workflow_name,
                config.get("trigger"),
                total_steps,
                planned_steps,
                completed_steps,
                current_data,
                started_at,
                ledger=ledger,
                cisiv_stage=cisiv_stage,
                currentStep=index + 1,
                currentStepLabel=step["label"],
                nextStepIndex=index,
                error=f"Approval rejected for step: {step['label']}",
                message=f"Approval rejected for step: {step['label']}",
                failedAt=now_iso(),
            )
            failure_output = _append_ledger(
                failure_output,
                "failed",
                f"Approval rejected for step: {step['label']}",
                cisiv_stage=cisiv_stage,
                stepId=step["id"],
            )
            ledger = _normalize_ledger(failure_output.get("ledger"))
            update_workflow_run(
                workflow_run_id,
                status="failed",
                output=failure_output,
                expected_lease_owner=lease_owner,
                clear_lease=True,
                recovery_state="rejected",
            )
            _stop_heartbeat(heartbeat_stop, heartbeat_thread)
            return

        step_attempt = int(planned_steps[index].get("attempt") or 0) + 1
        planned_steps[index] = {
            **planned_steps[index],
            "status": "running",
            "output": None,
            "error": None,
                "attempt": step_attempt,
                "startedAt": now_iso(),
                "completedAt": None,
                "resultRef": None,
                "cisiv_stage": cisiv_stage,
            }
        running_output = _build_output(
            workflow_name,
            config.get("trigger"),
            total_steps,
            planned_steps,
            completed_steps,
            current_data,
            started_at,
            ledger=ledger,
            cisiv_stage=cisiv_stage,
            currentStep=index + 1,
            currentStepLabel=step["label"],
            nextStepIndex=index,
            message=f"Running step {index + 1} of {total_steps}",
        )
        running_output = _append_ledger(
            running_output,
            "step_started",
            f"Started step {index + 1}: {step['label']}",
            cisiv_stage=cisiv_stage,
            stepId=step["id"],
            attempt=step_attempt,
        )
        ledger = _normalize_ledger(running_output.get("ledger"))
        if not update_workflow_run(
            workflow_run_id,
            status="running",
            output=running_output,
            expected_lease_owner=lease_owner,
            recovery_state="active",
        ):
            _stop_heartbeat(heartbeat_stop, heartbeat_thread)
            return

        try:
            result = run_workflow_step(step, current_data)
            result_ref = f"{step['id']}:attempt:{step_attempt}"
            step_result = {
                "stepId": result["step_id"],
                "label": result["label"],
                "type": result["type"],
                "cisiv_stage": cisiv_stage,
                "ok": bool(result["ok"]),
                "output": result["output"],
                "data": result["data"],
                "attempt": step_attempt,
                "resultRef": result_ref,
            }
            completed_steps = [existing for existing in completed_steps if existing.get("stepId") != step_result["stepId"]]
            completed_steps.append(step_result)
            current_data = result["data"]
            planned_steps[index] = {
                **planned_steps[index],
                "status": "completed" if result["ok"] else "failed",
                "output": result["output"],
                "error": None if result["ok"] else result["output"],
                "completedAt": now_iso(),
                "resultRef": result_ref,
            }

            step_output = _build_output(
                workflow_name,
                config.get("trigger"),
                total_steps,
                planned_steps,
                completed_steps,
                current_data,
                started_at,
                ledger=ledger,
                cisiv_stage=cisiv_stage,
                currentStep=index + 1,
                currentStepLabel=step["label"],
                nextStepIndex=index + 1 if result["ok"] else index,
                latestStep=step_result,
                message=f"Completed step {index + 1} of {total_steps}" if result["ok"] else f"Step {index + 1} failed",
            )
            step_output = _append_ledger(
                step_output,
                "step_completed" if result["ok"] else "step_failed",
                result["output"],
                cisiv_stage=cisiv_stage,
                stepId=step["id"],
                attempt=step_attempt,
                resultRef=result_ref,
            )
            ledger = _normalize_ledger(step_output.get("ledger"))
            if not update_workflow_run(
                workflow_run_id,
                status="running" if result["ok"] else "failed",
                output=step_output,
                expected_lease_owner=lease_owner,
                recovery_state="active" if result["ok"] else "failed",
                clear_lease=not result["ok"],
            ):
                _stop_heartbeat(heartbeat_stop, heartbeat_thread)
                return

            if not result["ok"]:
                raise RuntimeError(result["output"] or f"Step failed: {step['label']}")

            if result["type"].startswith("condition.") and not bool(result["data"].get("passed", True)):
                condition_output = _build_output(
                    workflow_name,
                    config.get("trigger"),
                    total_steps,
                    planned_steps,
                    completed_steps,
                    current_data,
                    started_at,
                    ledger=ledger,
                    cisiv_stage=cisiv_stage,
                    currentStep=index + 1,
                    currentStepLabel=None,
                    nextStepIndex=index + 1,
                    finalOutput=current_data,
                    summary=f"Workflow stopped at condition: {step['label']}.",
                    message=f"Condition stopped the workflow at step {index + 1}.",
                    completedAt=now_iso(),
                )
                condition_output = _append_ledger(
                    condition_output,
                    "completed",
                    f"Workflow completed early because condition '{step['label']}' stopped the run.",
                    cisiv_stage=cisiv_stage,
                    stepId=step["id"],
                )
                ledger = _normalize_ledger(condition_output.get("ledger"))
                update_workflow_run(
                    workflow_run_id,
                    status="completed",
                    output=condition_output,
                    expected_lease_owner=lease_owner,
                    clear_lease=True,
                    recovery_state="completed",
                    stale_reason=None,
                )
                _stop_heartbeat(heartbeat_stop, heartbeat_thread)
                return
        except Exception as exc:
            planned_steps[index] = {
                **planned_steps[index],
                "status": "failed",
                "output": None,
                "error": str(exc),
                "completedAt": None,
                "resultRef": None,
            }
            failure_output = _build_output(
                workflow_name,
                config.get("trigger"),
                total_steps,
                planned_steps,
                completed_steps,
                current_data,
                started_at,
                ledger=ledger,
                cisiv_stage=cisiv_stage,
                currentStep=index + 1,
                currentStepLabel=step["label"],
                nextStepIndex=index,
                error=str(exc),
                message=f"Step {index + 1} failed",
                failedAt=now_iso(),
            )
            failure_output = _append_ledger(
                failure_output,
                "failed",
                f"Workflow failed on step: {step['label']}",
                cisiv_stage=cisiv_stage,
                stepId=step["id"],
                attempt=step_attempt,
                error=str(exc),
            )
            ledger = _normalize_ledger(failure_output.get("ledger"))
            update_workflow_run(
                workflow_run_id,
                status="failed",
                output=failure_output,
                expected_lease_owner=lease_owner,
                clear_lease=True,
                recovery_state="failed",
            )
            _stop_heartbeat(heartbeat_stop, heartbeat_thread)
            raise

    completed_output = _build_output(
        workflow_name,
        config.get("trigger"),
        total_steps,
        planned_steps,
        completed_steps,
        current_data,
        started_at,
        ledger=ledger,
        cisiv_stage=cisiv_stage,
        currentStep=total_steps,
        currentStepLabel=None,
        nextStepIndex=total_steps,
        finalOutput=current_data,
        summary=f"Executed {len(completed_steps)} step(s).",
        completedAt=now_iso(),
    )
    completed_output = _append_ledger(
        completed_output,
        "completed",
        f"Workflow completed after executing {len(completed_steps)} step(s).",
        cisiv_stage=cisiv_stage,
    )
    ledger = _normalize_ledger(completed_output.get("ledger"))
    update_workflow_run(
        workflow_run_id,
        status="completed",
        output=completed_output,
        expected_lease_owner=lease_owner,
        clear_lease=True,
        recovery_state="completed",
        stale_reason=None,
    )
    _stop_heartbeat(heartbeat_stop, heartbeat_thread)
