"""T5-LAW invariant tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import new_intent
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(
            id="t5-1",
            hash="ref-hash-1",
            issued_at="now",
            issuer="test",
        )


def _make_router(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    return make_law_kernel_stack()


def _stable_payload(event: dict) -> dict:
    payload = dict(event["payload"])
    payload.pop("invariant_proof_id", None)
    return {
        "kind": event["kind"],
        "decision": payload.get("decision"),
        "context": payload.get("context"),
        "reasons": payload.get("reasons"),
    }


def test_t5_law_1_replay_stability(monkeypatch):
    router = _make_router(monkeypatch)

    intent = new_intent(
        kind="ASK",
        payload={"x": 1, "pit_evidence_fitness": 0.9, "correctness_score": 0.9},
        origin="operator",
    )

    ctx_kwargs = dict(
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        lineage_event_id="le-1",
    )

    router.route(intent, **ctx_kwargs)
    first_events = [_stable_payload(event) for event in router.lineage_emitter.client.events]

    router.substrate_executor.executed.clear()
    router.lineage_emitter.client.clear()

    router.route(intent, **ctx_kwargs)
    second_events = [_stable_payload(event) for event in router.lineage_emitter.client.events]

    assert first_events == second_events


def test_t5_law_2_no_admitted_decision_contradicts_laws(monkeypatch):
    router = _make_router(monkeypatch)

    intent = new_intent(kind="ASK", payload={"x": 1}, origin="operator")

    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    for event in router.lineage_emitter.client.events:
        if event["kind"] == "LAW_EVAL":
            decision = event["payload"]["decision"]
            laws = event["payload"]["applicable_laws"]
            forbidden = [
                law
                for law in laws
                if f"FORBID DOMAIN:{event['payload']['context']['domain'].upper()}"
                in law["text"].upper()
            ]
            if forbidden:
                assert decision != "admit"


def test_t5_law_3_law_fitness_changes_are_lineage_anchored(monkeypatch):
    router = _make_router(monkeypatch)

    intent = new_intent(kind="ASK", payload={"x": 1}, origin="operator")

    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        lineage_event_id="le-1",
    )

    for event in router.lineage_emitter.client.events:
        if event["kind"] in ("LAW_EVAL", "LAW_PANIC"):
            payload = event["payload"]
            assert payload["context"]["lineage_contract_id"] == "lc-1"
            assert payload["context"]["lineage_event_id"] == "le-1"
            assert payload["t5_ref_signal_hash"] == "ref-hash-1"
