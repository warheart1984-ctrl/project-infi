"""UCC constitutional safety tests."""

from __future__ import annotations

import pytest

from nova.audhd.interpreter import AuDHDInterpreter, Utterance
from nova.audhd.protection import AuDHDProtectionEngine
from nova.audhd.safety_layer import AuDHDCognitiveSafetyLayer
from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.transform import pit2_transform
from nova.law_kernel.t5_binding import T5ReferenceSignal
from nova.ucc.patterns import pacing_consent_prompt, render_pattern


def test_overload_reduction():
    safety = AuDHDCognitiveSafetyLayer()
    safety.state.overload_score = 0.9
    long_reply = "word " * 200
    result = safety.scaffold_reply(long_reply)
    assert len(result) < 400
    assert "Summary:" in result
    assert "pace okay" in result


def test_ambiguity_translation():
    interpreter = AuDHDInterpreter()
    utterance = Utterance(text="Can you handle this?", tone="masked", intent="request")
    output = interpreter.to_audhd(utterance)
    assert interpreter.has_explicit_intent_label(output)


def test_boundary_enforcement():
    protection = AuDHDProtectionEngine()
    flags = protection.analyze("You always fail and you never deliver. Calm down.")
    assert flags.manipulation is True
    assert flags.gaslighting_risk is True


def test_pacing_consent_prompt_present():
    opening = render_pattern("safe_opening")
    assert "pace" in opening.lower()


def test_pit_ucc_compliance(monkeypatch):
    class _Ref(T5ReferenceSignal):
        @classmethod
        def current(cls) -> T5ReferenceSignal:
            return T5ReferenceSignal(id="t5", hash="ref", issued_at="now", issuer="test")

    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _Ref)

    intent = new_intent(
        kind="ASK",
        payload={
            "task": "draft_boundary_email",
            "ucc_enabled": True,
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
        },
        origin="user:1",
    )
    ctx = LawContext(
        actor_id="user:1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
        t5_ref_signal_hash="ref",
    )
    result = pit2_transform(intent, ctx)
    reflection = result.transformed_intent.payload["reflection"]
    assert reflection["intent"]
    assert reflection["reasoning_steps"]
    assert reflection["ambiguity_removed"] is True


def test_ucc_laws_seeded():
    router = make_law_kernel_stack()
    codes = {law.code for law in router.ledger.admitted()}
    for code in ("LAW-UCC-1", "LAW-UCC-2", "LAW-UCC-3", "LAW-UCC-4", "LAW-UCC-5", "LAW-UCC-6"):
        assert code in codes


def test_pacing_consent_helper():
    assert "slow" in pacing_consent_prompt()
