"""K4 — Reconstructability Invariant (anti-entropy layer)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css.spec import K4_REFERENCE, K4_REQUIREMENTS
from src.cos1.accumulation.chain_detector import (
    ClassifiedAccumulationEvent,
    detect_compounding_chains,
)
from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEventLog

DEFAULT_RECONSTRUCTION_COMPLEXITY_THRESHOLD = 5.0
DEFAULT_COGNITIVE_LOAD_RATIO = 3.0


class K4Assessment(BaseModel):
    reference: str = K4_REFERENCE
    satisfied: bool = False
    max_chain_length: int = 0
    accumulation_to_transmission_ratio: float = 0.0
    grammar_coverage: float = 0.0
    bounded_complexity: bool = False
    survivable_cognitive_load: bool = False
    violations: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def assess_k4(
    ce_log: ContinuityEngineEventLog,
    *,
    max_chain_threshold: float = DEFAULT_RECONSTRUCTION_COMPLEXITY_THRESHOLD,
    max_accumulation_ratio: float = DEFAULT_COGNITIVE_LOAD_RATIO,
) -> K4Assessment:
    """
    K4 — Reconstructability: future stewards can reconstruct the lineage after accumulation.

    Without K4: accumulation destroys transferability → stewardability → continuity.
    """
    events = ce_log.events
    acc_events = ce_log.accumulation_events()
    violations: list[str] = []
    notes: list[str] = []

    classified = [
        ClassifiedAccumulationEvent(
            event_id=event.event_id,
            actor_id=event.actor.id,
            accumulation_signature=event.accumulation.signature,
            builds_on_event_ids=list(event.accumulation.builds_on_event_ids),
        )
        for event in acc_events
    ]
    chains = detect_compounding_chains(classified)
    max_chain = max((chain.length for chain in chains), default=0)

    p = len(ce_log.propagation_events())
    c = len(ce_log.convergence_events())
    transmission = p + c
    a = len(acc_events)
    ratio = a / max(transmission, 1)

    with_grammar = sum(1 for event in events if event.insight.structural_alignment)
    grammar_coverage = with_grammar / max(len(events), 1)

    bounded = max_chain <= max_chain_threshold
    survivable_load = ratio <= max_accumulation_ratio

    if not bounded:
        violations.append(
            f"Compounding chain length {max_chain} exceeds reconstructability threshold "
            f"{max_chain_threshold}."
        )
    if not survivable_load:
        violations.append(
            f"Accumulation/transmission ratio {ratio:.2f} exceeds cognitive load bound "
            f"{max_accumulation_ratio}."
        )
    if grammar_coverage < 0.5 and len(events) >= 3:
        violations.append(
            f"Grammar coverage {grammar_coverage:.2f} too low — lineage lacks modularity."
        )

    if bounded:
        notes.append("Bounded complexity: chain depth within threshold.")
    if survivable_load:
        notes.append("Survivable cognitive load: accumulation not outpacing transmission.")
    if grammar_coverage >= 0.5:
        notes.append("Grammar-level coherence maintained.")

    return K4Assessment(
        satisfied=not violations,
        max_chain_length=max_chain,
        accumulation_to_transmission_ratio=round(ratio, 4),
        grammar_coverage=round(grammar_coverage, 4),
        bounded_complexity=bounded,
        survivable_cognitive_load=survivable_load,
        violations=violations,
        notes=notes,
    )


def format_k4_requirements() -> str:
    lines = [f"=== {K4_REFERENCE} ===", ""]
    lines.extend(K4_REQUIREMENTS)
    return "\n".join(lines)
