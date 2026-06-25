"""Cockpit v2 unified summary tests."""

from __future__ import annotations

from nova.continuity.ril_bridge import export_epoch_lineage, replay_epoch
from nova.crk.cockpit.summary_builder import build_cockpit_summary
from nova.crk.lineage.reflexive_events import clear_reflexive_events
from nova.crk.panels.perception_health_panel import clear_perception_snapshots
from nova.crk.panels.reflexive_evaluation_panel import ReflexiveEvaluationPanel
from nova.governance.steward_ledger import clear_steward_ledger
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.transform import pit2_transform
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-ckpt", hash="ref-ckpt", issued_at="now", issuer="test")


def _seed_epoch(monkeypatch, epoch_id: str) -> None:
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()
    clear_perception_snapshots()
    clear_steward_ledger()

    panel = ReflexiveEvaluationPanel()
    ctx = LawContext(
        actor_id="op",
        domain="cognition",
        epoch=epoch_id,
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-ckpt",
        lineage_event_id="le:ckpt",
    )
    intent = new_intent(
        kind="ASK",
        payload={"pit_mode": "PIT-2", "pit_evidence_fitness": 0.9, "correctness_score": 0.9},
        origin="op",
    )
    panel.evaluate(pit2_transform(intent, ctx).transformed_intent, ctx)


def test_cockpit_summary_replay_stable(monkeypatch):
    epoch_id = "EPOCH:4:T0"
    _seed_epoch(monkeypatch, epoch_id)
    first = build_cockpit_summary(epoch_id=epoch_id)
    bundle = export_epoch_lineage(epoch_id)
    replayed = replay_epoch(bundle)
    assert replayed.cockpit_summary == first


def test_cockpit_includes_all_panels_and_governance_blocks(monkeypatch):
    epoch_id = "EPOCH:4:T1"
    _seed_epoch(monkeypatch, epoch_id)
    summary = build_cockpit_summary(epoch_id=epoch_id)
    for section in (
        "boundary_detection",
        "reference_integrity",
        "identity_history",
        "pit_evolution",
        "reflexive_evaluation",
        "perception_health",
        "amendment_history",
    ):
        assert section in summary
    assert summary["reflexive_evaluation"]["reflexive_eval_count"] >= 1
