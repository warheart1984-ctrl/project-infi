"""Read-only OTEM v2-v5 enrichment helpers.

These helpers keep OTEM inside Jarvis authority while adding:
- v2 execution-aware recommendations
- v3 workflow handoff proposals
- v4 session-scoped task continuity
- v5 tool-aware, tool-cold suggestions

Everything here is proposal-only. No execution, workflow creation, approval
mutation, run creation, or durable memory writes are allowed.
"""

# Mythic: Otem Runtime
# Engineering: OtemRuntimeEngine
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import re
from typing import Any

OTEM_VERSION = "v5_frozen"


def get_frozen_otem_version() -> str:
    version = str(OTEM_VERSION or "").strip()
    assert version == "v5_frozen", f"Unexpected OTEM runtime version: {version!r}"
    return version


FOCUS_STEP_RE = re.compile(r"\b(?:focus on|zoom into|drill into)\s+step\s+(\d+)\b", re.IGNORECASE)
SHOW_PLAN_PATTERNS = (
    "show plan",
    "show the plan",
    "show current plan",
    "show current task",
)
END_TASK_PATTERNS = (
    "end task",
    "end the task",
    "clear otem",
    "stop otem",
    "close otem",
)
REFINE_PATTERNS = (
    "refine",
    "revise",
    "adjust plan",
    "update task",
    "narrow task",
)
WORKFLOW_SIGNAL_TERMS = (
    "workflow",
    "pipeline",
    "automation",
    "automate",
    "when ",
    "whenever",
    "every ",
    "daily",
    "weekly",
    "incoming email",
    "incoming webhook",
    "slack",
    "email",
    "webhook",
    "schedule",
)
TOOL_PROPOSAL_HINTS = {
    "git_status": {
        "terms": ("git", "branch", "repo status", "changes", "working tree"),
        "reason": "Use Git Status when the task depends on current branch or workspace change visibility.",
        "proposed_args": {},
    },
    "run_pytest": {
        "terms": ("pytest", "tests", "test suite", "failing test", "backend failure", "traceback"),
        "reason": "Run Pytest is the safest verification proposal for backend or test-failure work.",
        "proposed_args": {},
    },
    "build_frontend": {
        "terms": ("frontend", "ui", "browser", "build", "bundle", "react"),
        "reason": "Build Frontend is the safest proposal when UI or bundling integrity matters.",
        "proposed_args": {},
    },
    "spatial_reason": {
        "terms": ("layout", "position", "visibility", "space", "map", "distance"),
        "reason": "Spatial Reason fits tasks that depend on layout, visibility, or relational geometry.",
        "proposed_args": {"mode": "build"},
    },
}
SPECIAL_TOOL_REGISTRY = (
    {
        "id": "spatial_reason",
        "label": "Spatial Reason",
        "type": "tool",
        "capabilities": [
            "build bounded spatial graphs",
            "reason about visibility and proximity",
        ],
        "constraints": [
            "proposal only in OTEM v5",
            "no direct tool execution",
        ],
    },
    {
        "id": "mystic_reading",
        "label": "Mystic Reading",
        "type": "tool",
        "capabilities": [
            "symbolic reading",
            "reflective framing",
        ],
        "constraints": [
            "proposal only in OTEM v5",
            "not appropriate for operator-state execution",
        ],
    },
    {
        "id": "v9_core",
        "label": "V9 Core",
        "type": "runtime",
        "capabilities": [
            "creative scene drafting",
            "bounded runtime event logging",
        ],
        "constraints": [
            "proposal only in OTEM v5",
            "not used for OTEM execution",
        ],
    },
    {
        "id": "v10_core",
        "label": "V10 Core",
        "type": "runtime",
        "capabilities": [
            "scene briefing and critic pass",
            "bounded runtime event logging",
        ],
        "constraints": [
            "proposal only in OTEM v5",
            "not used for OTEM execution",
        ],
    },
)


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _clip_text(value: Any, limit: int = 180) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def load_workflow_template_catalog(limit: int = 6) -> list[dict[str, Any]]:
    """Expose workflow templates as a read-only catalog for OTEM handoff decisions."""
    try:
        from app.workflow_templates import WORKFLOW_TEMPLATES
    except Exception:
        return []

    catalog: list[dict[str, Any]] = []
    for template in list(WORKFLOW_TEMPLATES or [])[: max(1, min(int(limit or 6), 12))]:
        integrations = [str(item).strip() for item in list(template.get("integrations") or []) if str(item).strip()]
        capabilities = []
        if "email" in integrations:
            capabilities.append("email-triggered flow")
        if "slack" in integrations:
            capabilities.append("slack delivery or alerting")
        if "api" in integrations:
            capabilities.append("webhook or API intake")
        if "schedules" in integrations:
            capabilities.append("scheduled execution")
        if not capabilities:
            capabilities.append("structured workflow handoff")
        catalog.append(
            {
                "id": str(template.get("id") or "").strip(),
                "name": str(template.get("name") or "").strip(),
                "description": _clip_text(template.get("description"), limit=220),
                "category": str(template.get("category") or "general").strip() or "general",
                "difficulty": str(template.get("difficulty") or "unknown").strip() or "unknown",
                "integrations": integrations,
                "capabilities": capabilities,
            }
        )
    return [item for item in catalog if item.get("id") and item.get("name")]


