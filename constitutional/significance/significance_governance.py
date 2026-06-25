"""Significance succession gates — judgment, continuity, and evolution readiness."""

from __future__ import annotations

from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.significance_judgment_runtime import (
    SignificanceJudgmentRuntime,
    StewardSignificanceAnswer,
    load_significance_judgment_state,
)


def succession_significance_judgment_ready(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    steward_answers: dict[str, StewardSignificanceAnswer] | None = None,
) -> tuple[bool, list[str]]:
    """Require passing Significance Judgment Test v1 before succession."""
    if csr is None and steward_answers is None:
        return False, ["significance_judgment_not_evaluated"]

    if steward_answers is not None:
        result = SignificanceJudgmentRuntime().evaluate(steward_answers)
        if not result.passed:
            return False, [
                f"significance_judgment_failed_score_{result.score:.2f}",
                *result.failures,
            ]
        return True, []

    state = load_significance_judgment_state(csr)  # type: ignore[arg-type]
    if state is None or state.last_result is None:
        return False, ["significance_judgment_not_completed"]

    if not state.passed:
        score = state.last_result.score
        return False, [f"significance_judgment_failed_score_{score:.2f}", *state.last_result.failures]

    return True, []


def succession_significance_continuity_ready(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    steward_answers: dict[str, StewardSignificanceAnswer] | None = None,
) -> tuple[bool, list[str]]:
    """Require invariant/purpose linkage across all significance judgments."""
    judgment_ok, judgment_reasons = succession_significance_judgment_ready(
        csr,
        steward_answers=steward_answers,
    )
    if not judgment_ok:
        return False, judgment_reasons

    answers = steward_answers
    if answers is None and csr is not None:
        state = load_significance_judgment_state(csr)
        answers = state.steward_answers if state else {}

    reasons: list[str] = []
    for artifact_id, answer in (answers or {}).items():
        if not answer.invariant_links:
            reasons.append(f"significance_continuity_missing_invariants_{artifact_id}")
        if not answer.purpose_links:
            reasons.append(f"significance_continuity_missing_purpose_{artifact_id}")

    return not reasons, reasons


def succession_significance_evolution_ready(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    steward_answers: dict[str, StewardSignificanceAnswer] | None = None,
) -> tuple[bool, list[str]]:
    """Require articulated reclassification evidence for significance evolution."""
    judgment_ok, judgment_reasons = succession_significance_judgment_ready(
        csr,
        steward_answers=steward_answers,
    )
    if not judgment_ok:
        return False, judgment_reasons

    answers = steward_answers
    if answers is None and csr is not None:
        state = load_significance_judgment_state(csr)
        answers = state.steward_answers if state else {}

    reasons: list[str] = []
    for artifact_id, answer in (answers or {}).items():
        if not answer.evidence_that_would_change:
            reasons.append(f"significance_evolution_missing_evidence_{artifact_id}")

    return not reasons, reasons
