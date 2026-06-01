"""Bounded anti-drift control for final Jarvis replies.

This module keeps one active thread contract in front of the reply layer so
AAIS can clamp or block visible drift without inventing a second routing
authority.
"""

from __future__ import annotations

import re
from datetime import datetime
from src.datetime_compat import UTC
from typing import Any

from src.jarvis_reasoning_protocol import DIRECT_CHALLENGE_FALLBACK, looks_like_direct_challenge


TRACE_MARKERS = (
    "response trace",
    "think contract",
    "deliberate local",
    "gather -> plan -> answer",
    "memory cues",
    "review matches",
    "council deliberation",
    "bug hunter",
    "attached workspace",
    "attached review",
    "internal trace",
    "internal scaffolding",
)

GENERIC_IDENTITY_MARKERS = (
    "as an ai",
    "i am just an assistant",
    "i'm just a tool",
    "i am just a tool",
    "i can't be a real person",
    "i cant be a real person",
    "i cannot do that",
    "i'm sorry, but",
    "i apologize for the inconvenience",
    "thank you for your patience",
    "how can i assist you today",
)

READY_STANCE_MARKERS = (
    "i'm here to help",
    "what's the issue",
    "what is the issue",
    "let's take a calm, practical approach",
)

EXECUTION_DRIFT_MARKERS = (
    "i ran",
    "i executed",
    "i created the workflow",
    "workflow created",
    "i stored",
    "i merged",
    "i applied",
)

HEADER_RE = re.compile(r"(?mi)^(?:analysis|system|assistant|user|workspace|sources)\s*:")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _resolved_turn_value(primary: Any, secondary: Any, default: str) -> str:
    value = _normalize_text(primary) or _normalize_text(secondary) or default
    return value


