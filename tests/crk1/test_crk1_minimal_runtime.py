"""Tests for CRK-1 minimal conceptual runtime."""

from __future__ import annotations

import pytest

from src.crk1.crk1_minimal_runtime import (
    CRK1MinimalRuntime,
    Decision,
    Interpretation,
    Outcome,
)
from src.crk1.errors import ConstitutionalError


def test_minimal_transmission_loop() -> None:
    runtime = CRK1MinimalRuntime()
    decision = Decision(identity_id="root", evidence_ids=["input-e1"])
    outcome = runtime.execute_decision(decision)

    assert outcome.id in runtime.outcomes
    assert any(item.outcome_id == outcome.id for item in runtime.evidence.values())
    replay = runtime.replay_outcome(outcome)
    assert replay.admissible is True


def test_minimal_semantic_invariants() -> None:
    runtime = CRK1MinimalRuntime()
    exposure = runtime.check_semantic_invariants()
    assert exposure > 0


def test_minimal_register_additional_frame() -> None:
    runtime = CRK1MinimalRuntime()
    runtime.register_interpretation(
        Interpretation(name="challenger-frame", adversarial=True, weight=0.2)
    )
    assert len(runtime.interpretations) == 3


def test_minimal_k7_requires_pluralism() -> None:
    runtime = CRK1MinimalRuntime()
    runtime.interpretations.clear()
    with pytest.raises(ConstitutionalError, match="K7"):
        runtime.register_interpretation(Interpretation(name="only-frame"))


def test_minimal_k1_blocks_non_replayable_outcome() -> None:
    runtime = CRK1MinimalRuntime()
    outcome = Outcome(replayable=False)
    with pytest.raises(ConstitutionalError, match="K1"):
        runtime.replay_outcome(outcome)
