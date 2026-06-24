"""CRK-1 replay-stable continuity trace format."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.crk1.runtime_facade import CRK1Runtime


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ContinuityTrace:
    version: str = "1.0"
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    identity: str = ""
    lineage: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    continuity_status: str = "PRESERVED"
    replay_hash: str = ""

    def compute_replay_hash(self) -> str:
        body = json.dumps(
            {"events": self.events, "lineage": self.lineage},
            sort_keys=True,
        ).encode()
        self.replay_hash = hashlib.sha256(body).hexdigest()
        return self.replay_hash

    def to_dict(self) -> dict[str, Any]:
        if not self.replay_hash:
            self.compute_replay_hash()
        return {
            "version": self.version,
            "trace_id": self.trace_id,
            "identity": self.identity,
            "lineage": list(self.lineage),
            "events": list(self.events),
            "continuity_status": self.continuity_status,
            "replay_hash": self.replay_hash,
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def build_trace_from_runtime(
    runtime: CRK1Runtime,
    identity_id: str,
    *,
    continuity_status: str = "PRESERVED",
) -> ContinuityTrace:
    trace = ContinuityTrace(
        identity=identity_id,
        lineage=runtime.get_lineage(identity_id),
        continuity_status=continuity_status,
    )

    for record in runtime.kernel.decisions.list_decisions():
        if record.identity_id != identity_id:
            continue
        trace.events.append(
            {
                "type": "Decision",
                "id": record.id,
                "timestamp": record.created_at or _now_iso(),
                "evidence_ids": list(record.evidence_refs),
            }
        )

    for outcome in runtime.get_all_outcomes():
        decision = runtime.kernel.decisions.get(outcome.decision_id)
        if decision is None or decision.identity_id != identity_id:
            continue
        trace.events.append(
            {
                "type": "Outcome",
                "id": outcome.id,
                "decision_id": outcome.decision_id,
                "status": "success",
                "replayable": outcome.replayable,
            }
        )

    for evidence in runtime.get_all_evidence():
        if evidence.source_identity_id != identity_id:
            continue
        trace.events.append(
            {
                "type": "Evidence",
                "id": evidence.id,
                "source_outcome_id": evidence.outcome_id or None,
                "admissible_for_decision": evidence.admissible_for_decision,
            }
        )

    trace.compute_replay_hash()
    return trace
