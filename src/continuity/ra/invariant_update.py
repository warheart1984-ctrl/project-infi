"""Consequence-weighted invariant update rule."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from src.continuity.ra.models import Invariant, InvariantStatus
from src.continuity.ra.spec import (
    DEFAULT_LEARNING_RATE,
    INVARIANT_DEPRECATION_THRESHOLD,
    INVARIANT_REVIEW_THRESHOLD,
)


class InvariantUpdateResult(BaseModel):
    invariant_id: str
    prior_weight: float
    new_weight: float
    evidence_score: float
    new_status: InvariantStatus
    action: str


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def update_invariant_weight(
    inv: Invariant,
    evidence_score: float,
    *,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> Invariant:
    """
    w_k' = σ(log(w_k / (1 - w_k)) + η · c_k · e_k)

    High-impact invariants (large c_k) move more cautiously for the same evidence.
    """
    w = min(max(inv.weight, 1e-6), 1.0 - 1e-6)
    logit = math.log(w / (1.0 - w))
    updated_logit = logit + learning_rate * inv.impact * evidence_score
    new_w = logistic(updated_logit)
    return inv.model_copy(update={"weight": new_w})


def resolve_invariant_status(weight: float, prior: InvariantStatus) -> InvariantStatus:
    if weight < INVARIANT_DEPRECATION_THRESHOLD:
        return "DEPRECATED"
    if weight < INVARIANT_REVIEW_THRESHOLD:
        return "UNDER_REVIEW"
    return "ACTIVE" if prior != "DEPRECATED" else "UNDER_REVIEW"


def apply_invariant_update(
    inv: Invariant,
    evidence_score: float,
    *,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> InvariantUpdateResult:
    clamped_evidence = max(-1.0, min(1.0, evidence_score))
    updated = update_invariant_weight(inv, clamped_evidence, learning_rate=learning_rate)
    new_status = resolve_invariant_status(updated.weight, inv.status)
    updated = updated.model_copy(update={"status": new_status})

    if clamped_evidence > 0:
        action = "Increased confidence in invariant."
    elif clamped_evidence < 0:
        action = "Decreased confidence; review or deprecate if below threshold."
    else:
        action = "No weight change from neutral evidence."

    return InvariantUpdateResult(
        invariant_id=inv.id,
        prior_weight=inv.weight,
        new_weight=updated.weight,
        evidence_score=clamped_evidence,
        new_status=new_status,
        action=action,
    )


def update_invariants_from_validation(
    invariants: dict[str, Invariant],
    change_affects: list[str],
    evidence_score: float,
    *,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> tuple[dict[str, Invariant], list[InvariantUpdateResult]]:
    """Update weights for invariants touched by a validated or rejected change."""
    results: list[InvariantUpdateResult] = []
    updated = dict(invariants)
    targets = change_affects or list(invariants.keys())

    for inv_id in targets:
        inv = updated.get(inv_id)
        if inv is None:
            continue
        result = apply_invariant_update(inv, evidence_score, learning_rate=learning_rate)
        updated[inv_id] = inv.model_copy(
            update={"weight": result.new_weight, "status": result.new_status}
        )
        results.append(result)

    return updated, results
