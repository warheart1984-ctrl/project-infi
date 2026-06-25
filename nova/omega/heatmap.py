from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from copy import deepcopy

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import new_intent
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _OmegaRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(
            id="t5-omega",
            hash="ref-hash-omega",
            issued_at="now",
            issuer="omega",
        )


@dataclass
class OmegaHeatmapPoint:
    evidence: float
    correctness: float
    domain: str
    survived: bool


def run_heatmap(
    monkeypatch: Any,
    domains: list[str],
    evidence_grid: list[float],
    correctness_grid: list[float],
) -> list[OmegaHeatmapPoint]:
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _OmegaRef)

    points: list[OmegaHeatmapPoint] = []

    for domain in domains:
        for evidence in evidence_grid:
            for correctness in correctness_grid:
                router = make_law_kernel_stack()

                intent = new_intent(
                    kind="ASK",
                    payload={
                        "pit_mode": "PIT-1",
                        "pit_evidence_fitness": evidence,
                        "correctness_score": correctness,
                        "capability_level": 3,
                    },
                    origin="omega",
                )

                ctx = dict(
                    actor_id="omega-actor",
                    domain=domain,
                    epoch="EPOCH:OMEGA",
                    lineage_contract_id="lc-omega",
                    lineage_event_id="le-omega",
                )

                router.route(intent, **ctx)
                events = deepcopy(router.lineage_emitter.client.events)
                points.append(
                    OmegaHeatmapPoint(
                        evidence=evidence,
                        correctness=correctness,
                        domain=domain,
                        survived=_survived(events),
                    )
                )

    return points


def _survived(events: list[dict[str, Any]]) -> bool:
    for event in events:
        if event["kind"] in ("LAW_EVAL", "LAW_PANIC"):
            payload = event["payload"]
            decision = payload["decision"]
            if decision not in ("admit", "deny", "panic", "transform"):
                return False
            if not payload.get("t5_ref_signal_hash"):
                return False
            ctx = payload.get("context", {})
            if not ctx.get("lineage_contract_id") or not ctx.get("lineage_event_id"):
                return False
    return True
