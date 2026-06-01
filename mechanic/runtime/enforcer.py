"""Validate turn/tool requests against MECHANIC_RUNTIME_PROFILE.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EnforcementViolation(Exception):
    def __init__(self, code: str, message: str, evidence: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.evidence = dict(evidence or {})


def load_runtime_profile(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    payload = json.loads(target.read_text(encoding="utf-8"))
    if str(payload.get("profile_version") or "") != "mechanic.runtime_profile.v1":
        raise ValueError("invalid runtime profile version")
    return payload


def enforce_turn_request(
    profile: dict[str, Any],
    *,
    action: str,
    model_calls_this_turn: int = 0,
    audit_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return admission record or raise EnforcementViolation."""
    enforcement = profile.get("enforcement") or {}
    allowed = set(enforcement.get("allowed_action_set") or [])
    blocked = set(enforcement.get("blocked_modes") or [])
    if action in blocked:
        raise EnforcementViolation(
            "RNT-04",
            f"action {action} is blocked by runtime profile",
            {"action": action},
        )
    if allowed and action not in allowed:
        raise EnforcementViolation(
            "GOV-12",
            f"action {action} not in allowed_action_set",
            {"allowed": sorted(allowed)},
        )
    ceiling = (enforcement.get("cost_ceiling") or {}).get("max_model_calls_per_turn")
    if ceiling is not None and model_calls_this_turn > int(ceiling):
        raise EnforcementViolation(
            "CST-07",
            f"model calls {model_calls_this_turn} exceed ceiling {ceiling}",
            {"model_calls_this_turn": model_calls_this_turn},
        )
    required = list(enforcement.get("require_audit_fields") or [])
    audit = dict(audit_fields or {})
    missing = [field for field in required if not str(audit.get(field) or "").strip()]
    if missing:
        raise EnforcementViolation(
            "RNT-11",
            f"missing audit fields: {missing}",
            {"missing": missing},
        )
    return {
        "admitted": True,
        "action": action,
        "case_id": profile.get("case_id"),
        "safety_state": profile.get("safety_state", "dry_run_only"),
    }
