"""Reusable verification gate policy for mission and review flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class GateDecision(str, Enum):
    """Stable verification gate outcomes."""

    BLOCK = "BLOCK"
    ELIGIBLE = "ELIGIBLE"


LAW_BREAK = "LAW_BREAK"
INTENT_MISS = "INTENT_MISS"
ROLE_DRIFT = "ROLE_DRIFT"
CONSTRAINT_FAIL = "CONSTRAINT_FAIL"
DRIFT_INSTABILITY = "DRIFT_INSTABILITY"


@dataclass(slots=True)
class VerificationTestResult:
    """One normalized verification test result consumed by the gate."""

    test_id: str
    law: int
    intent: int
    role: int
    constraint: int
    drift: int
    tags: set[str] = field(default_factory=set)
    is_repeat_test: bool = False


@dataclass(slots=True)
class GateEvaluation:
    """Decision plus the blocked tests and reasons."""

    decision: GateDecision
    reasons: list[str]
    failed_tests: list[str]


def _normalize_score(value, *, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def normalize_verification_result(raw: VerificationTestResult | dict) -> VerificationTestResult:
    """Coerce dict payloads into the gate's normalized result model."""
    if isinstance(raw, VerificationTestResult):
        return raw
    if not isinstance(raw, dict):
        raise TypeError("Verification result must be a dict or VerificationTestResult.")

    tags = {
        " ".join(str(tag or "").split()).strip().upper()
        for tag in list(raw.get("tags") or [])
        if " ".join(str(tag or "").split()).strip()
    }
    return VerificationTestResult(
        test_id=" ".join(str(raw.get("test_id") or "").split()).strip() or "unnamed_test",
        law=_normalize_score(raw.get("law")),
        intent=_normalize_score(raw.get("intent")),
        role=_normalize_score(raw.get("role")),
        constraint=_normalize_score(raw.get("constraint")),
        drift=_normalize_score(raw.get("drift")),
        tags=tags,
        is_repeat_test=bool(raw.get("is_repeat_test")),
    )


def normalize_verification_results(
    results: Iterable[VerificationTestResult | dict] | None,
) -> list[VerificationTestResult]:
    """Normalize a sequence of raw verification results."""
    normalized: list[VerificationTestResult] = []
    for raw in results or []:
        normalized.append(normalize_verification_result(raw))
    return normalized


def evaluate_verification_gate(results: list[VerificationTestResult]) -> GateEvaluation:
    """Evaluate whether verification evidence is eligible for mission admission."""
    reasons: list[str] = []
    failed_tests: list[str] = []
    role_drift_count = 0

    for result in results:
        if LAW_BREAK in result.tags:
            reasons.append(f"{result.test_id}: LAW_BREAK present")
            failed_tests.append(result.test_id)

        if INTENT_MISS in result.tags:
            reasons.append(f"{result.test_id}: INTENT_MISS present")
            failed_tests.append(result.test_id)

        if result.law < 2:
            reasons.append(f"{result.test_id}: Law < 2")
            failed_tests.append(result.test_id)

        if result.intent < 2:
            reasons.append(f"{result.test_id}: Intent < 2")
            failed_tests.append(result.test_id)

        if result.is_repeat_test and DRIFT_INSTABILITY in result.tags:
            reasons.append(f"{result.test_id}: DRIFT_INSTABILITY in repeat test")
            failed_tests.append(result.test_id)

        if ROLE_DRIFT in result.tags:
            role_drift_count += 1

    if role_drift_count > 1:
        reasons.append("ROLE_DRIFT occurred more than once")

    decision = GateDecision.BLOCK if reasons else GateDecision.ELIGIBLE

    return GateEvaluation(
        decision=decision,
        reasons=reasons,
        failed_tests=sorted(set(failed_tests)),
    )
