"""Continuity proof tests."""

from __future__ import annotations

from nova.continuity.proof_generator import generate_proof_for_epoch
from nova.continuity.proofs import proof_from_cockpit_summary
from nova.crk.cockpit.summary_builder import build_cockpit_summary
from nova.crk.lineage.reflexive_events import clear_reflexive_events
from nova.crk.panels.perception_health_panel import clear_perception_snapshots
from nova.crk.panels.reflexive_evaluation_panel import ReflexiveEvaluationPanel
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.transform import pit2_transform
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-proof", hash="ref-proof", issued_at="now", issuer="test")


def test_proof_replay_stable(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()
    clear_perception_snapshots()

    epoch_id = "EPOCH:7:T0"
    panel = ReflexiveEvaluationPanel()
    ctx = LawContext(
        actor_id="op",
        domain="cognition",
        epoch=epoch_id,
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-proof",
        lineage_event_id="le:proof",
    )
    intent = new_intent(
        kind="ASK",
        payload={"pit_mode": "PIT-2", "pit_evidence_fitness": 0.9, "correctness_score": 0.9},
        origin="op",
    )
    panel.evaluate(pit2_transform(intent, ctx).transformed_intent, ctx)

    first = generate_proof_for_epoch(epoch_id)
    second = generate_proof_for_epoch(epoch_id)
    assert first.to_dict() == second.to_dict()


def test_proof_changes_when_any_panel_state_changes(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()
    clear_perception_snapshots()

    epoch_id = "EPOCH:7:T1"
    base_summary = build_cockpit_summary(epoch_id=epoch_id)
    base_proof = proof_from_cockpit_summary(epoch_id, base_summary)

    changed = dict(base_summary)
    changed["perception_health"] = {
        **base_summary["perception_health"],
        "latest_perception_health": "degraded",
    }
    changed_proof = proof_from_cockpit_summary(epoch_id, changed)
    assert changed_proof.perception_health_hash != base_proof.perception_health_hash
    assert changed_proof.proof_id != base_proof.proof_id
