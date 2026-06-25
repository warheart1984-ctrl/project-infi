"""Tests for constitutional_state drop-in core."""

from __future__ import annotations

import pytest

from constitutional.core import (
    AmendmentContext,
    AmendmentEngine,
    ConstitutionalStateRuntime,
    LEGAL_TRANSITIONS,
    ObserverVerificationEngine,
    StateObject,
    validate_transition,
)


def test_legal_transition_graph() -> None:
    assert LEGAL_TRANSITIONS["Proposed"] == ["Evaluated"]
    assert "Closed" in LEGAL_TRANSITIONS["Observed"]


def test_csr_register_replay_happy_path() -> None:
    csr = ConstitutionalStateRuntime()
    state = StateObject(state_id="claim-001", state_type="ClaimState")
    csr.register_state(state)
    from constitutional.core.models import Transition

    for to_state in ["Evaluated", "Approved", "Executed", "Observed", "Closed"]:
        current = csr.get_state("claim-001")
        csr.apply_transition(
            Transition(
                state_object_id="claim-001",
                from_state=current.current_state,
                to_state=to_state,
                receipt_id=f"rcv-{to_state}",
                runtime="test",
                legal_basis="test",
                accountable_party="operator",
            )
        )
    replay = csr.replay("claim-001")
    assert not replay["diverged"]
    assert replay["reconstructed_state"] == "Closed"


def test_amendment_engine_lifecycle() -> None:
    csr = ConstitutionalStateRuntime()
    engine = AmendmentEngine(csr)
    amendment = StateObject(state_id="amend-xvii", state_type="AmendmentState")
    ctx = AmendmentContext(
        article="XVII",
        change_type="addition",
        justification="new article",
        trigger_receipt_id="trg-1",
    )
    receipt_ids = {
        "proposal": "r-proposal",
        "evaluation": "r-eval",
        "ratification": "r-ratify",
        "implementation": "r-impl",
        "closure": "r-close",
    }
    final = engine.run_amendment_lifecycle(amendment, ctx, receipt_ids, "sovereign")
    assert final.current_state == "Closed"
    assert final.version == 5


def test_observer_engine_detects_divergence() -> None:
    csr = ConstitutionalStateRuntime()
    state = StateObject(state_id="s1", state_type="ClaimState", current_state="Closed")
    csr.register_state(state)
    observer = ObserverVerificationEngine(csr)
    result = observer.verify_state("s1")
    assert result.divergence_detected


def test_validate_transition_rejects_skip() -> None:
    with pytest.raises(ValueError, match="Illegal transition"):
        validate_transition("Proposed", "Closed")
