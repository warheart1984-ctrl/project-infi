"""CRK-1.K0 — Consequence Transmission atomic tests."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.schema_validator import SchemaValidationError
from tests.crk1.conftest import now_iso, uuid4_str


def test_k0_execution_must_produce_outcome(runtime) -> None:
  """K0-T1: execution without outcome is unconstitutional."""
  identity = runtime.create_identity("A")
  decision = runtime.propose_decision(identity=identity.id, evidence=["E1"])

  runtime._disable_outcome_creation = True

  with pytest.raises(ConstitutionalError, match="K0"):
    runtime.execute_decision(decision.id)


def test_k0_outcome_must_be_replayable(schema_validator) -> None:
  """K0-T2: schema rejects non-replayable outcomes."""
  invalid = {
    "id": uuid4_str(),
    "decision_id": uuid4_str(),
    "status": "success",
    "replayable": False,
    "created_at": now_iso(),
  }

  with pytest.raises(SchemaValidationError):
    schema_validator.validate("OutcomeObject", invalid)


def test_k0_replay_yields_admissible_evidence(runtime) -> None:
  """K0-T3: replay must yield admissible evidence."""
  identity = runtime.create_identity("A")
  decision = runtime.propose_and_execute(identity=identity.id, evidence=["E1"])
  outcome = runtime.get_outcomes(decision.id)[0]

  evidence = runtime.replay_outcome(outcome.id)

  assert evidence.admissible_for_decision is True
