"""Forward replay under historical law (dry-run default)."""

from __future__ import annotations

from typing import Any

from src.temporal_replay.emitter_registry import live_fork_allowed
from src.temporal_replay.law_pin import events_at_or_before, parse_at_timestamp, resolve_law_pin


def forward_replay(
    *,
    subject_type: str,
    subject_id: str,
    events: list[dict[str, Any]],
    fork_at: str,
    mode: str = "dry_run",
    steps: int = 1,
    target: str = "cloud_invariants",
    receipt_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fork_iso = parse_at_timestamp(fork_at)
    if not fork_iso:
        raise ValueError("fork_at must be a valid ISO timestamp")

    law_pin = resolve_law_pin(events, at=fork_iso, receipt_schema=receipt_schema)
    scoped = events_at_or_before(events, fork_iso)
    next_events = [e for e in events if str(e.get("timestamp_utc") or "") > fork_iso][: max(1, int(steps or 1))]

    if mode == "live_fork":
        subsystem = _target_subsystem(target)
        if not live_fork_allowed(subsystem):
            return {
                "ok": False,
                "mode": mode,
                "blocked": True,
                "reason": f"live_fork not allowed for subsystem {subsystem}",
                "law_pin": law_pin,
                "runtime_effect": "blocked",
            }

    deltas: list[dict[str, Any]] = []
    for recorded in next_events[: max(1, int(steps or 1))]:
        deltas.append(_replay_one(target, recorded, law_pin, mode=mode, subject_id=subject_id))

    overall = "match"
    if any(d.get("delta") == "drift" for d in deltas):
        overall = "drift"
    if any(d.get("delta") == "blocked" for d in deltas):
        overall = "blocked"

    return {
        "ok": overall == "match",
        "mode": mode,
        "fork_at": fork_iso,
        "target": target,
        "law_pin": law_pin,
        "steps_requested": steps,
        "replay_delta": overall,
        "deltas": deltas,
        "runtime_effect": "dry_run" if mode == "dry_run" else "live_fork",
    }


def _target_subsystem(target: str) -> str:
    mapping = {
        "cognitive_bridge": "capability_service_bridge",
        "cloud_invariants": "invariant_engine_organ",
        "otem": "otem_bounded_organ",
        "mission_step": "urg.mission_runtime",
    }
    return mapping.get(target, "invariant_engine_organ")


def _replay_one(
    target: str,
    recorded: dict[str, Any],
    law_pin: dict[str, Any],
    *,
    mode: str,
    subject_id: str,
) -> dict[str, Any]:
    recorded_kind = str(recorded.get("kind") or "")
    recomputed: dict[str, Any] = {"status": "skipped", "detail": "unknown target"}

    if target == "cloud_invariants":
        recomputed = _dry_run_invariants(law_pin, recorded)
    elif target == "cognitive_bridge":
        recomputed = _dry_run_cognitive_bridge(law_pin, recorded, subject_id)
    elif target == "otem":
        recomputed = {"status": "asserted", "detail": "otem dry-run uses recorded plan only"}
    elif target == "mission_step":
        recomputed = {"status": "asserted", "detail": "mission step dry-run compares ledger kind only"}

    delta = _compare_delta(recorded, recomputed)
    return {
        "event_id": recorded.get("event_id"),
        "kind": recorded_kind,
        "recorded_summary": recorded.get("summary"),
        "recomputed": recomputed,
        "delta": delta,
        "mode": mode,
    }


def _dry_run_invariants(law_pin: dict[str, Any], recorded: dict[str, Any]) -> dict[str, Any]:
    flags = dict(recorded.get("invariant_flags") or {})
    inv_version = str(law_pin.get("invariant_version") or "")
    recorded_inv = str((recorded.get("law_context") or {}).get("invariant_version") or "")
    if recorded_inv and inv_version and recorded_inv != inv_version:
        return {"status": "blocked", "detail": "invariant_version_mismatch_at_pin"}
    if flags.get("hard_fail"):
        return {"status": "blocked", "detail": "recorded_hard_fail"}
    return {"status": "ok", "detail": "invariant_pin_aligned"}


def _dry_run_cognitive_bridge(
    law_pin: dict[str, Any],
    recorded: dict[str, Any],
    subject_id: str,
) -> dict[str, Any]:
    try:
        from src.cognitive_bridge import CognitiveBridgeService

        bridge = CognitiveBridgeService()
        result = bridge.route_to_bridge(
            {
                "user_message": f"[temporal-replay dry-run] subject={subject_id}",
                "session_metadata": {
                    "replay_context": {
                        "law_pin": law_pin,
                        "recorded_event_id": recorded.get("event_id"),
                    }
                },
                "operator_approved": True,
            },
            runtime_context="operator_runtime",
        )
        decision = str(result.get("decision") or result.get("status") or "")
        return {"status": decision or "routed", "detail": "cognitive_bridge dry-run"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _compare_delta(recorded: dict[str, Any], recomputed: dict[str, Any]) -> str:
    rec_flags = dict(recorded.get("invariant_flags") or {})
    if recomputed.get("status") == "blocked" and rec_flags.get("hard_fail"):
        return "match"
    if recomputed.get("status") == "ok" and not rec_flags.get("hard_fail"):
        return "match"
    if recomputed.get("status") == "error":
        return "blocked"
    if recomputed.get("detail", "").endswith("_mismatch_at_pin"):
        return "drift"
    return "drift"
