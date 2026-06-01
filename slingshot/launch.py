"""Phase 3 — Launch: turn admission and compose configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from slingshot.common import DEFAULT_MECHANIC_ROOT, DEFAULT_SLINGSHOT_ROOT
from slingshot.frame import load_slingshot_frame
from slingshot.packet import ensure_packet_for_case, load_slingshot_packet, packet_is_expired


def resolve_slingshot_turn_config(session_metadata: dict[str, Any]) -> dict[str, Any] | None:
    """Return slingshot compose hints when session is in active non-escalated slingshot mode."""
    slingshot = session_metadata.get("slingshot") or {}
    if not slingshot.get("active"):
        return None
    if str(slingshot.get("status") or "") == "escalated":
        return None
    packet = slingshot.get("packet") or {}
    return {
        "compose_mode": str(packet.get("compose_mode") or "fast"),
        "cortex_fast_path": bool(packet.get("cortex_fast_path", True)),
        "cognitive_runtime": True,
        "runtime_context": "jarvis_operator_live",
        "packet_type": "operator_turn",
    }


def _error_payload(
    *,
    code: str,
    message: str,
    status_code: int = 403,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": message,
        "slingshot": {
            "blocked": True,
            "code": code,
            "message": message,
            "status_code": status_code,
            "evidence": dict(evidence or {}),
            "claim_label": "proven",
        },
        "status_code": status_code,
    }


def admit_slingshot_turn(
    session,
    slingshot_payload: dict[str, Any],
    *,
    session_id: str,
    slingshot_root: Path | None = None,
    mechanic_root: Path | None = None,
) -> dict[str, Any] | None:
    """
    Validate slingshot admission for a chat turn.
    Returns error payload on denial, or None when admitted.
    """
    if not isinstance(slingshot_payload, dict) or not slingshot_payload:
        return None

    case_id = str(slingshot_payload.get("case_id") or "").strip()
    if not case_id:
        return _error_payload(code="GOV-01", message="slingshot.case_id is required")

    metadata = getattr(session, "metadata", None) or {}
    pending = metadata.get("pending_action") or {}
    if str(pending.get("type") or "") == "slingshot_signoff":
        return _error_payload(
            code="GOV-12",
            message="slingshot launch blocked pending human signoff",
            evidence={"pending_action_id": pending.get("id")},
        )

    shot_root = slingshot_root or DEFAULT_SLINGSHOT_ROOT
    mech_root = mechanic_root or DEFAULT_MECHANIC_ROOT

    try:
        frame = load_slingshot_frame(case_id, runtime_root=shot_root)
    except (OSError, ValueError, FileNotFoundError) as exc:
        return _error_payload(
            code="GOV-12",
            message=f"slingshot frame not found: {exc}",
            evidence={"case_id": case_id},
        )

    operator_intent = {
        "authorized_goals": slingshot_payload.get("authorized_goals") or [],
        "required_constraints": slingshot_payload.get("required_constraints") or [],
    }
    try:
        packet = ensure_packet_for_case(case_id, operator_intent, runtime_root=shot_root)
    except (OSError, ValueError) as exc:
        return _error_payload(code="GOV-12", message=str(exc), evidence={"case_id": case_id})

    if packet_is_expired(packet):
        return _error_payload(
            code="CST-07",
            message="slingshot packet expired; run preload and rebuild packet",
            evidence={"case_id": case_id, "expires_at_utc": packet.get("expires_at_utc")},
        )

    if bool(frame.get("launch_blocked")) or bool(packet.get("launch_blocked")):
        return _error_payload(
            code="RNT-04",
            message="slingshot launch blocked by preload governance frame",
            evidence={
                "case_id": case_id,
                "reasons": frame.get("launch_block_reasons") or [],
            },
        )

    from mechanic.integration.chat_hook import enforce_chat_turn_request

    block = enforce_chat_turn_request(
        action="propose",
        model_calls_this_turn=0,
        audit_fields={"trace_id": session_id, "case_id": case_id},
        runtime_root=mech_root,
        case_id=case_id,
        force_enforcement=True,
    )
    if block is not None:
        block["slingshot"] = {
            **(block.get("slingshot") or block.get("mechanic_enforcement") or {}),
            "phase": "launch",
        }
        return block

    session.metadata["slingshot"] = {
        "active": True,
        "case_id": case_id,
        "status": "active",
        "frame": {"case_id": case_id, "scan_hash": frame.get("scan_hash")},
        "packet": packet,
        "authorized_goals": list(packet.get("authorized_goals") or []),
        "required_constraints": list(packet.get("required_constraints") or []),
    }
    return None
