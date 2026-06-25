"""Bridge between COS-1 ContinuityMemory and constitutional layer registers (1–7)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.register import StewardAbilityRegister


class LayerRegisterCounts(BaseModel):
    """Entry counts per continuity layer — lightweight artifact health snapshot."""

    decisions: int = 0
    outcomes: int = 0
    perceptions: int = 0
    reflections: int = 0
    invariants: int = 0
    constitutional_decisions: int = 0
    certified_stewards: int = 0
    stewardability_events: int = 0


class ContinuityRegisterSnapshot(BaseModel):
    """Snapshot of Layers 1–7 plus stewardability runtime ledger."""

    synced_at: str
    counts: LayerRegisterCounts = Field(default_factory=LayerRegisterCounts)
    has_eck2_pipeline: bool = False
    has_jpss_cycle: bool = False
    epistemic_ready: bool = False
    artifacts_populated: bool = False


def sync_constitutional_registers(
    csr: object,
    stewardability_register: StewardAbilityRegister,
) -> ContinuityRegisterSnapshot:
    """Load constitutional domain registers into a continuity snapshot."""
    from datetime import UTC, datetime

    from constitutional.eck2.runtime import load_eck2_pipeline
    from constitutional.jpss.constitutional_register import load_constitutional_register
    from constitutional.jpss.invariant_register import load_invariant_register
    from constitutional.jpss.registers import (
        load_decision_register,
        load_outcome_register,
        load_perception_register,
        load_reflection_register,
    )
    from constitutional.jpss.runtime import load_jpss_cycle
    from constitutional.legitimacy.legitimacy_register import load_legitimacy_register

    decision_reg = load_decision_register(csr)
    outcome_reg = load_outcome_register(csr)
    perception_reg = load_perception_register(csr)
    reflection_reg = load_reflection_register(csr)
    invariant_reg = load_invariant_register(csr)
    constitutional_reg = load_constitutional_register(csr)
    legitimacy_reg = load_legitimacy_register(csr)

    pipeline = load_eck2_pipeline(csr)
    cycle = load_jpss_cycle(csr)

    counts = LayerRegisterCounts(
        decisions=len(decision_reg.entries),
        outcomes=len(outcome_reg.entries),
        perceptions=len(perception_reg.entries),
        reflections=len(reflection_reg.entries),
        invariants=len(invariant_reg.entries),
        constitutional_decisions=len(constitutional_reg.entries),
        certified_stewards=len(legitimacy_reg.active_stewards()),
        stewardability_events=len(stewardability_register.events),
    )

    artifacts_populated = any(
        [
            counts.decisions > 0,
            counts.invariants > 0,
            counts.constitutional_decisions > 0,
            counts.certified_stewards > 0,
        ]
    )

    epistemic_ready = (
        counts.decisions > 0
        and counts.perceptions > 0
        and (pipeline is not None or counts.reflections > 0)
    )

    return ContinuityRegisterSnapshot(
        synced_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        counts=counts,
        has_eck2_pipeline=pipeline is not None,
        has_jpss_cycle=cycle is not None,
        epistemic_ready=epistemic_ready,
        artifacts_populated=artifacts_populated,
    )


def epistemic_conditions_from_snapshot(snapshot: ContinuityRegisterSnapshot) -> dict[str, bool]:
    """Map register snapshot to stewardability epistemic viability signals."""
    return {
        "history_accessible": snapshot.artifacts_populated,
        "registers_complete_enough": snapshot.epistemic_ready,
        "failures_visible": snapshot.counts.reflections > 0,
        "reasoning_transparent": snapshot.has_eck2_pipeline or snapshot.has_jpss_cycle,
    }
