"""CRK-1.K3 — Anti-Insulation atomic tests."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError


def test_k3_cannot_fork_consequence_free_lineage(runtime) -> None:
  """K3-T1: child cannot escape ancestor consequence evidence."""
  parent = runtime.create_identity("P")
  child = runtime.create_identity("C", parent_identity_id=parent.id)

  decision = runtime.propose_and_execute(identity=parent.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]
  evidence = runtime.replay_outcome(outcome.id)

  visible = runtime.get_admissible_evidence(child.id)

  assert evidence in visible


def test_k3_cannot_mark_ancestor_evidence_irrelevant(runtime) -> None:
  """K3-T2: marking ancestor evidence irrelevant is forbidden."""
  parent = runtime.create_identity("P")
  child = runtime.create_identity("C", parent_identity_id=parent.id)

  decision = runtime.propose_and_execute(identity=parent.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]
  evidence = runtime.replay_outcome(outcome.id)

  with pytest.raises(ConstitutionalError, match="K3"):
    runtime.mark_evidence_irrelevant_for_identity(evidence.id, child.id)
