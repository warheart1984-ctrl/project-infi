from __future__ import annotations

import pytest

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import new_intent
from nova.law_kernel.router import LawfulIntentRouter
from nova.law_kernel.t5_binding import T5ReferenceSignal


# --- monkeypatch T5 reference signal ----------------------------------------


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(
            id="t5-1",
            hash="ref-hash-1",
            issued_at="now",
            issuer="test",
        )


# --- helpers ----------------------------------------------------------------


def make_router(monkeypatch) -> LawfulIntentRouter:
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    return make_law_kernel_stack()


# --- PIT‑2 / PIT‑3 activation tests -----------------------------------------


def test_pit2_fires_only_with_evidence_and_domain(monkeypatch):
    router = make_router(monkeypatch)

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    executed = router.substrate_executor.executed
    assert executed, "Expected transformed intent to be executed"
    assert executed[0].id.endswith(":pit2")


def test_pit2_does_not_fire_with_low_evidence(monkeypatch):
    router = make_router(monkeypatch)

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.3,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    executed = router.substrate_executor.executed
    assert executed, "Expected ADMIT path to execute original intent"
    assert not executed[0].id.endswith(":pit2")


def test_pit2_does_not_fire_in_wrong_domain(monkeypatch):
    router = make_router(monkeypatch)

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="substrate",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    executed = router.substrate_executor.executed
    assert executed, "Expected ADMIT path to execute original intent"
    assert not executed[0].id.endswith(":pit2")


def test_pit3_fires_only_with_evidence_and_domain(monkeypatch):
    router = make_router(monkeypatch)

    intent = new_intent(
        kind="PLAN",
        payload={
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.8,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="planning",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    executed = router.substrate_executor.executed
    assert executed, "Expected transformed intent to be executed"
    assert executed[0].id.endswith(":pit3")


def test_pit3_does_not_fire_with_low_evidence(monkeypatch):
    router = make_router(monkeypatch)

    intent = new_intent(
        kind="PLAN",
        payload={
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.2,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="planning",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    executed = router.substrate_executor.executed
    assert executed, "Expected ADMIT path"
    assert not executed[0].id.endswith(":pit3")


def test_pit3_does_not_fire_in_wrong_domain(monkeypatch):
    router = make_router(monkeypatch)

    intent = new_intent(
        kind="PLAN",
        payload={
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="governance",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )

    executed = router.substrate_executor.executed
    assert executed, "Expected ADMIT path"
    assert not executed[0].id.endswith(":pit3")
