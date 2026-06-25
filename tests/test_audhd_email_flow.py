"""AuDHD email flow integration tests."""

from __future__ import annotations

from nova.audhd.email_flow import AuDHDEmailOrchestrator
from nova.law_kernel.t5_binding import T5ReferenceSignal
from nova.lineage.bus import clear_lineage_bus, list_structured_events


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(
            id="t5-email",
            hash="ref-hash-email",
            issued_at="now",
            issuer="test",
        )


def test_incoming_email_protection_and_interpretation(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_lineage_bus()

    orchestrator = AuDHDEmailOrchestrator()
    incoming = "You always miss deadlines. I need you to fix this now. Can you?"

    audhd_view, flags, actions = orchestrator.process_incoming(incoming, intent="request")

    assert "Request (explicit)" in audhd_view
    assert flags.manipulation is True
    assert actions.get("raise_boundary_prompt") is True


def test_full_draft_flow(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_lineage_bus()

    orchestrator = AuDHDEmailOrchestrator()
    incoming = "You always miss deadlines. I need you to fix this now."

    audhd_view, flags, actions = orchestrator.process_incoming(incoming)
    result = orchestrator.draft_response(
        "That email stressed me out. I want to say no but not blow things up.",
        audhd_view=audhd_view,
        flags=flags,
        actions=actions,
        actor_id="user:123",
        epoch="EPOCH:2:T0",
        lineage_contract_id="lc-1",
    )

    assert result.draft_reply
    assert "Summary:" in result.scaffolded_reply
    assert result.law_result is not None
    assert result.law_result["admitted"] is True

    eval_payload = result.law_result["evaluation"]
    transformed = eval_payload.get("transformed_intent")
    if transformed:
        assert "reflection" in transformed["payload"]


def test_send_email_blocked_on_overload(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_lineage_bus()

    orchestrator = AuDHDEmailOrchestrator()
    orchestrator.safety.state.overload_score = 0.95
    orchestrator.pacing_ok = True

    outcome = orchestrator.send_response(
        manager_email="boss@example.com",
        body="I can't take this on right now.",
        actor_id="user:123",
        epoch="EPOCH:2:T1",
        lineage_contract_id="lc-1",
    )

    assert outcome["sent"] is False
    assert "Overload" in outcome["error"]


def test_ucc_lineage_emitted(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_lineage_bus()

    orchestrator = AuDHDEmailOrchestrator()
    orchestrator.process_incoming("Can you take this project?", intent="request")

    events = list_structured_events()
    assert any(event.kind == "UCC_PROTECTION" for event in events)
