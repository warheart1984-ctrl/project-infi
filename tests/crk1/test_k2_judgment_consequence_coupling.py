"""CRK-1.K2 — Judgment–Consequence Coupling atomic tests."""

from __future__ import annotations

import pytest

from src.crk1.schema_validator import SchemaValidationError
from tests.crk1.conftest import now_iso, uuid4_str


def test_k2_identity_must_see_own_outcome_evidence(runtime) -> None:
  """K2-T1: identity must see evidence from its own outcomes."""
  identity = runtime.create_identity("A")

  decision = runtime.propose_and_execute(identity=identity.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]
  evidence = runtime.replay_outcome(outcome.id)

  visible = runtime.get_admissible_evidence(identity.id)

  assert evidence in visible


def test_k2_lineage_must_inherit_ancestor_evidence(runtime) -> None:
  """K2-T2: child lineage inherits parent consequence evidence."""
  parent = runtime.create_identity("P")
  child = runtime.create_identity("C", parent_identity_id=parent.id)

  decision = runtime.propose_and_execute(identity=parent.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]
  evidence = runtime.replay_outcome(outcome.id)

  visible = runtime.get_admissible_evidence(child.id)

  assert evidence in visible


def test_k2_decision_requires_evidence(schema_validator) -> None:
  """K2-T3: schema rejects decisions without evidence."""
  invalid = {
    "id": uuid4_str(),
    "identity_id": uuid4_str(),
    "status": "proposed",
    "input_evidence_ids": [],
    "created_at": now_iso(),
  }

  with pytest.raises(SchemaValidationError):
    schema_validator.validate("DecisionObject", invalid)
