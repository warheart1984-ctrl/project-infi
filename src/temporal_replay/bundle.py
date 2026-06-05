"""Export temporal replay verification bundles."""

from __future__ import annotations

from typing import Any

from src.temporal_replay.event import payload_hash
from src.temporal_replay.law_pin import resolve_law_pin
from src.temporal_replay.paths import BUNDLE_VERSION
from src.temporal_replay.state import reconstruct_state
from src.temporal_replay.verify import verify_replay


def build_replay_bundle(
    *,
    subject_type: str,
    subject_id: str,
    events: list[dict[str, Any]],
    fork_at: str | None = None,
    tenant_id: str | None = None,
    receipt_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    law_pin = resolve_law_pin(events, at=fork_at, receipt_schema=receipt_schema)
    verification = verify_replay(
        subject_type=subject_type,
        subject_id=subject_id,
        events=events,
        at=fork_at,
        tenant_id=tenant_id,
    )
    state = reconstruct_state(
        subject_type=subject_type,
        subject_id=subject_id,
        events=events,
        at=fork_at,
        receipt_schema=receipt_schema,
    )
    scoped = events
    if fork_at:
        from src.temporal_replay.law_pin import events_at_or_before, parse_at_timestamp

        scoped = events_at_or_before(events, parse_at_timestamp(fork_at))

    artifact_hashes = {
        "timeline": payload_hash(scoped),
        "law_pin": payload_hash(law_pin),
        "state": payload_hash(state),
    }

    return {
        "bundle_version": BUNDLE_VERSION,
        "subject": {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "tenant_id": law_pin.get("tenant_id") or tenant_id or "default",
        },
        "fork_at": fork_at or (scoped[-1].get("timestamp_utc") if scoped else None),
        "law_pin": law_pin,
        "timeline_hash": payload_hash(scoped),
        "verification_report": verification,
        "artifact_hashes": artifact_hashes,
        "claim_label": verification.get("claim_label") or "asserted",
        "runtime_effect": "readout_only",
        "event_count": len(scoped),
    }
