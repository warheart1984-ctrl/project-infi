"""Constitutional substrate — Meta Lawbook spine and collaboration membrane."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from src.substrate.ingress.collaboration_membrane import (
    CollaborationCharterError,
    bootstrap_collaboration_charter,
    evaluate_turn_collaboration_membrane,
    resolve_collaboration_context,
)
from src.substrate.meta_law_engine import (
    ConstitutionalLawbookError,
    bootstrap_constitutional_lawbook,
    resolve_constitutional_context,
)
from tests.governance_bootstrap import (
    ensure_collaboration_charter_ready,
    ensure_constitutional_substrate,
)


def test_resolve_constitutional_context_loads_lawbook():
    context = resolve_constitutional_context()
    assert context["lawbook_present"] is True
    assert context["digest"]
    assert context["precedence"] == [
        "law",
        "blueprint",
        "contract",
        "implementation",
        "pipeline",
        "tool",
    ]
    invariant_ids = {item["invariant_id"] for item in context["invariants"]}
    assert "constitutional_precedence" in invariant_ids
    assert "proof_of_reality" in invariant_ids
    assert "trust_bundle" in invariant_ids
    assert "fail_closed" in invariant_ids
    assert "ma_12_operational_primer" in invariant_ids
    assert "ma_13_copilot_integrator" in invariant_ids


def test_resolve_collaboration_context_loads_charter():
    context = resolve_collaboration_context(details={"claim_label": "asserted", "reversible": True})
    assert context["charter_present"] is True
    assert context["admitted"] is True
    invariant_ids = {item["invariant_id"] for item in context["invariants"]}
    assert invariant_ids == {
        "claim_labels",
        "human_authority",
        "override",
        "epistemic_escalation",
        "reversibility",
    }


def test_project_infi_law_attaches_constitutional_context():
    from src.project_infi_law import ProjectInfiLaw

    engine = ProjectInfiLaw()
    contract, _ul, _event = engine.require_contract(
        surface="chat_turn",
        action_id="constitutional_probe",
        actor_id="test",
        actor_role="system",
        session_id="sess-constitutional",
        target="chat_session:sess-constitutional",
    )
    constitutional = contract.get("constitutional_context") or {}
    assert constitutional.get("lawbook_present") is True
    law_ids = [check["law_id"] for check in contract.get("law_checks") or []]
    assert law_ids[0] == "law_0_supreme_precedence"


def test_collaboration_membrane_blocks_invalid_claim_label():
    context = evaluate_turn_collaboration_membrane(
        session_id="sess-charter",
        details={"claim_label": "trusted", "reversible": True},
    )
    assert context["admitted"] is False
    assert "claim_labels" in (context.get("blocking_invariants") or [])


def test_governance_bootstrap_constitutional_hooks():
    ensure_constitutional_substrate()
    ensure_collaboration_charter_ready()


def test_bootstrap_refuses_missing_lawbook_when_required(monkeypatch):
    monkeypatch.setenv("AAIS_REQUIRE_CONSTITUTIONAL_LAW", "1")
    monkeypatch.setattr(
        "src.substrate.meta_law_engine.load_lawbook_text",
        lambda: None,
    )
    with pytest.raises(ConstitutionalLawbookError):
        bootstrap_constitutional_lawbook()


def test_bootstrap_refuses_missing_charter_when_required(monkeypatch):
    monkeypatch.setenv("AAIS_REQUIRE_COLLABORATION_CHARTER", "1")
    monkeypatch.setattr(
        "src.substrate.ingress.collaboration_membrane.load_charter_text",
        lambda: None,
    )
    with pytest.raises(CollaborationCharterError):
        bootstrap_collaboration_charter()


def test_finalize_chat_turn_admission_applies_membrane(monkeypatch):
    from src.chat_turn_governance import finalize_chat_turn_admission

    session = SimpleNamespace(
        session_id="sess-membrane",
        metadata={
            "cognitive_bridge": {},
            "modular_preview": {},
            "ul_snapshot": {},
        },
    )
    monkeypatch.setenv("AAIS_REQUIRE_COLLABORATION_CHARTER", "0")
    text, blocked = finalize_chat_turn_admission(
        session,
        user_message="hello",
        response_text="world",
        response_trace={"claim_label": "asserted"},
    )
    assert blocked is None or isinstance(blocked, dict)
    assert session.metadata.get("collaboration_membrane") is not None
