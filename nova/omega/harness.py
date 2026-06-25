from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
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
class OmegaCase:
    name: str
    mutate: Callable[[Any], None]
    intent_payload: dict[str, Any]
    domain: str
    expect: Callable[[list[dict[str, Any]], Any], bool]


@dataclass
class OmegaRunner:
    cases: list[OmegaCase]

    def run(self, monkeypatch: Any) -> dict[str, Any]:
        monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _OmegaRef)

        results: list[dict[str, Any]] = []
        failures = 0

        for case in self.cases:
            router = make_law_kernel_stack()
            case.mutate(router)

            intent = new_intent(
                kind="ASK",
                payload=case.intent_payload,
                origin="omega",
            )

            ctx = dict(
                actor_id="omega-actor",
                domain=case.domain,
                epoch="EPOCH:OMEGA",
                lineage_contract_id="lc-omega",
                lineage_event_id="le-omega",
            )

            router.route(intent, **ctx)
            events = deepcopy(router.lineage_emitter.client.events)

            proofs: list[dict[str, Any]] = []
            for event in events:
                if event["kind"] == "LAW_EVAL":
                    payload = event["payload"]
                    proofs.append(
                        {
                            "decision": payload["decision"],
                            "t5_ref_signal_hash": payload["t5_ref_signal_hash"],
                            "invariant_proof_id": payload.get("invariant_proof_id", ""),
                        }
                    )

            passed = case.expect(events, router)
            results.append({"case": case.name, "passed": passed, "proofs": proofs})

            if not passed:
                failures += 1

        total = len(self.cases)
        omega_score = 1.0 - (failures / total) if total else 0.0

        return {
            "total": total,
            "failures": failures,
            "omega_score": omega_score,
            "results": results,
        }
