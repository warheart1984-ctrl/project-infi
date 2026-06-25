"""LawKernelPanicHandler — KLAW-2 fail-closed panic path."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nova.law_kernel.lineage import LineageStore
from nova.law_kernel.models import LawDecision, LawEvalPayload


@dataclass
class PanicRecord:
    evaluation: LawEvalPayload
    frozen_lane: str
    details: dict[str, Any] = field(default_factory=dict)


class LawKernelPanicHandler:
    """Centralizes fail-closed behavior for uncertainty, drift, and violations."""

    def __init__(self, *, lineage: LineageStore) -> None:
        self.lineage = lineage
        self.frozen_lanes: set[str] = set()
        self.panics: list[PanicRecord] = []

    def handle(self, evaluation: LawEvalPayload) -> PanicRecord:
        if evaluation.decision != LawDecision.PANIC:
            raise ValueError("panic handler requires decision=panic")
        lane = f"{evaluation.context.domain}:{evaluation.context.actor_id}"
        self.frozen_lanes.add(lane)
        self.lineage.emit_panic(evaluation)
        record = PanicRecord(
            evaluation=evaluation,
            frozen_lane=lane,
            details={
                "reasons": list(evaluation.reasons),
                "proof_id": evaluation.invariant_proof_id,
                "ref_signal_hash": evaluation.t5_ref_signal_hash,
            },
        )
        self.panics.append(record)
        return record

    def is_frozen(self, *, domain: str, actor_id: str) -> bool:
        return f"{domain}:{actor_id}" in self.frozen_lanes
