"""CRK-1 K4–K6 consequence transmission lattice tests."""

from __future__ import annotations

import pytest

from src.crk1.consequence_lattice import (
    ConsequenceExposure,
    apply_amendment_with_drift_check,
    assert_mutation_admissible,
    consequence_exposure,
    mutation_admissible,
    validate_drift_envelope,
)
from src.crk1.errors import ConstitutionalError
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator


def test_k5_rejects_insulating_mutation() -> None:
    assert mutation_admissible({"governance.quorum": 5}) is True
    assert mutation_admissible({"Outcome.replayable": False}) is False
    with pytest.raises(ConstitutionalError, match="K5 violation"):
        assert_mutation_admissible({"lineage_rules": "disable"})


def test_k6_drift_envelope() -> None:
    before = ConsequenceExposure(
        score=0.9,
        outcome_replayable_ratio=1.0,
        evidence_admissible_ratio=1.0,
        lineage_exposure_ratio=0.8,
        judgment_coupling_ratio=1.0,
        transmission_loop_ratio=0.8,
    )
    after_ok = ConsequenceExposure(
        score=0.95,
        outcome_replayable_ratio=1.0,
        evidence_admissible_ratio=1.0,
        lineage_exposure_ratio=1.0,
        judgment_coupling_ratio=1.0,
        transmission_loop_ratio=0.75,
    )
    after_bad = ConsequenceExposure(
        score=0.5,
        outcome_replayable_ratio=0.5,
        evidence_admissible_ratio=1.0,
        lineage_exposure_ratio=0.5,
        judgment_coupling_ratio=0.5,
        transmission_loop_ratio=0.5,
    )
    validate_drift_envelope(before, after_ok)
    with pytest.raises(ConstitutionalError, match="K6 violation"):
        validate_drift_envelope(before, after_bad)


def test_ce_function_on_runtime(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    root = crk1_runtime.ledgers.identity.id
    facade.propose_and_execute(identity=root, evidence=["EVD-CRK1-001"])
    ce = consequence_exposure(facade)
    assert 0.0 < ce.score <= 1.0
    assert ce.outcome_replayable_ratio == 1.0


def test_validator_k4_k5_k6(crk1_runtime) -> None:
    validator = CRK1RuntimeValidator()
    with pytest.raises(ConstitutionalError, match="K5 violation"):
        validator.validate_k5({"Outcome.replayable": False})

    before = ConsequenceExposure(0.8, 1, 1, 1, 1, 0.6)
    after = ConsequenceExposure(0.9, 1, 1, 1, 1, 0.7)
    validator.validate_k6(before, after)

    with pytest.raises(ConstitutionalError, match="K6 violation"):
        validator.validate_k6(before, ConsequenceExposure(0.5, 0.5, 1, 1, 1, 0.5))


def test_apply_amendment_with_drift_check(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    root = crk1_runtime.ledgers.identity.id
    facade.propose_and_execute(identity=root, evidence=["EVD-CRK1-001"])
    ce = apply_amendment_with_drift_check(facade, {"governance.quorum": 3})
    assert ce.score > 0
