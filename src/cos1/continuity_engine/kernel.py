"""Continuity kernel K1–K3 — invariants required for compounding to survive."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEvent


class KernelInvariantResult(BaseModel):
    invariant_id: str
    name: str
    satisfied: bool
    violations: list[str] = Field(default_factory=list)


class ContinuityKernelAssessment(BaseModel):
    all_satisfied: bool
    invariants: list[KernelInvariantResult] = Field(default_factory=list)


def _check_k1_identity_coherence(events: list[ContinuityEngineEvent]) -> KernelInvariantResult:
    violations: list[str] = []
    for event in events:
        if not event.insight.lineage_compatible:
            violations.append(f"{event.event_id}: insight not lineage-compatible.")
        if event.origin.type == "DRIFT":
            violations.append(f"{event.event_id}: drift origin breaks identity coherence.")
        if event.origin.evidence.identity_breaking_divergence:
            violations.append(f"{event.event_id}: identity-breaking divergence detected.")

    return KernelInvariantResult(
        invariant_id="K1",
        name="Identity Coherence",
        satisfied=not violations,
        violations=violations,
    )


def _check_k2_generative_grammar(events: list[ContinuityEngineEvent]) -> KernelInvariantResult:
    violations: list[str] = []
    for event in events:
        if not event.insight.structural_alignment:
            violations.append(f"{event.event_id}: no structural alignment tags (grammar absent).")
        if event.insight.novelty_level == "ECHO":
            violations.append(f"{event.event_id}: ECHO novelty — no generative extension.")

    return KernelInvariantResult(
        invariant_id="K2",
        name="Generative Grammar",
        satisfied=not violations,
        violations=violations,
    )


def _check_k3_integrability(events: list[ContinuityEngineEvent]) -> KernelInvariantResult:
    violations: list[str] = []
    for event in events:
        acc = event.accumulation
        if acc.signature != "NONE" and not acc.returns_stronger:
            if acc.signature in {"A1", "A2", "A3"} and not event.insight.lineage_compatible:
                violations.append(
                    f"{event.event_id}: accumulation without lineage-compatible integrability."
                )
        if event.origin.type == "NOISE":
            violations.append(f"{event.event_id}: noise origin fragments lineage.")

    return KernelInvariantResult(
        invariant_id="K3",
        name="Integrability",
        satisfied=not violations,
        violations=violations,
    )


def assess_continuity_kernel(events: list[ContinuityEngineEvent]) -> ContinuityKernelAssessment:
    """Evaluate K1–K3 on the unified event log."""
    if not events:
        empty = [
            KernelInvariantResult(
                invariant_id=kid,
                name=name,
                satisfied=True,
                violations=[],
            )
            for kid, name in [("K1", "Identity Coherence"), ("K2", "Generative Grammar"), ("K3", "Integrability")]
        ]
        return ContinuityKernelAssessment(all_satisfied=True, invariants=empty)

    results = [
        _check_k1_identity_coherence(events),
        _check_k2_generative_grammar(events),
        _check_k3_integrability(events),
    ]
    return ContinuityKernelAssessment(
        all_satisfied=all(result.satisfied for result in results),
        invariants=results,
    )
