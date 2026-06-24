"""
CRK-1 K4–K6 — Consequence Transmission Lattice.

K4: Consequence Preservation Law
K5: Mutation Admissibility Test
K6: Constitutional Drift Envelope (CE function)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.crk1.errors import ConstitutionalError
from src.crk1.runtime_facade import CRK1Runtime


@dataclass(frozen=True)
class ConsequenceExposure:
    """CE(S) — degree to which consequences propagate into judgment."""

    score: float
    outcome_replayable_ratio: float
    evidence_admissible_ratio: float
    lineage_exposure_ratio: float
    judgment_coupling_ratio: float
    transmission_loop_ratio: float

    def to_dict(self) -> dict[str, float]:
        return {
            "score": self.score,
            "outcome_replayable_ratio": self.outcome_replayable_ratio,
            "evidence_admissible_ratio": self.evidence_admissible_ratio,
            "lineage_exposure_ratio": self.lineage_exposure_ratio,
            "judgment_coupling_ratio": self.judgment_coupling_ratio,
            "transmission_loop_ratio": self.transmission_loop_ratio,
        }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return numerator / denominator


def consequence_exposure(runtime: CRK1Runtime) -> ConsequenceExposure:
    """
    CE(S) = degree to which consequences propagate into judgment.

    Combines five exposure dimensions from K5:
    - Outcome replayability
    - Evidence admissibility
    - Lineage exposure per identity
    - Judgment coupling (decisions require evidence)
    - Outcome → Evidence → Decision loop completeness
    """
    outcomes = runtime.get_all_outcomes()
    evidence_items = runtime.get_all_evidence()
    identities = runtime.get_all_identities()
    decisions = runtime.kernel.decisions.list_decisions()

    outcome_replayable_ratio = _ratio(
        sum(1 for outcome in outcomes if outcome.replayable is True),
        len(outcomes),
    )

    evidence_admissible_ratio = _ratio(
        sum(1 for item in evidence_items if item.admissible_for_decision is True),
        len(evidence_items),
    )

    lineage_hits = 0
    for identity in identities:
        if runtime.get_admissible_evidence(identity.id):
            lineage_hits += 1
    lineage_exposure_ratio = _ratio(lineage_hits, len(identities))

    judgment_coupling_ratio = _ratio(
        sum(1 for decision in decisions if decision.evidence_refs),
        len(decisions),
    )

    loop_complete = 0
    for decision in decisions:
        has_outcome = bool(runtime.get_outcomes(decision.id))
        has_evidence = bool(decision.evidence_refs)
        if has_outcome and has_evidence:
            loop_complete += 1
    transmission_loop_ratio = _ratio(loop_complete, len(decisions))

    score = (
        outcome_replayable_ratio
        + evidence_admissible_ratio
        + lineage_exposure_ratio
        + judgment_coupling_ratio
        + transmission_loop_ratio
    ) / 5.0

    return ConsequenceExposure(
        score=score,
        outcome_replayable_ratio=outcome_replayable_ratio,
        evidence_admissible_ratio=evidence_admissible_ratio,
        lineage_exposure_ratio=lineage_exposure_ratio,
        judgment_coupling_ratio=judgment_coupling_ratio,
        transmission_loop_ratio=transmission_loop_ratio,
    )


# ------------------------------------------------------------
# K5 — Mutation Admissibility Test
# ------------------------------------------------------------

_FORBIDDEN_MUTATION_KEYS: frozenset[str] = frozenset(
    {
        "Outcome.replayable",
        "Evidence.admissible_for_decision",
        "lineage_rules",
        "Decision.input_evidence_required",
        "block_consequence_propagation",
        "insulate_judgment_from_outcomes",
    }
)


def mutation_admissible(changes: dict[str, Any]) -> bool:
    """
    K5: M is admissible iff all Preserves(M, ·) predicates hold.

    Returns True when the mutation does not reduce consequence exposure.
    """
    if changes.get("Outcome.replayable") is False:
        return False

    if changes.get("Evidence.admissible_for_decision") is False:
        return False

    if changes.get("lineage_rules") == "disable":
        return False

    if changes.get("Decision.input_evidence_required") is False:
        return False

    if changes.get("block_consequence_propagation") is True:
        return False

    if changes.get("insulate_judgment_from_outcomes") is True:
        return False

    return True


def assert_mutation_admissible(changes: dict[str, Any]) -> None:
    if not mutation_admissible(changes):
        raise ConstitutionalError("K5 violation: mutation is inadmissible — reduces consequence exposure")


# ------------------------------------------------------------
# K4 — Consequence Preservation Law
# ------------------------------------------------------------


def validate_consequence_preservation(
    runtime: CRK1Runtime,
    *,
    changes: dict[str, Any] | None = None,
) -> None:
    """
    K4: Constitutional change C is valid iff the transmission loop remains intact
    and no change blocks consequences from reaching judgment.
    """
    assert_mutation_admissible(changes or {})

    ce = consequence_exposure(runtime)
    if ce.transmission_loop_ratio < 1.0 and runtime.get_all_outcomes():
        incomplete = [
            decision.id
            for decision in runtime.kernel.decisions.list_decisions()
            if decision.evidence_refs and not runtime.get_outcomes(decision.id)
        ]
        if incomplete:
            raise ConstitutionalError(
                f"K4 violation: decisions without outcome transmission: {incomplete[:3]}",
            )

    if ce.outcome_replayable_ratio < 1.0:
        raise ConstitutionalError("K4 violation: non-replayable outcomes break consequence transmission")

    if ce.evidence_admissible_ratio < 1.0:
        raise ConstitutionalError("K4 violation: inadmissible evidence breaks consequence transmission")


# ------------------------------------------------------------
# K6 — Constitutional Drift Envelope
# ------------------------------------------------------------


def validate_drift_envelope(
    ce_before: ConsequenceExposure,
    ce_after: ConsequenceExposure,
) -> None:
    """K6: CE(S_{t+1}) >= CE(S_t). Drift downhill into insulation is unconstitutional."""
    if ce_after.score + 1e-9 < ce_before.score:
        raise ConstitutionalError(
            f"K6 violation: unconstitutional drift — CE dropped from "
            f"{ce_before.score:.4f} to {ce_after.score:.4f}",
        )


def apply_amendment_with_drift_check(
    runtime: CRK1Runtime,
    changes: dict[str, Any],
) -> ConsequenceExposure:
    """Apply amendment only if K5 and K6 pass."""
    assert_mutation_admissible(changes)
    ce_before = consequence_exposure(runtime)
    runtime.apply_amendment(changes)
    ce_after = consequence_exposure(runtime)
    try:
        validate_drift_envelope(ce_before, ce_after)
    except ConstitutionalError:
        runtime._amendments.pop()  # noqa: SLF001 — rollback failed drift
        raise
    runtime._last_consequence_exposure = ce_after  # noqa: SLF001
    return ce_after
