from __future__ import annotations

from nova.continuity.fitness import (
    ContinuityFitnessComponents,
    compute_pit_fitness,
    continuity_fitness_index,
)
from nova.law_continuity.runtime import ContinuityDriftDetector, ContinuityReplayEngine
from nova.cortex.facade import NovaCortexFacade
from nova.governance.engine import GovernanceEngine
from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.t5_binding import T5ReferenceSignal
from nova.omega.drift import drift_for_mode, expected_drift_bounds, within_bounds
from nova.specimen.manager import SpecimenManager


def test_cortex_facade_routes_through_law_kernel(monkeypatch):
    class _Ref(T5ReferenceSignal):
        @classmethod
        def current(cls) -> T5ReferenceSignal:
            return T5ReferenceSignal(
                id="t5",
                hash="ref-hash-facade",
                issued_at="now",
                issuer="test",
            )

    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _Ref)

    cortex = NovaCortexFacade.from_kernel()
    result = cortex.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "hello"},
        actor_id="session-1",
        domain="substrate",
        epoch="EPOCH:1:T0",
        lineage_contract_id="lc-1",
    )

    assert result["admitted"] is True
    assert cortex.router.evaluations
    assert cortex.router.lineage.list()


def test_continuity_replay_and_drift(monkeypatch):
    from nova.law_kernel.t5_binding import T5ReferenceSignal

    class _Ref(T5ReferenceSignal):
        @classmethod
        def current(cls) -> T5ReferenceSignal:
            return T5ReferenceSignal(
                id="t5",
                hash="ref-hash-cont",
                issued_at="now",
                issuer="test",
            )

    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _Ref)

    router = make_law_kernel_stack()
    engine = ContinuityReplayEngine(router)
    snapshot = engine.snapshot()
    assert snapshot.state_hash

    intent = new_intent(kind="ASK", payload={}, origin="operator")
    ctx = LawContext(
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-hash-cont",
        lineage_event_id="le-1",
    )

    first = engine.replay(intent, ctx)
    second = engine.replay(intent, ctx)
    detector = ContinuityDriftDetector()
    assert detector.compare_runs(first, second)


def test_governance_engine_admits_law():
    router = make_law_kernel_stack(persist=False)
    engine = GovernanceEngine(router.ledger)
    proposal = engine.propose_law("SIT-9", "New structural invariant")
    engine.vote(proposal.id, 1.0, True)
    finalized = engine.finalize(proposal.id)
    assert finalized.status.value == "accepted"
    assert router.ledger.get("SIT-9") is not None


def test_specimen_manager_isolation():
    manager = SpecimenManager()
    left = manager.create("alpha")
    right = manager.create("beta")
    assert left.router is not right.router


def test_cfi_and_drift_bounds():
    router = make_law_kernel_stack()
    pit_fitness = compute_pit_fitness(router.ledger)
    cfi = continuity_fitness_index(
        ContinuityFitnessComponents(
            omega_score=0.96,
            pit_fitness=pit_fitness,
            lineage_stability=0.9,
        )
    )
    assert 0.0 <= cfi <= 1.0

    intent = new_intent(
        kind="ASK",
        payload={"pit_evidence_fitness": 0.9, "correctness_score": 0.9, "capability_level": 2},
        origin="operator",
    )
    ctx = LawContext(
        actor_id="a",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="h",
    )
    for mode in ("PIT-1", "PIT-2", "PIT-3"):
        drift = drift_for_mode(intent, ctx, mode)
        assert within_bounds(drift, expected_drift_bounds(mode))
