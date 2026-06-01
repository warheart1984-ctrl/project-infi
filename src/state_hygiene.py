"""Shared AAIS state hygiene taxonomy and projection helpers."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from typing import Any


STATE_CLASSES = ("live", "demo", "smoke", "test")
TRUTH_STATUSES = ("canonical", "derived", "reference", "historical")
RETENTION_STATUSES = ("current", "archived", "expired")
TRUTH_SCOPES = ("live", "all")

_NON_LIVE_TEXT_MARKERS = {
    "demo": (
        "browser verification",
        "browser_verify",
        "workbench demo",
        "demo artifact",
        "demo review",
        "wb canonical",
        "wb duplicate",
        "wb why gap",
    ),
    "smoke": (
        "smoke test",
        "smoke artifact",
        "verification run",
    ),
    "test": (
        "test artifact",
        "pytest-temp",
        "fixture seed",
    ),
}

_BADGE_TONES = {
    ("live", "canonical"): "success",
    ("live", "derived"): "info",
    ("live", "reference"): "neutral",
    ("demo", "derived"): "warning",
    ("smoke", "derived"): "warning",
    ("test", "derived"): "warning",
}

_SOURCE_PRECEDENCE = {
    ("memory_override", "canonical"): 100,
    ("memory", "canonical"): 95,
    ("governance_state", "canonical"): 92,
    ("workspace", "canonical"): 88,
    ("workspace", "derived"): 82,
    ("document", "reference"): 76,
    ("document", "derived"): 72,
    ("live_research", "derived"): 68,
    ("doctrine", "reference"): 62,
    ("review", "derived"): 56,
    ("run", "derived"): 48,
    ("governance_event", "historical"): 32,
}


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_state_class(value: Any, default: str = "live") -> str:
    normalized = _normalized_text(value)
    if normalized in STATE_CLASSES:
        return normalized
    return default if default in STATE_CLASSES else "live"


def normalize_truth_status(value: Any, default: str = "derived") -> str:
    normalized = _normalized_text(value)
    if normalized in TRUTH_STATUSES:
        return normalized
    return default if default in TRUTH_STATUSES else "derived"


def normalize_retention_status(value: Any, default: str = "current") -> str:
    normalized = _normalized_text(value)
    if normalized in RETENTION_STATUSES:
        return normalized
    return default if default in RETENTION_STATUSES else "current"


def normalize_truth_scope(value: Any, default: str = "live") -> str:
    normalized = _normalized_text(value)
    if normalized in TRUTH_SCOPES:
        return normalized
    return default if default in TRUTH_SCOPES else "live"


def _joined_record_text(record: dict[str, Any], fields: tuple[str, ...]) -> str:
    parts: list[str] = []
    for field in fields:
        value = record.get(field)
        if isinstance(value, (list, tuple, set)):
            parts.extend(str(item or "") for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item or "") for item in value.values())
        else:
            parts.append(str(value or ""))
    return _normalized_text(" ".join(parts))


def _nested_explicit_value(record: dict[str, Any], key: str) -> str:
    direct = _normalized_text(record.get(key))
    if direct:
        return direct
    for nested_key in ("meta", "details", "patch_plan"):
        nested = record.get(nested_key)
        if isinstance(nested, dict):
            value = _normalized_text(nested.get(key))
            if value:
                return value
    return ""


def _infer_state_class(kind: str, record: dict[str, Any]) -> tuple[str, str]:
    explicit = _nested_explicit_value(record, "state_class")
    if explicit in STATE_CLASSES:
        return explicit, "explicit"

    fields_by_kind = {
        "memory": ("id", "content", "why", "source", "tags", "category"),
        "run": ("id", "title", "summary", "kind", "status", "session_id", "meta"),
        "review": ("id", "goal", "status", "session_id", "patch_plan"),
        "governance_event": ("id", "event_type", "target", "reason", "details", "actor_id"),
        "policy_request": ("id", "title", "status", "submitted_by", "diff_summary"),
    }
    haystack = _joined_record_text(record, fields_by_kind.get(kind, ("id", "title", "summary", "details")))

    for state_class, markers in _NON_LIVE_TEXT_MARKERS.items():
        if any(marker in haystack for marker in markers):
            return state_class, f"inferred_from_{state_class}_markers"

    return "live", "default_live"


def _infer_truth_status(kind: str, record: dict[str, Any], *, retention_status: str) -> tuple[str, str]:
    explicit = _nested_explicit_value(record, "truth_status")
    if explicit in TRUTH_STATUSES:
        return explicit, "explicit"

    if retention_status == "archived":
        return "historical", "archived_record"

    if kind == "memory":
        if bool(record.get("override")) or str(record.get("kind") or "").strip().lower() == "override":
            return "canonical", "override_memory"
        if bool(record.get("active", True)):
            return "canonical", "active_memory"
        return "historical", "inactive_memory"

    if kind == "review":
        decision_state = _normalized_text((record.get("current_decision") or {}).get("state") or record.get("status"))
        if decision_state == "accepted":
            return "canonical", "accepted_review"
        if decision_state in {"rejected", "needs_revision"}:
            return "historical", "closed_review"
        return "derived", "proposal_review"

    if kind == "run":
        return "derived", "run_history"

    if kind == "policy_request":
        status = _normalized_text(record.get("status"))
        if status == "promoted":
            return "canonical", "promoted_policy"
        if status in {"rejected"}:
            return "historical", "rejected_policy"
        return "derived", "policy_request"

    if kind == "governance_event":
        return "historical", "event_history"

    return "derived", "default_derived"


def retention_policy_for(record: dict[str, Any], *, kind: str) -> dict[str, Any]:
    state_class, state_reason = _infer_state_class(kind, record)
    explicit = _normalized_text(record.get("retention_status"))
    if explicit in RETENTION_STATUSES:
        retention_status = explicit
        reason = "explicit"
    else:
        archived_at = str(record.get("archived_at") or "").strip()
        active = bool(record.get("active", True))
        status = _normalized_text(record.get("status"))
        if archived_at or not active:
            retention_status = "archived"
            reason = "archived_record"
        elif kind == "run" and state_class != "live" and status == "open":
            retention_status = "expired"
            reason = "non_live_open_run"
        else:
            retention_status = "current"
            reason = state_reason

    operator_visible = retention_status == "current" and state_class == "live"
    return {
        "retention_status": retention_status,
        "reason": reason,
        "operator_visible": operator_visible,
    }


def badge_for_state(record: dict[str, Any]) -> dict[str, str]:
    state_class = normalize_state_class(record.get("state_class"))
    truth_status = normalize_truth_status(record.get("truth_status"))
    retention_status = normalize_retention_status(record.get("retention_status"))
    if retention_status != "current":
        label = retention_status.title()
        tone = "muted"
    else:
        label = f"{state_class.title()} {truth_status}"
        tone = _BADGE_TONES.get((state_class, truth_status), "neutral")
    return {"label": label, "tone": tone}


def is_operator_visible(record: dict[str, Any], truth_scope: str = "live") -> bool:
    if normalize_truth_scope(truth_scope) == "all":
        return True
    policy = retention_policy_for(record, kind=str(record.get("_state_hygiene_kind") or "record"))
    return bool(policy.get("operator_visible"))


def precedence_rank(source_type: str, truth_status: str) -> int:
    normalized_source = _normalized_text(source_type)
    normalized_truth = normalize_truth_status(truth_status)
    return _SOURCE_PRECEDENCE.get((normalized_source, normalized_truth), 40)


def project_record(
    record: dict[str, Any],
    *,
    kind: str,
    source_type: str | None = None,
) -> dict[str, Any]:
    projected = dict(record or {})
    retention = retention_policy_for(projected, kind=kind)
    state_class, state_reason = _infer_state_class(kind, projected)
    truth_status, truth_reason = _infer_truth_status(
        kind,
        projected,
        retention_status=retention["retention_status"],
    )
    projected["state_class"] = state_class
    projected["truth_status"] = truth_status
    projected["retention_status"] = retention["retention_status"]
    projected["_state_hygiene_kind"] = kind
    projected["state_hygiene"] = {
        "kind": kind,
        "source_type": source_type or kind,
        "state_class": state_class,
        "truth_status": truth_status,
        "retention_status": retention["retention_status"],
        "state_reason": state_reason,
        "truth_reason": truth_reason,
        "retention_reason": retention["reason"],
        "operator_visible": retention["operator_visible"],
        "badge": badge_for_state(
            {
                "state_class": state_class,
                "truth_status": truth_status,
                "retention_status": retention["retention_status"],
            }
        ),
    }
    return projected


def filter_operator_records(records: list[dict[str, Any]], *, truth_scope: str) -> list[dict[str, Any]]:
    scope = normalize_truth_scope(truth_scope)
    return [record for record in records if is_operator_visible(record, truth_scope=scope)]


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "total": len(records),
        "visible": 0,
        "live": 0,
        "demo": 0,
        "smoke": 0,
        "test": 0,
        "current": 0,
        "archived": 0,
        "expired": 0,
    }
    for record in records:
        state_class = normalize_state_class(record.get("state_class"))
        retention_status = normalize_retention_status(record.get("retention_status"))
        counts[state_class] += 1
        counts[retention_status] += 1
        if is_operator_visible(record, truth_scope="live"):
            counts["visible"] += 1
    return counts
