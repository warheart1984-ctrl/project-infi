"""Lightweight reconstruction validation for early / pre-freeze concepts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EarlyConceptHarnessError(RuntimeError):
    pass


def load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EarlyConceptHarnessError(f"fixture must be object: {path}")
    return payload


def validate_early_concepts(fixture: dict[str, Any]) -> dict[str, Any]:
    events = {str(row["event_id"]): row for row in fixture.get("events") or []}
    ground = fixture.get("ground_truth") or {}
    pointers = ground.get("lineage_pointers") or []
    broken: list[str] = []
    for pointer in pointers:
        from_id = str(pointer["from_event_id"])
        to_id = str(pointer["to_event_id"])
        if from_id not in events:
            broken.append(f"missing from_event: {from_id}")
            continue
        if to_id not in events:
            broken.append(f"missing to_event: {to_id}")
            continue
        lineage = [str(item) for item in events[from_id].get("lineage") or []]
        if to_id not in lineage:
            broken.append(f"lineage gap: {from_id} -> {to_id}")

    anchor = str(ground.get("anchor_decision_id") or "")
    anchor_ok = anchor in events if anchor else True

    freeze_ids = [str(item) for item in ground.get("frozen_concept_ids") or []]
    missing_frozen = [item for item in freeze_ids if item not in events]

    passed = not broken and anchor_ok and not missing_frozen
    return {
        "harness_id": fixture.get("harness_id"),
        "thread_id": fixture.get("thread_id"),
        "passed": passed,
        "events_checked": len(events),
        "broken_lineage": broken,
        "anchor_decision_id": anchor,
        "anchor_ok": anchor_ok,
        "frozen_concept_ids": freeze_ids,
        "missing_frozen_concepts": missing_frozen,
    }


def run_fixture(path: Path) -> dict[str, Any]:
    return validate_early_concepts(load_fixture(path))
