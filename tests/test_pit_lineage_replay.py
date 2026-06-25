"""PIT lineage replay stability tests."""

from __future__ import annotations

from copy import deepcopy

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
    return {
        "kind": event["kind"],
        "decision": payload.get("decision"),
        "context": payload.get("context"),
    }


def _stable_replay(router, intent, ctx):
    router.route(intent, **ctx)
    first_events = [_stable_payload(event) for event in router.lineage_emitter.client.events]

    router.substrate_executor.executed.clear()
    router.lineage_emitter.client.clear()

    router.route(intent, **ctx)
    second_events = [_stable_payload(event) for event in router.lineage_emitter.client.events]

    assert first_events == second_events


def test_pit2_lineage_replay_is_stable(monkeypatch):
    router = _make_router(monkeypatch)

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    ctx = dict(
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        lineage_event_id="le-1",
    )

    _stable_replay(router, intent, ctx)


def test_pit3_lineage_replay_is_stable(monkeypatch):
    router = _make_router(monkeypatch)

    intent = new_intent(
        kind="PLAN",
        payload={
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.8,
        },
        origin="operator",
    )

    ctx = dict(
        actor_id="actor-1",
        domain="planning",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        lineage_event_id="le-1",
    )

    _stable_replay(router, intent, ctx)
