"""Reconstruct replay state at timestamp T."""

from __future__ import annotations

from typing import Any

from src.temporal_replay.law_pin import events_at_or_before, parse_at_timestamp, resolve_law_pin


def reconstruct_state(
    *,
    subject_type: str,
    subject_id: str,
    events: list[dict[str, Any]],
    at: str | None = None,
    receipt_schema: dict[str, Any] | None = None,
    ledger_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    at_iso = parse_at_timestamp(at)
    scoped = events_at_or_before(events, at_iso)
    law_pin = resolve_law_pin(events, at=at_iso, receipt_schema=receipt_schema)

    state: dict[str, Any] = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "at": at_iso,
        "law_pin": law_pin,
        "event_count": len(scoped),
        "last_event_id": scoped[-1].get("event_id") if scoped else None,
        "runtime_effect": "readout_only",
    }

    invariant_violations = [
        {
            "event_id": e.get("event_id"),
            "timestamp_utc": e.get("timestamp_utc"),
            "kind": e.get("kind"),
            "codes": list((e.get("invariant_flags") or {}).get("codes") or []),
        }
        for e in scoped
        if (e.get("invariant_flags") or {}).get("hard_fail")
    ]
    state["invariant_violations"] = invariant_violations

    if subject_type == "mission":
        state["mission"] = _mission_slice(subject_id, scoped, ledger_rows=ledger_rows, receipt_schema=receipt_schema)
    elif subject_type == "workflow_run":
        state["workflow"] = {"law_events": [e for e in scoped if e.get("kind") == "law_event"]}
    elif subject_type == "session":
        state["session"] = {
            "capability_events": [e for e in scoped if e.get("kind") == "capability_audit"],
            "coverage": "partial" if scoped else "missing",
        }
    elif subject_type == "jarvis_run":
        state["jarvis_run"] = {"steps": [e for e in scoped if e.get("kind") == "jarvis_run_step"]}

    if receipt_schema:
        state["receipt_snapshot"] = {
            "ledger_root": receipt_schema.get("ledger_root"),
            "invariant_digest": receipt_schema.get("invariant_digest"),
            "goal_hash": receipt_schema.get("goal_hash"),
            "outcome": receipt_schema.get("outcome"),
        }

    return state


def _mission_slice(
    mission_id: str,
    scoped: list[dict[str, Any]],
    *,
    ledger_rows: list[dict[str, Any]] | None,
    receipt_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    from src.ugr.mission.ledger_merkle import compute_ledger_merkle_root

    rows = list(ledger_rows or [])
    if not rows and mission_id:
        try:
            from src.ugr.mission.mission_ledger import MissionLedger

            rows = MissionLedger().list_for_mission(mission_id)
        except Exception:
            rows = []

    at_iso = scoped[-1].get("timestamp_utc") if scoped else None
    if at_iso:
        filtered = []
        for row in rows:
            ts = str(row.get("timestamp") or "")
            if not ts or ts <= at_iso:
                filtered.append(row)
        rows = filtered or rows

    computed_root = compute_ledger_merkle_root(rows)
    expected_root = str((receipt_schema or {}).get("ledger_root") or "")
    return {
        "ledger_row_count": len(rows),
        "computed_ledger_root": computed_root,
        "expected_ledger_root": expected_root,
        "ledger_root_match": (not expected_root) or computed_root == expected_root,
        "lineage_nodes": len([e for e in scoped if e.get("kind") == "lineage_node"]),
        "deliberation_events": len([e for e in scoped if e.get("kind") == "deliberation"]),
    }
