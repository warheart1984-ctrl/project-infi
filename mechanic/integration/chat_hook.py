"""MECH-CHAT-01 — enforce MECHANIC_RUNTIME_PROFILE before chat turn actuation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mechanic.runtime.enforcer import EnforcementViolation, enforce_turn_request, load_runtime_profile


def mechanic_enforcement_enabled() -> bool:
    return os.environ.get("MECHANIC_ENFORCE_PROFILE", "").strip() == "1"


def resolve_mechanic_case_id() -> str:
    return os.environ.get("MECHANIC_CASE_ID", "").strip()


def resolve_runtime_profile_path(case_id: str, *, runtime_root: Path | None = None) -> Path:
    root = runtime_root or Path(".runtime/mechanic")
    return root / case_id / "MECHANIC_RUNTIME_PROFILE.json"


def enforce_chat_turn_request(
    *,
    action: str = "propose",
    model_calls_this_turn: int = 0,
    audit_fields: dict[str, Any] | None = None,
    runtime_root: Path | None = None,
    case_id: str | None = None,
    force_enforcement: bool = False,
) -> dict[str, Any] | None:
    """Return governed error payload on violation, or None when admitted / disabled."""
    if not force_enforcement and not mechanic_enforcement_enabled():
        return None
    case_id = str(case_id or resolve_mechanic_case_id()).strip()
    if not case_id:
        return _error_payload(
            code="GOV-01",
            message="MECHANIC_ENFORCE_PROFILE=1 requires MECHANIC_CASE_ID",
            status_code=403,
        )
    profile_path = resolve_runtime_profile_path(case_id, runtime_root=runtime_root)
    if not profile_path.is_file():
        return _error_payload(
            code="GOV-12",
            message=f"MECHANIC_RUNTIME_PROFILE not found for case {case_id}",
            status_code=403,
            evidence={"profile_path": str(profile_path)},
        )
    try:
        profile = load_runtime_profile(profile_path)
        fields = dict(audit_fields or {})
        fields.setdefault("case_id", case_id)
        enforce_turn_request(
            profile,
            action=action,
            model_calls_this_turn=model_calls_this_turn,
            audit_fields=fields,
        )
    except EnforcementViolation as exc:
        return _error_payload(
            code=exc.code,
            message=exc.message,
            status_code=403,
            evidence=exc.evidence,
        )
    except (OSError, ValueError) as exc:
        return _error_payload(
            code="GOV-12",
            message=f"invalid MECHANIC_RUNTIME_PROFILE: {exc}",
            status_code=403,
        )
    return None


def slingshot_enforcement_for_case(case_id: str, *, session_id: str) -> dict[str, Any] | None:
    """Force Mechanic profile enforcement for an active slingshot session."""
    return enforce_chat_turn_request(
        action="propose",
        model_calls_this_turn=0,
        audit_fields={"trace_id": session_id, "case_id": case_id},
        case_id=case_id,
        force_enforcement=True,
    )


def _error_payload(
    *,
    code: str,
    message: str,
    status_code: int,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": message,
        "mechanic_enforcement": {
            "blocked": True,
            "code": code,
            "message": message,
            "status_code": status_code,
            "evidence": dict(evidence or {}),
            "claim_label": "proven",
        },
        "status_code": status_code,
    }
