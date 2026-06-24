"""CRK-1 unified insulation attack suite — continuity health check."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.schema_validator import SchemaValidationError
from tests.crk1.conftest import now_iso, uuid4_str


def test_insulation_attack_suite(runtime, schema_validator) -> None:
  """
  CRK-1 Continuity Health Check:
  System must reject all insulation attempts.
  """
  identity = runtime.create_identity("A")

  decision = runtime.propose_and_execute(identity=identity.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]

  with pytest.raises(ConstitutionalError, match="K1"):
    runtime.delete_outcome(outcome.id)

  evidence = runtime.replay_outcome(outcome.id)
  with pytest.raises(ConstitutionalError, match="K1"):
    runtime.mark_evidence_non_admissible(evidence.id)

  invalid_outcome = {
    "id": uuid4_str(),
    "decision_id": uuid4_str(),
    "status": "success",
    "replayable": False,
    "created_at": now_iso(),
  }
  with pytest.raises(SchemaValidationError):
    schema_validator.validate("OutcomeObject", invalid_outcome)

  invalid_evidence = {
    "id": uuid4_str(),
    "source_type": "outcome",
    "source_outcome_id": uuid4_str(),
    "admissible_for_decision": False,
    "created_at": now_iso(),
  }
  with pytest.raises(SchemaValidationError):
    schema_validator.validate("EvidenceObject", invalid_evidence)

  invalid_decision = {
    "id": uuid4_str(),
    "identity_id": uuid4_str(),
    "status": "proposed",
    "input_evidence_ids": [],
    "created_at": now_iso(),
  }
  with pytest.raises(SchemaValidationError):
    schema_validator.validate("DecisionObject", invalid_decision)

  parent = runtime.create_identity("P")
  child = runtime.create_identity("C", parent_identity_id=parent.id)

  decision2 = runtime.propose_and_execute(identity=parent.id, evidence=["E2"])
  outcome2 = runtime.get_outcomes(decision2.id)[0]
  evidence2 = runtime.replay_outcome(outcome2.id)

  visible = runtime.get_admissible_evidence(child.id)
  assert evidence2 in visible
