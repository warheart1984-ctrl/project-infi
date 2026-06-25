"""KLAW-5 — lineage-anchored law decisions."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from nova.law_kernel.models import LawEvalPayload, LineageEvent


class LineageStore:
    """Process-local lineage event ledger."""

    def __init__(self) -> None:
        self._events: list[LineageEvent] = []

    def list(self) -> list[LineageEvent]:
        return list(self._events)

    def emit_law_eval(self, evaluation: LawEvalPayload) -> LineageEvent:
        event = LineageEvent(
            id=f"lev-{uuid.uuid4().hex[:10]}",
            contract_id=evaluation.context.lineage_contract_id,
            kind="LAW_EVAL",
            payload=evaluation.to_dict(),
            ref_signal_hash=evaluation.t5_ref_signal_hash,
            invariant_proof_id=evaluation.invariant_proof_id,
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
        self._events.append(event)
        return event

    def emit_panic(self, evaluation: LawEvalPayload) -> LineageEvent:
        event = LineageEvent(
            id=f"lpn-{uuid.uuid4().hex[:10]}",
            contract_id=evaluation.context.lineage_contract_id,
            kind="LAW_PANIC",
            payload=evaluation.to_dict(),
            ref_signal_hash=evaluation.t5_ref_signal_hash,
            invariant_proof_id=evaluation.invariant_proof_id,
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
        self._events.append(event)
        return event

    def clear(self) -> None:
        self._events.clear()
