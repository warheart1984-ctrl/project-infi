"""Constitutional runtime v0.2 scenario tests."""

from __future__ import annotations

from nova.continuity.proof_generator import generate_proof_for_epoch
from nova.cortex.execution import CortexExecutor
from nova.crk.lineage.reflexive_events import clear_reflexive_events
from nova.crk.panels.perception_health_panel import clear_perception_snapshots
from nova.governance.api import propose_amendment, ratify_amendment
from nova.governance.steward_ledger import clear_steward_ledger
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-v02", hash="ref-v02", issued_at="now", issuer="test")


def test_epoch_run_produces_continuity_proof(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()
    clear_perception_snapshots()

    epoch_id = "EPOCH:8:T0"
    executor = CortexExecutor()
    executor.handle(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
            "message": "epoch run",
        },
        actor_id="operator",
        domain="cognition",
        epoch=epoch_id,
        lineage_contract_id="lc-1",
    )
    proof = generate_proof_for_epoch(epoch_id)
    assert proof.proof_id
    assert proof.reflexive_health_hash


def test_governed_evolution_respects_all_panels_and_governance(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()
    clear_perception_snapshots()
    clear_steward_ledger()

    epoch_id = "EPOCH:8:T1"
    executor = CortexExecutor()
    executor.handle(
        kind="ACT",
        payload={"capability": "echo", "message": "governed", "force_anomaly": 0.2},
        actor_id="operator",
        domain="substrate",
        epoch=epoch_id,
        lineage_contract_id="lc-1",
    )
    proposal = propose_amendment(
        "steward-a",
        {"actor_id": "operator", "epoch_id": epoch_id, "identity_hash": "ih-1"},
    )
    ratify_amendment("steward-a", proposal.id)
    proof = generate_proof_for_epoch(epoch_id)
    assert proof.amendment_history_hash
    assert proof.perception_health_hash


def test_no_ungoverned_path_to_substrate_exists(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)

    executor = CortexExecutor()
    try:
        result = executor.handle(
            kind="ACT",
            payload={"capability": "unknown_cap"},
            actor_id="operator",
            domain="substrate",
            epoch="EPOCH:8:T2",
            lineage_contract_id="lc-1",
        )
    except RuntimeError as exc:
        assert "Unknown capability" in str(exc)
        assert executor.router.router.evaluations
        return

    assert result.law_result["admitted"] is False
    assert executor.router.router.evaluations
