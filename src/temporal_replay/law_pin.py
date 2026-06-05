"""Resolve law + boundary snapshot at replay timestamp T."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.project_infi_law import PROJECT_INFI_CONTRACT_VERSION
from src.ugr.invariants.cloud_manifold import CLOUD_INVARIANT_SET_VERSION


def parse_at_timestamp(at: str | None) -> str | None:
    if not at:
        return None
    text = str(at).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except ValueError:
        return None


def events_at_or_before(events: list[dict[str, Any]], at_iso: str | None) -> list[dict[str, Any]]:
    if not at_iso:
        return list(events)
    return [e for e in events if str(e.get("timestamp_utc") or "") <= at_iso]


def resolve_law_pin(
    events: list[dict[str, Any]],
    *,
    at: str | None = None,
    receipt_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return ReplayLawPin for timestamp T (last event at or before T with law context)."""
    at_iso = parse_at_timestamp(at)
    scoped = events_at_or_before(events, at_iso)

    pin_event: dict[str, Any] | None = None
    for event in reversed(scoped):
        law = dict(event.get("law_context") or {})
        boundary = dict(event.get("boundary") or {})
        if law.get("invariant_version") or law.get("law_version") or boundary.get("boundary_digest"):
            pin_event = event
            break

    law_context = dict((pin_event or {}).get("law_context") or {})
    boundary = dict((pin_event or {}).get("boundary") or {})

    if receipt_schema:
        law_context.setdefault("invariant_version", str(receipt_schema.get("invariant_version") or ""))
        law_context.setdefault("law_version", str(receipt_schema.get("urg_version") or ""))
        boundary.setdefault("boundary_digest", str(receipt_schema.get("boundary_digest") or ""))
        boundary.setdefault("cloud_identity_hash", str(receipt_schema.get("cloud_identity_hash") or ""))
        op_sig = dict(receipt_schema.get("operator_sig") or {})
        boundary.setdefault("tenant_id", str(op_sig.get("tenant_id") or "default"))

    return {
        "pinned_at": at_iso or (scoped[-1].get("timestamp_utc") if scoped else None),
        "pin_event_id": (pin_event or {}).get("event_id"),
        "law_id": str(law_context.get("law_id") or "project_infi_law"),
        "law_version": str(law_context.get("law_version") or ""),
        "contract_version": str(law_context.get("contract_version") or PROJECT_INFI_CONTRACT_VERSION),
        "invariant_version": str(law_context.get("invariant_version") or CLOUD_INVARIANT_SET_VERSION),
        "boundary_digest": str(boundary.get("boundary_digest") or ""),
        "tenant_id": str(boundary.get("tenant_id") or "default"),
        "cloud_identity_hash": str(boundary.get("cloud_identity_hash") or ""),
        "source_of_truth": "temporal_replay_law_pin",
    }
