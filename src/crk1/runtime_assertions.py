"""CRK-1 Runtime Assertions — drop-in invariant guards for K0–K3."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from src.crk1.errors import ConstitutionalError

LineageResolver = Callable[[Any], Sequence[str]]


def assert_outcome_replayable(outcome: Any) -> None:
    if getattr(outcome, "replayable", None) is not True:
        raise ConstitutionalError("K1 violation: Outcome must be replayable")


def assert_evidence_admissible(evidence: Any) -> None:
    if getattr(evidence, "admissible_for_decision", None) is not True:
        raise ConstitutionalError("K1 violation: Evidence must be admissible")


def assert_decision_has_evidence(decision: Any) -> None:
    evidence_ids = getattr(decision, "input_evidence_ids", None)
    if evidence_ids is None:
        evidence_ids = getattr(decision, "evidence_refs", None)
    if not evidence_ids:
        raise ConstitutionalError("K2 violation: Decision requires Evidence")


def assert_decision_has_identity(decision: Any) -> None:
    if getattr(decision, "identity_id", None) is None:
        raise ConstitutionalError("K2 violation: Decision requires Identity")


def assert_lineage_inherits_evidence(
    identity: Any,
    evidence: Any,
    lineage_resolver: LineageResolver,
) -> None:
    lineage = set(lineage_resolver(identity))
    source = getattr(evidence, "source_identity_id", None)
    if source is None or str(source) not in lineage:
        raise ConstitutionalError("K3 violation: Lineage must inherit ancestor Evidence")


def assert_no_outcome_deletion() -> None:
    raise ConstitutionalError("K1 violation: Outcome deletion is forbidden")


def assert_no_evidence_quarantine() -> None:
    raise ConstitutionalError("K1 violation: Evidence quarantine is forbidden")


def assert_no_lineage_escape() -> None:
    raise ConstitutionalError("K3 violation: Lineage escape is forbidden")


def assert_replay_produces_evidence(evidence: Any) -> None:
    if evidence is None:
        raise ConstitutionalError("K0 violation: Replay must yield Evidence")
    assert_evidence_admissible(evidence)


def assert_execution_produces_outcome(outcome: Any) -> None:
    if outcome is None:
        raise ConstitutionalError("K0 violation: Decision execution must produce Outcome")
    assert_outcome_replayable(outcome)


def assert_no_evidence_irrelevance_mark() -> None:
    raise ConstitutionalError("K3 violation: cannot mark evidence irrelevant for identity")
