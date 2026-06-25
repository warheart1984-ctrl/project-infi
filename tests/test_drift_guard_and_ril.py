"""DriftGuard and RIL bridge tests."""

from __future__ import annotations

from nova.continuity.drift_guard import DriftGuard, clear_epoch_states
from nova.continuity.ril_bridge import export_epoch_lineage, replay_epoch
from nova.crk.cockpit.summary_builder import build_cockpit_summary
from nova.crk.lineage.reflexive_events import clear_reflexive_events
from nova.crk.panels.reflexive_evaluation_panel import ReflexiveEvaluationPanel
from nova.governance.api import propose_amendment, ratify_amendment
from nova.governance.steward_ledger import clear_steward_ledger
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.transform import pit2_transform
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-drift", hash="ref-drift", issued_at="now", issuer="test")


def test_epoch_export_and_replay_are_identical(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()

    epoch_id = "EPOCH:6:T0"
    panel = ReflexiveEvaluationPanel()
    ctx = LawContext(
        actor_id="op",
        domain="cognition",
        epoch=epoch_id,
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-drift",
        lineage_event_id="le:drift",
    )
    intent = new_intent(
        kind="ASK",
        payload={"pit_mode": "PIT-2", "pit_evidence_fitness": 0.9, "correctness_score": 0.9},
        origin="op",
    )
    panel.evaluate(pit2_transform(intent, ctx).transformed_intent, ctx)

    original = build_cockpit_summary(epoch_id=epoch_id)
    bundle = export_epoch_lineage(epoch_id)
    replayed = replay_epoch(bundle)
    assert replayed.cockpit_summary == original


def test_drift_report_detects_boundary_or_identity_changes(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_epoch_states()
    clear_steward_ledger()

    guard = DriftGuard()
    epoch_a = "EPOCH:6:T1"
    epoch_b = "EPOCH:6:T2"
    summary_a = build_cockpit_summary(epoch_id=epoch_a)
    guard.record_epoch_state(epoch_a, summary_a)

    proposal = propose_amendment(
        "steward-a",
        {"actor_id": "op", "epoch_id": epoch_b, "identity_hash": "changed"},
    )
    ratify_amendment("steward-a", proposal.id)
    summary_b = build_cockpit_summary(epoch_id=epoch_b)
    guard.record_epoch_state(epoch_b, summary_b)

    report = guard.detect_drift(epoch_a, epoch_b)
    assert report.drift_detected is True
    assert report.divergence > 0
    assert "amendment_history" in report.changed_sections or "identity_history" in report.changed_sections