def build_thread_contract(
    *,
    session_id: str,
    user_message: str,
    turn_contract: dict[str, Any] | None = None,
    mode_guidance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one canonical thread contract from the active turn truth."""

    turn_contract = dict(turn_contract or {})
    mode_guidance = dict(mode_guidance or {})
    resolved_mode = _resolved_turn_value(
        turn_contract.get("resolved_mode"),
        mode_guidance.get("effective_mode"),
        "operator",
    )
    resolved_scope = _resolved_turn_value(
        turn_contract.get("resolved_scope"),
        mode_guidance.get("resolved_scope"),
        "operator_task",
    )
    resolved_voice = _resolved_turn_value(
        turn_contract.get("resolved_voice"),
        mode_guidance.get("resolved_voice"),
        "jarvis",
    )
    contract_label = _normalize_text(turn_contract.get("contract_label")) or "mode_guidance"
    if looks_like_direct_challenge(user_message):
        contract_label = "direct_challenge"
    purpose = (
        _normalize_text(turn_contract.get("otem_task"))
        or _normalize_text(turn_contract.get("memory_rejection", {}).get("detail"))
        or _normalize_text(user_message)
        or "Respond inside the active operator task."
    )

    mode_map = {
        "debug": "audit",
        "research": "exploratory",
        "tiny": "strict",
        "operator": "standard",
        "think": "strict",
        "fast": "standard",
    }
    contract_mode = mode_map.get(resolved_mode, "standard")

    forbidden_scope = ["internal_trace"]
    if contract_label == "otem":
        forbidden_scope.extend(
            ["workflow_creation", "tool_execution", "memory_write", "run_creation", "persistence"]
        )
    if turn_contract.get("memory_rejection"):
        forbidden_scope.extend(["memory_write", "generic_ready_stance"])

    return {
        "thread_id": session_id,
        "task_id": f"{session_id}:{contract_label or 'turn'}",
        "purpose": purpose,
        "mode": contract_mode,
        "allowed_scope": [resolved_scope],
        "forbidden_scope": forbidden_scope,
        "identity_constraints": {
            "allow_tone_shift": False,
            "allow_mode_shift": False,
            "allow_task_expansion": False,
        },
        "output_constraints": {
            "verbosity": "medium",
            "format": "freeform",
            "must_answer_directly": True,
        },
        "correction_policy": {
            "warn_threshold": 2,
            "clamp_threshold": 3,
            "block_threshold": 4,
        },
        "authority_order": [
            "active_user_instruction",
            "thread_contract",
            "active_task_state",
            "recent_relevant_context",
            "historical_context",
        ],
        "resolved_mode": resolved_mode,
        "resolved_scope": resolved_scope,
        "resolved_voice": resolved_voice,
        "contract_label": contract_label,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _drift_findings(text: str, thread_contract: dict[str, Any]) -> list[dict[str, Any]]:
    lowered = text.lower()
    findings: list[dict[str, Any]] = []

    if any(marker in lowered for marker in TRACE_MARKERS) or HEADER_RE.search(text):
        findings.append(
            {
                "kind": "scope_drift",
                "severity": 3,
                "reason": "internal_scaffolding",
                "detail": "Reply leaked trace or internal scaffolding outside the active thread contract.",
            }
        )

    if any(marker in lowered for marker in GENERIC_IDENTITY_MARKERS):
        findings.append(
            {
                "kind": "identity_drift",
                "severity": 3,
                "reason": "generic_assistant_drift",
                "detail": "Reply drifted into generic assistant language instead of Jarvis voice.",
            }
        )

    if any(marker in lowered for marker in READY_STANCE_MARKERS):
        findings.append(
            {
                "kind": "mode_drift",
                "severity": 3,
                "reason": "ready_stance_softening",
                "detail": "Reply softened into a ready-stance template instead of staying decision-oriented.",
            }
        )

    if thread_contract.get("contract_label") == "otem" and any(
        marker in lowered for marker in EXECUTION_DRIFT_MARKERS
    ):
        findings.append(
            {
                "kind": "scope_drift",
                "severity": 3,
                "reason": "execution_claim_inside_reason_only_lane",
                "detail": "OTEM v5 is proposal-only, but the reply implied execution or persistence.",
            }
        )

    return findings


def _line_contains_any(lowered_line: str, markers: tuple[str, ...]) -> bool:
    return any(marker in lowered_line for marker in markers)


def _clamp_reply(text: str, *, thread_contract: dict[str, Any]) -> str:
    lines = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if HEADER_RE.match(line):
            continue
        lowered = line.lower()
        if _line_contains_any(lowered, TRACE_MARKERS):
            continue
        if _line_contains_any(lowered, GENERIC_IDENTITY_MARKERS):
            continue
        if _line_contains_any(lowered, READY_STANCE_MARKERS):
            continue
        if thread_contract.get("contract_label") == "otem" and _line_contains_any(
            lowered,
            EXECUTION_DRIFT_MARKERS,
        ):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def anti_drift_fallback(thread_contract: dict[str, Any]) -> str:
    """Return a minimal Jarvis-owned fallback for blocked drift."""

    contract_label = _normalize_text(thread_contract.get("contract_label"))
    if contract_label == "direct_challenge":
        return DIRECT_CHALLENGE_FALLBACK
    if contract_label == "otem":
        return "Staying inside the active OTEM contract. I can restate the task and keep the plan proposal-only."
    if contract_label == "memory_governance":
        return "Staying inside the active memory-governance contract. This turn remains decision-oriented and does not change live memory."
    if thread_contract.get("resolved_mode") == "debug":
        return "Staying inside the current debug contract. Point me to the exact mismatch or trace and I'll inspect that only."
    return "Staying inside the active operator contract. State the exact step you want handled next."


def enforce_anti_drift(
    response_text: str,
    *,
    thread_contract: dict[str, Any],
) -> dict[str, Any]:
    """Clamp or block a reply when it drifts beyond the active thread contract."""

    text = str(response_text or "").strip()
    correction_policy = dict(thread_contract.get("correction_policy") or {})
    warn_threshold = int(correction_policy.get("warn_threshold") or 2)
    clamp_threshold = int(correction_policy.get("clamp_threshold") or 3)
    block_threshold = int(correction_policy.get("block_threshold") or 4)

    findings = _drift_findings(text, thread_contract)
    score = sum(int(item.get("severity") or 0) for item in findings)

    if score >= block_threshold:
        status = "blocked"
        final_text = anti_drift_fallback(thread_contract)
    elif score >= clamp_threshold:
        status = "clamped"
        final_text = _clamp_reply(text, thread_contract=thread_contract) or anti_drift_fallback(thread_contract)
    elif score >= warn_threshold:
        status = "warned"
        final_text = text
    else:
        status = "aligned"
        final_text = text

    return {
        "status": status,
        "score": score,
        "findings": findings,
        "thread_contract": dict(thread_contract or {}),
        "final_text": final_text,
        "contained": status in {"blocked", "clamped"},
        "summary": (
            "Anti-drift kept the reply inside the active thread contract."
            if status == "aligned"
            else "Anti-drift corrected drift against the active thread contract."
        ),
    }
