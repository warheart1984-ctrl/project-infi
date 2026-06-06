"""Temporal replay event envelope helpers."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

TEMPORAL_REPLAY_EVENT_VERSION = "temporal_replay_event.v1"
PROJECT_INFI_CONTRACT_VERSION = "1.0.0"
CLOUD_INVARIANT_SET_VERSION = "1.0.0"

_EMITTER_REGISTRY: dict[str, dict[str, str]] = {
    "operator_decision": {
        "subsystem_id": "operator_decision_ledger",
        "module": "src.operator_decision_ledger",
        "genome_ref": "governance/subsystem_genomes/operator_decision_ledger.genome.v1.json",
    },
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def payload_hash(payload: dict[str, Any]) -> str:
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:32]


def new_event_id(kind: str, subject_key: str, sequence: int) -> str:
    safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(subject_key))[:48]
    return f"tre_{kind}_{safe_key}_{sequence:06d}"


def resolve_emitter(kind: str) -> dict[str, str]:
    return dict(
        _EMITTER_REGISTRY.get(kind)
        or {"subsystem_id": kind, "module": "", "genome_ref": ""}
    )


def normalize_replay_event(event: dict[str, Any]) -> dict[str, Any]:
    row = dict(event)
    row.setdefault("kind", "operator_decision")
    row.setdefault("subject_type", "operator_session")
    row.setdefault("emitter", resolve_emitter(str(row.get("kind") or "")))
    return row
