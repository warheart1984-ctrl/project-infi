"""Reasoning delta engine — recorded vs recomputed at fork."""

from __future__ import annotations

from typing import Any

from src.temporal_replay.forward import forward_replay
from src.temporal_replay.law_pin import events_at_or_before, parse_at_timestamp


def build_reasoning_diff(
    *,
    subject_type: str,
    subject_id: str,
    events: list[dict[str, Any]],
    fork_at: str,
    target: str = "cloud_invariants",
    receipt_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fork_iso = parse_at_timestamp(fork_at)
    if not fork_iso:
        raise ValueError("fork_at must be a valid ISO timestamp")

    scoped = events_at_or_before(events, fork_iso)
    pin_event = scoped[-1] if scoped else None
    forward = forward_replay(
        subject_type=subject_type,
        subject_id=subject_id,
        events=events,
        fork_at=fork_iso,
        mode="dry_run",
        steps=1,
        target=target,
        receipt_schema=receipt_schema,
    )

    recorded_slice = [
        {
            "event_id": e.get("event_id"),
            "kind": e.get("kind"),
            "summary": e.get("summary"),
            "timestamp_utc": e.get("timestamp_utc"),
            "payload_hash": (e.get("payload_ref") or {}).get("hash"),
            "invariant_flags": e.get("invariant_flags"),
        }
        for e in scoped[-5:]
    ]

    return {
        "fork_at": fork_iso,
        "target": target,
        "pin_event_id": (pin_event or {}).get("event_id"),
        "recorded_tail": recorded_slice,
        "forward_replay": forward,
        "replay_delta": forward.get("replay_delta"),
        "deltas": forward.get("deltas") or [],
        "runtime_effect": "readout_only",
    }
