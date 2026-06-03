"""Phase 2 — Tension: compress execution packet from frame + operator intent."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mechanic.hosted.models import SignoffPolicy

from slingshot.common import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_SLINGSHOT_ROOT,
    PACKET_VERSION,
    _slingshot_cache_get,
    _slingshot_cache_put,
    hash_text,
    json_stable,
    packet_path,
    slingshot_json_cache_key,
)
from slingshot.frame import load_slingshot_frame


def _invariant_derived_constraints(drifts: list[dict[str, Any]]) -> list[str]:
    constraints: list[str] = []
    for drift in drifts:
        code = str(drift.get("code") or "")
        ma13 = str(drift.get("ma13_class") or "").upper()
        if ma13 == "III":
            constraints.append(f"block_class_III:{code}")
        if code.startswith("RNT-"):
            constraints.append("no_unbounded_agent_loops")
        if code.startswith("GOV-"):
            constraints.append("require_human_exception_path")
    return sorted(set(constraints))


def _human_control_markers(
    drifts: list[dict[str, Any]],
    *,
    policy: SignoffPolicy | None = None,
) -> list[str]:
    signoff = policy or SignoffPolicy()
    markers: list[str] = []
    for drift in drifts:
        remediation = signoff.remediation_class(drift)
        code = str(drift.get("code") or "")
        if remediation != "observe":
            markers.append(f"{code}:{remediation}")
    markers.append("raw_apply_blocked")
    return sorted(set(markers))


def build_slingshot_packet(
    frame: dict[str, Any],
    operator_intent: dict[str, Any] | None = None,
    *,
    ttl_minutes: int = DEFAULT_PACKET_TTL_MINUTES,
    runtime_root: Path | None = None,
    signoff_policy: SignoffPolicy | None = None,
) -> dict[str, Any]:
    """Build SLINGSHOT_PACKET.v1 from frame and Stage-1 operator intent."""
    intent = dict(operator_intent or {})
    case_id = str(frame.get("case_id") or "")
    if not case_id:
        raise ValueError("frame missing case_id")

    mech_dir = Path(str(frame.get("mechanic_case_dir") or ""))
    scan_path = mech_dir / "mechanic_scan.v1.json"
    drifts: list[dict[str, Any]] = []
    trace_hash = ""
    cost_envelope: dict[str, Any] = {"max_model_calls_per_turn": 3}
    if scan_path.is_file():
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        drifts = list(scan.get("drifts") or [])
    profile_path = mech_dir / "MECHANIC_RUNTIME_PROFILE.json"
    if profile_path.is_file():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        cost_envelope = dict((profile.get("enforcement") or {}).get("cost_ceiling") or cost_envelope)

    authorized_goals = [str(g).strip() for g in (intent.get("authorized_goals") or []) if str(g).strip()]
    if not authorized_goals:
        authorized_goals = ["analyze and propose remediation only"]

    operator_constraints = [str(c).strip() for c in (intent.get("required_constraints") or []) if str(c).strip()]
    derived = _invariant_derived_constraints(drifts)
    required_constraints = sorted(set(operator_constraints + derived + ["no apply", "no repo writes"]))

    expires_at = datetime.utcnow() + timedelta(minutes=max(1, int(ttl_minutes)))
    packet: dict[str, Any] = {
        "packet_version": PACKET_VERSION,
        "case_id": case_id,
        "genome_hash": str(frame.get("genome_hash") or ""),
        "scan_hash": str(frame.get("scan_hash") or ""),
        "compose_mode": "fast",
        "cortex_fast_path": True,
        "authorized_goals": authorized_goals,
        "required_constraints": required_constraints,
        "human_control_markers": _human_control_markers(drifts, policy=signoff_policy),
        "cost_envelope": cost_envelope,
        "trace_bound_context": {"trace_manifest_hash": trace_hash} if trace_hash else {},
        "launch_blocked": bool(frame.get("launch_blocked")),
        "active_invariants": list(frame.get("active_invariants") or []),
        "runtime_profile_path": str(frame.get("runtime_profile_path") or ""),
        "expires_at_utc": expires_at.isoformat() + "Z",
        "claim_label": "asserted",
    }
    packet["packet_hash"] = hash_text(json_stable({k: v for k, v in packet.items() if k != "packet_hash"}))

    target = packet_path(case_id, runtime_root=runtime_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet


def load_slingshot_packet(case_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    path = packet_path(case_id, runtime_root=runtime_root)
    if not path.is_file():
        raise FileNotFoundError(f"SLINGSHOT_PACKET not found for case {case_id}")
    cache_key = slingshot_json_cache_key("packet", path)
    cached = _slingshot_cache_get(cache_key)
    if cached is not None:
        return cached
    payload = json.loads(path.read_text(encoding="utf-8"))
    if str(payload.get("packet_version") or "") != PACKET_VERSION:
        raise ValueError("invalid slingshot packet version")
    _slingshot_cache_put(cache_key, payload)
    return payload


def packet_is_expired(packet: dict[str, Any]) -> bool:
    raw = str(packet.get("expires_at_utc") or "").strip()
    if not raw:
        return True
    try:
        normalized = raw.replace("Z", "+00:00")
        expires = datetime.fromisoformat(normalized)
        if expires.tzinfo is not None:
            from src.datetime_compat import UTC

            expires = expires.astimezone(UTC).replace(tzinfo=None)
        return datetime.utcnow() > expires
    except ValueError:
        return True


def ensure_packet_for_case(
    case_id: str,
    operator_intent: dict[str, Any] | None = None,
    *,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    """Load existing packet or build from frame."""
    root = runtime_root or DEFAULT_SLINGSHOT_ROOT
    path = packet_path(case_id, runtime_root=root)
    if path.is_file():
        packet = load_slingshot_packet(case_id, runtime_root=root)
        if not packet_is_expired(packet):
            return packet
    frame = load_slingshot_frame(case_id, runtime_root=root)
    return build_slingshot_packet(frame, operator_intent, runtime_root=root)
