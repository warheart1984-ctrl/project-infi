"""CRK-1.K1 — Immutable Exposure Constraint atomic tests."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError


def test_k1_cannot_delete_outcome(runtime) -> None:
  """K1-T1: outcome deletion is forbidden."""
  identity = runtime.create_identity("A")
  decision = runtime.propose_and_execute(identity=identity.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]

  with pytest.raises(ConstitutionalError, match="K1"):
    runtime.delete_outcome(outcome.id)


def test_k1_cannot_quarantine_evidence(runtime) -> None:
  """K1-T2: evidence quarantine is forbidden."""
  identity = runtime.create_identity("A")
  decision = runtime.propose_and_execute(identity=identity.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]
  evidence = runtime.replay_outcome(outcome.id)

  with pytest.raises(ConstitutionalError, match="K1"):
    runtime.mark_evidence_non_admissible(evidence.id)


def test_k1_cannot_bypass_replay(runtime) -> None:
  """K1-T3: non-replayable outcomes cannot be replayed."""
  identity = runtime.create_identity("A")
  decision = runtime.propose_and_execute(identity=identity.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]

  with pytest.raises(ConstitutionalError, match="K1"):
    outcome.replayable = False