def build_tool_registry(actions: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Build a read-only OTEM tool registry from Jarvis actions plus bounded tools."""
    registry: list[dict[str, Any]] = []
    seen: set[str] = set()

    for action in list(actions or []):
        action_id = str(action.get("id") or "").strip()
        if not action_id or action_id in seen:
            continue
        seen.add(action_id)
        constraints = ["proposal only in OTEM v5"]
        if action.get("requires_approval"):
            constraints.append("operator approval required before execution")
        registry.append(
            {
                "id": action_id,
                "label": str(action.get("label") or action_id).strip(),
                "type": "local_action",
                "capabilities": [_clip_text(action.get("description"), limit=140)],
                "constraints": constraints,
            }
        )

    for tool in SPECIAL_TOOL_REGISTRY:
        if tool["id"] in seen:
            continue
        seen.add(tool["id"])
        registry.append(dict(tool))

    return registry


def classify_otem_operation(user_input: str, prior_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve the session-scoped OTEM operation for this turn."""
    lower = _normalize_text(user_input)
    prior_state = dict(prior_state or {})
    for pattern in END_TASK_PATTERNS:
        if pattern in lower:
            return {"operation": "end_task", "matched": pattern}

    focus_match = FOCUS_STEP_RE.search(lower)
    if focus_match:
        return {
            "operation": "focus_step",
            "matched": focus_match.group(0),
            "step_index": max(1, int(focus_match.group(1))),
        }

    for pattern in SHOW_PLAN_PATTERNS:
        if pattern in lower:
            return {"operation": "show_plan", "matched": pattern}

    if prior_state:
        for pattern in REFINE_PATTERNS:
            if pattern in lower:
                return {"operation": "refine_task", "matched": pattern}

    return {"operation": "new_task", "matched": None}


def build_session_context(
    base_result: dict[str, Any],
    *,
    prior_state: dict[str, Any] | None = None,
    operation_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build OTEM v4 session continuity without persisting outside the session."""
    prior_state = dict(prior_state or {})
    operation_info = dict(operation_info or {})
    operation = str(operation_info.get("operation") or "new_task").strip() or "new_task"
    prior_plan = [dict(step or {}) for step in list(prior_state.get("plan") or [])]

    use_prior = operation in {"show_plan", "focus_step", "end_task"} and bool(prior_plan)
    task = str((prior_state if use_prior else base_result).get("task") or "").strip()
    restated_task = str((prior_state if use_prior else base_result).get("restated_task") or "").strip()
    plan = [dict(step or {}) for step in list((prior_state if use_prior else base_result).get("plan") or [])]

    if not plan:
        plan = [dict(step or {}) for step in list(base_result.get("plan") or [])]
    if not task:
        task = str(base_result.get("task") or "").strip()
    if not restated_task:
        restated_task = str(base_result.get("restated_task") or "").strip()

    requested_focus = int(operation_info.get("step_index") or 0)
    prior_focus = int(prior_state.get("focus_step_index") or 0)
    focus_step_index = requested_focus or prior_focus or (int(plan[0].get("index") or 1) if plan else 0)
    focus_step = next(
        (dict(step) for step in plan if int(step.get("index") or 0) == focus_step_index),
        dict(plan[0]) if plan else {},
    )
    if focus_step and not focus_step_index:
        focus_step_index = int(focus_step.get("index") or 1)

    active = operation != "end_task"
    if operation == "focus_step" and prior_plan:
        note = f"OTEM kept the current task thread and zoomed into step {focus_step_index}."
    elif operation == "show_plan" and prior_plan:
        note = "OTEM kept the current task thread and replayed the active plan."
    elif operation == "end_task" and prior_plan:
        note = "OTEM closed the active task thread. The plan remains visible for this turn, but no OTEM task is left active."
    elif operation == "end_task":
        note = "No active OTEM task was present to close, so Jarvis ended the request without carrying a task forward."
    elif operation == "refine_task" and prior_state:
        note = "OTEM refined the existing task thread and rebuilt the plan inside the same session."
    elif prior_state:
        note = "OTEM started a fresh task thread and replaced the previous OTEM session context."
    else:
        note = "OTEM opened a session-scoped task thread for this request."

    return {
        "active": active,
        "operation": operation,
        "task": task,
        "restated_task": restated_task,
        "plan": plan,
        "focus_step_index": focus_step_index or None,
        "focus_step": focus_step or None,
        "note": note,
        "session_scoped": True,
        "persistent": False,
    }


def _score_workflow_template(restated_task: str, template: dict[str, Any]) -> int:
    lower = _normalize_text(restated_task)
    score = 0
    integrations = {item.lower() for item in list(template.get("integrations") or [])}
    category = str(template.get("category") or "").strip().lower()

    if "email" in lower and "email" in integrations:
        score += 3
    if "slack" in lower and "slack" in integrations:
        score += 3
    if any(token in lower for token in ("webhook", "api", "endpoint")) and "api" in integrations:
        score += 3
    if any(token in lower for token in ("daily", "weekly", "schedule", "brief")) and "schedules" in integrations:
        score += 3
    if category and category in lower:
        score += 1
    if any(signal in lower for signal in WORKFLOW_SIGNAL_TERMS):
        score += 1
    return score


def build_workflow_handoff(
    restated_task: str,
    workflow_templates: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Build the OTEM v3 workflow handoff object without creating a workflow."""
    templates = [dict(template or {}) for template in list(workflow_templates or [])]
    if not templates:
        return None

    best_template = None
    best_score = 0
    for template in templates:
        score = _score_workflow_template(restated_task, template)
        if score > best_score:
            best_template = template
            best_score = score

    if not best_template or best_score < 3:
        return None

    template_name = best_template.get("name") or best_template.get("id")
    return {
        "workflow_template_id": best_template.get("id"),
        "template_name": template_name,
        "suggested_inputs": {
            "goal": _clip_text(restated_task, limit=220),
            "source": "otem_v3_handoff",
        },
        "rationale": (
            f"This task matches the {template_name} workflow shape and is better treated as an operator-confirmed workflow handoff than a one-turn reply."
        ),
        "ui_affordance": {
            "label": "Create workflow from OTEM suggestion",
            "path": "/workflows/templates",
            "template_id": best_template.get("id"),
        },
        "proposal_only": True,
        "operator_confirmation_required": True,
    }


def _summarize_recent_runs(runs: list[dict[str, Any]] | None, limit: int = 5) -> list[dict[str, Any]]:
    items = []
    for run in list(runs or [])[: max(1, min(int(limit or 5), 8))]:
        items.append(
            {
                "id": run.get("id"),
                "title": run.get("title"),
                "kind": run.get("kind"),
                "status": run.get("status"),
                "updated_at": run.get("updated_at"),
                "summary": _clip_text(run.get("summary"), limit=160),
            }
        )
    return items


def build_execution_awareness(
    restated_task: str,
    *,
    workflow_templates: list[dict[str, Any]] | None,
    recent_runs: list[dict[str, Any]] | None,
    approval_state: dict[str, Any] | None,
    workflow_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build OTEM v2 execution-aware context without mutating runtime state."""
    templates = [dict(template or {}) for template in list(workflow_templates or [])]
    summarized_runs = _summarize_recent_runs(recent_runs)
    approval_state = dict(approval_state or {})

    recommendations: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    if workflow_handoff:
        recommendations.append(
            {
                "kind": "workflow_handoff",
                "label": f"Create workflow from {workflow_handoff.get('template_name') or workflow_handoff.get('workflow_template_id')}",
                "rationale": workflow_handoff.get("rationale"),
                "proposal_only": True,
                "operator_confirmation_required": True,
                "workflow_template_id": workflow_handoff.get("workflow_template_id"),
            }
        )

    pending_action = dict(approval_state.get("pending_action") or {})
    if pending_action:
        action_label = pending_action.get("label") or pending_action.get("id") or "pending action"
        conflicts.append(
            {
                "code": "pending_approval",
                "detail": f"Current session already has {action_label} waiting on approval.",
            }
        )
        recommendations.append(
            {
                "kind": "approval_lane",
                "label": f"Send this through approvals around {action_label}",
                "rationale": "This session already has approval-gated operator work in flight, so OTEM should route the next move through approvals instead of acting directly.",
                "proposal_only": True,
                "operator_confirmation_required": True,
            }
        )

    open_run = next((run for run in summarized_runs if str(run.get("status") or "") == "open"), None)
    if open_run:
        recommendations.append(
            {
                "kind": "resume_run",
                "label": f"Resume run {open_run.get('title') or open_run.get('id')}",
                "rationale": "An open run already exists in the current execution history, so resuming or inspecting it is safer than starting a new action lane.",
                "proposal_only": True,
                "operator_confirmation_required": True,
                "run_id": open_run.get("id"),
            }
        )

    return {
        "workflow_catalog": {
            "count": len(templates),
            "templates": templates[:4],
            "read_only": True,
        },
        "recent_runs": summarized_runs,
        "approval_state": {
            "pending": bool(pending_action),
            "pending_action": pending_action,
            "action_lifecycle": dict(approval_state.get("action_lifecycle") or {}),
            "read_only": True,
        },
        "recommendations": recommendations[:3],
        "conflicts": conflicts,
        "summary": "OTEM read workflow, run, and approval state without mutating any execution surface.",
    }


def build_tool_awareness(
    restated_task: str,
    *,
    tool_registry: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Build OTEM v5 tool-awareness without calling tools."""
    lower = _normalize_text(restated_task)
    registry = [dict(tool or {}) for tool in list(tool_registry or [])]
    suggestions: list[dict[str, Any]] = []

    for tool in registry:
        tool_id = str(tool.get("id") or "").strip()
        if not tool_id:
            continue
        hint = TOOL_PROPOSAL_HINTS.get(tool_id)
        if not hint:
            continue
        if not any(term in lower for term in hint["terms"]):
            continue
        suggestions.append(
            {
                "tool_id": tool_id,
                "label": tool.get("label") or tool_id,
                "reason": hint["reason"],
                "proposed_args": dict(hint["proposed_args"]),
                "proposal_only": True,
                "operator_confirmation_required": True,
            }
        )

    return {
        "registry": registry,
        "suggestions": suggestions[:3],
        "coverage": "matched" if suggestions else "no_match",
        "summary": (
            "OTEM matched the task against the read-only tool registry and produced proposal-only tool suggestions."
            if suggestions
            else "OTEM reviewed the read-only tool registry and did not find a strong tool match for this task."
        ),
    }


def build_otem_catalog_snapshot(actions: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Build the read-only OTEM catalog for operator UI surfaces."""
    workflow_templates = load_workflow_template_catalog()
    tool_registry = build_tool_registry(actions)
    return _wrap_ul_payload({
        "version_ceiling": get_frozen_otem_version(),
        "workflow_catalog": workflow_templates,
        "tool_registry": tool_registry,
        "execution_boundaries": [
            "proposal only",
            "no workflow creation",
            "no run execution",
            "no tool execution",
            "session-scoped only",
        ],
    })


def enrich_otem_result(
    base_result: dict[str, Any],
    *,
    workflow_templates: list[dict[str, Any]] | None,
    tool_registry: list[dict[str, Any]] | None,
    recent_runs: list[dict[str, Any]] | None,
    approval_state: dict[str, Any] | None,
    prior_state: dict[str, Any] | None = None,
    operation_info: dict[str, Any] | None = None,
    session_bound: bool = False,
) -> dict[str, Any]:
    """Add OTEM v2-v5 read-only context to the deterministic OTEM core result."""
    result = dict(base_result or {})
    session_context = build_session_context(
        result,
        prior_state=prior_state,
        operation_info=operation_info,
    )
    workflow_handoff = build_workflow_handoff(
        session_context.get("restated_task") or result.get("restated_task") or result.get("task"),
        workflow_templates,
    )
    execution_awareness = build_execution_awareness(
        session_context.get("restated_task") or result.get("restated_task") or result.get("task"),
        workflow_templates=workflow_templates,
        recent_runs=recent_runs,
        approval_state=approval_state,
        workflow_handoff=workflow_handoff,
    )
    tool_awareness = build_tool_awareness(
        session_context.get("restated_task") or result.get("restated_task") or result.get("task"),
        tool_registry=tool_registry,
    )

    operation = str((operation_info or {}).get("operation") or session_context.get("operation") or "new_task")
    result.update(
        {
            "version": get_frozen_otem_version(),
            "phase": "tool_aware_tool_cold",
            "status": "active" if session_bound and session_context.get("active") else "complete",
            "session_scoped": True,
            "persistent": False,
            "scope": "session" if session_bound else "turn",
            "operation": operation,
            "task": session_context.get("task") or result.get("task"),
            "restated_task": session_context.get("restated_task") or result.get("restated_task"),
            "plan": [dict(step or {}) for step in list(session_context.get("plan") or result.get("plan") or [])],
            "session_context": session_context,
            "execution_awareness": execution_awareness,
            "workflow_handoff": workflow_handoff,
            "tool_awareness": tool_awareness,
        }
    )
    return _wrap_ul_payload(result)
