"""C12 inter-temporal governance and temporal coherence."""

from __future__ import annotations

from dataclasses import dataclass

from src.continuity.continuity_lattice import trace_leq
from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, d_conv
from src.continuity.inheritance import DEFAULT_INVARIANT_LAWS
from src.continuity.lineage import Lineage, continuity_trace


C12_CAPABILITY_ID = "C12-inter-temporal-governance"
DEFAULT_PHI_MIN_T = DEFAULT_PHI_MIN


@dataclass(frozen=True, slots=True)
class TemporalState:
    """Temporal layer t of a civilization with lineage L(t) and invariants Λ(t)."""

    temporal_id: str
    lineage: Lineage
    invariant_laws: frozenset[str] = DEFAULT_INVARIANT_LAWS

    def continuity(self) -> frozenset[str]:
        return continuity_trace(self.lineage)


def _meaning_field_compatible(past: Lineage, future: Lineage) -> bool:
    if past.meaning_class == future.meaning_class:
        return True
    return past.meaning_class.startswith("conv:") or future.meaning_class.startswith("conv:")


def temporal_convergence_fitness(past: TemporalState, future: TemporalState) -> float:
    """C12-4: Φ_t1,t2 = 1 - d_conv(L(t1), L(t2))."""

    return round(1.0 - d_conv(past.lineage, future.lineage), 6)


def evaluate_temporal_coherence(
    past: TemporalState,
    future: TemporalState,
    *,
    phi_min_t: float = DEFAULT_PHI_MIN_T,
) -> dict[str, object]:
    """C12 — temporal non-interference and coherence across t1 < t2."""

    continuity_ok = trace_leq(past.continuity(), future.continuity())
    invariants_ok = past.invariant_laws == future.invariant_laws
    phi_tt = temporal_convergence_fitness(past, future)
    phi_ok = phi_tt >= phi_min_t
    non_contradiction_ok = _meaning_field_compatible(past.lineage, future.lineage)
    passed = continuity_ok and invariants_ok and phi_ok and non_contradiction_ok
    return {
        "capability_id": C12_CAPABILITY_ID,
        "past": past.temporal_id,
        "future": future.temporal_id,
        "continuity_non_annihilation": continuity_ok,
        "invariant_preservation": invariants_ok,
        "temporal_non_contradiction": non_contradiction_ok,
        "phi_t1_t2": phi_tt,
        "phi_min_t": phi_min_t,
        "passed": passed,
    }
