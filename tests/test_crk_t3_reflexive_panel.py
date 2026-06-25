"""CRK-T3 reflexive evaluation panel tests."""

from __future__ import annotations

from nova.crk.lineage.reflexive_events import clear_reflexive_events, list_reflexive_events
from nova.crk.panels.reflexive_evaluation_panel import ReflexiveEvaluationPanel
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.transform import pit2_transform
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-ref", hash="ref-t3", issued_at="now", issuer="test")


def test_reflexive_eval_requires_self_reflection_payload(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()

    intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
        },
        origin="user:1",
    )
    ctx = LawContext(
        actor_id="user:1",
        domain="cognition",
        epoch="EPOCH:1:T0",
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-t3",
        lineage_event_id="le:1",
    )
    transformed = pit2_transform(intent, ctx).transformed_intent
    reflection = transformed.payload["self_reflection"]
    assert reflection["reasoning_log_id"]
    assert reflection["assumptions_log_id"]
    assert reflection["uncertainty_profile_id"]

    panel = ReflexiveEvaluationPanel()
    report = panel.evaluate(transformed, ctx)
    assert report.reasoning_trace_present is True
    assert report.assumptions_logged is True
    assert report.uncertainty_tracked is True
    assert report.reflexive_health == "good"


def test_reflexive_eval_events_replay_stable(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()

    panel = ReflexiveEvaluationPanel()
    ctx = LawContext(
        actor_id="user:1",
        domain="cognition",
        epoch="EPOCH:1:T1",
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-t3",
        lineage_event_id="le:stable",
    )
    intent = new_intent(
        kind="ASK",
        payload={"pit_mode": "PIT-2", "pit_evidence_fitness": 0.9, "correctness_score": 0.9},
        origin="user:1",
    )
    transformed = pit2_transform(intent, ctx).transformed_intent
    panel.evaluate(transformed, ctx)
    panel.evaluate(transformed, ctx)

    stable = [
        {key: event[key] for key in ("kind", "epoch_id", "intent_id", "payload", "t5_ref_signal_hash")}
        for event in list_reflexive_events()
        if event["kind"] == "REFLEXIVE_EVAL"
    ]
    assert len(stable) == 2
    assert stable[0]["payload"]["reflexive_health"] == "good"


def test_reflexive_epoch_summary_monotone_in_degradation(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_reflexive_events()

    panel = ReflexiveEvaluationPanel()
    ctx = LawContext(
        actor_id="user:1",
        domain="cognition",
        epoch="EPOCH:1:T2",
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref-t3",
        lineage_event_id="le:deg",
    )

    good_intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "self_reflection": {
                "must_explain_reasoning": True,
                "must_log_assumptions": True,
                "must_track_uncertainty": True,
                "reasoning_log_id": "r1",
                "assumptions_log_id": "a1",
                "uncertainty_profile_id": "u1",
            },
        },
        origin="user:1",
    )
    degraded_intent = new_intent(
        kind="ASK",
        payload={
            "pit_mode": "PIT-2",
            "self_reflection": {
                "must_explain_reasoning": True,
                "must_log_assumptions": False,
                "must_track_uncertainty": False,
                "reasoning_log_id": "r2",
            },
        },
        origin="user:1",
    )

    panel.evaluate(good_intent, ctx)
    panel.evaluate(degraded_intent, ctx)
    summary = panel.summarize_epoch("EPOCH:1:T2")

    assert summary["eval_count"] == 2
    assert summary["degraded_count"] >= 1
    assert summary["health_sequence"][-1] == "degraded"
