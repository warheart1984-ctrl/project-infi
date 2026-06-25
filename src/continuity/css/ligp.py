"""LIGP-1 — Lineage Identity Governance Protocol."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEvent
from src.cos1.continuity_engine.kernel import ContinuityKernelAssessment, assess_continuity_kernel
from src.cos1.continuity_engine.spec import CONTINUITY_KERNEL_INVARIANTS

LIGP1_REFERENCE = "Lineage Identity Governance Protocol LIGP-1"

GOVERNANCE_RULE = (
    "Any extension that violates K1–K3 is drift, not evolution."
)

INVARIANT_K1 = "K1 — Identity Coherence"
INVARIANT_K2 = "K2 — Generative Grammar"
INVARIANT_K3 = "K3 — Integrability"
INVARIANT_K4 = "K4 — Reconstructability Protection"

GOVERNANCE_RULE_K1_K3 = GOVERNANCE_RULE
GOVERNANCE_RULE_FULL = (
    "Any extension that violates K1–K4 is drift, not evolution."
)


class InvariantViolation(BaseModel):
    event_id: str
    invariant_id: str
    description: str


class LIGPAssessment(BaseModel):
    reference: str = LIGP1_REFERENCE
    governance_rule: str = GOVERNANCE_RULE
    kernel: ContinuityKernelAssessment
    drift_events: list[str] = Field(default_factory=list)
    evolution_events: list[str] = Field(default_factory=list)
    identity_preserved: bool = False


def assess_ligp(events: list[ContinuityEngineEvent]) -> LIGPAssessment:
    """Evaluate K1–K3 and classify drift vs evolution."""
    kernel = assess_continuity_kernel(events)
    drift: list[str] = []
    evolution: list[str] = []

    for event in events:
        if event.origin.type in ("DRIFT", "NOISE"):
            drift.append(event.event_id)
        elif not event.insight.lineage_compatible:
            drift.append(event.event_id)
        else:
            evolution.append(event.event_id)

    return LIGPAssessment(
        kernel=kernel,
        drift_events=drift,
        evolution_events=evolution,
        identity_preserved=kernel.all_satisfied and not drift,
    )


def format_ligp_invariants() -> str:
    lines = [f"=== {LIGP1_REFERENCE} ===", "", GOVERNANCE_RULE, ""]
    lines.extend(CONTINUITY_KERNEL_INVARIANTS)
    return "\n".join(lines)
