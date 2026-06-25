"""Omega PIT adversarial harness tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.capability_ladders import DOMAIN_LADDERS, GLOBAL_CAPABILITY_HARD_CAP
from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.models import LawStatus, new_intent
from nova.law_kernel.t5_binding import T5ReferenceSignal
from nova.omega.cases import restore_ladders
from nova.omega.harness import OmegaRunner
from nova.omega.cases import all_cases


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(
            id="t5-omega",
            hash="ref-hash-omega",
            issued_at="now",
            issuer="omega-test",
        )


def _make_router_and_ledger(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    router = make_law_kernel_stack()
    ledger: LawLedger = router.ledger
    return router, ledger


def _run_and_collect(router, intent, **ctx):
    router.route(intent, **ctx)
    events = deepcopy(router.lineage_emitter.client.events)
    router.lineage_emitter.client.clear()
    router.substrate_executor.executed.clear()
    return events


def test_omega_pit_law_wrong_domain_fails_closed(monkeypatch):
    router, ledger = _make_router_and_ledger(monkeypatch)

    for code in ("PIT-2", "PIT-3"):
        ledger.append_status_change(code, status=LawStatus.REVOKED, epoch="EPOCH:OMEGA")

    ledger.add_law(
        code="PIT-2-BAD",
        text="Self-reflection transforms MAY be applied in BADDOMAIN only.",
        status=LawStatus.ADMITTED,
        fitness=0.9,
        epoch="EPOCH:OMEGA",
        domains=["BADDOMAIN"],
    )

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.95,
        },
        origin="operator",
    )

    events = _run_and_collect(
        router,
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-omega",
        lineage_event_id="le-omega-1",
    )

    decisions = [event["payload"]["decision"] for event in events if event["kind"] == "LAW_EVAL"]
    assert decisions
    assert "transform" not in decisions


def test_omega_insane_ladders_are_bounded(monkeypatch):
    router, _ = _make_router_and_ledger(monkeypatch)

    original = deepcopy(DOMAIN_LADDERS)
    DOMAIN_LADDERS["cognition"]["max_level"] = 1_000_000
    DOMAIN_LADDERS["cognition"]["base_step"] = 10_000.0

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-1",
            "pit_evidence_fitness": 1.0,
            "correctness_score": 1.0,
            "capability_level": 3,
        },
        origin="operator",
    )

    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-omega",
        lineage_event_id="le-omega-2",
    )

    executed = router.substrate_executor.executed
    assert executed
    cap = executed[0].payload["capability_level"]
    assert 1 <= cap <= GLOBAL_CAPABILITY_HARD_CAP

    DOMAIN_LADDERS.clear()
    DOMAIN_LADDERS.update(original)


def test_omega_negative_evidence_forces_non_transform(monkeypatch):
    router, _ = _make_router_and_ledger(monkeypatch)

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": -10.0,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    events = _run_and_collect(
        router,
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-omega",
        lineage_event_id="le-omega-3",
    )

    decisions = [event["payload"]["decision"] for event in events if event["kind"] == "LAW_EVAL"]
    assert decisions
    assert "transform" not in decisions


def test_omega_negative_law_fitness_does_not_enable_pit(monkeypatch):
    router, ledger = _make_router_and_ledger(monkeypatch)

    ledger.add_law(
        code="PIT-3-BAD",
        text="Multi-step planning transforms MAY be applied even with negative fitness.",
        status=LawStatus.ADMITTED,
        fitness=-1.0,
        epoch="EPOCH:OMEGA",
        domains=["planning"],
    )

    intent = new_intent(
        kind="PLAN",
        payload={
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.9,
        },
        origin="operator",
    )

    events = _run_and_collect(
        router,
        intent,
        actor_id="actor-1",
        domain="planning",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-omega",
        lineage_event_id="le-omega-4",
    )

    decisions = [event["payload"]["decision"] for event in events if event["kind"] == "LAW_EVAL"]
    assert decisions
    assert "panic" not in decisions


def test_omega_runner_score(monkeypatch):
    result = OmegaRunner(cases=all_cases()).run(monkeypatch)
    restore_ladders()
    assert result["omega_score"] >= 0.95
