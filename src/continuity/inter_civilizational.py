"""C11 non-destructive inter-civilizational interoperability."""

from __future__ import annotations

from dataclasses import dataclass

from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, converge_many, d_conv
from src.continuity.inheritance import DEFAULT_INVARIANT_LAWS
from src.continuity.lineage import Lineage, continuity_trace


C11_CAPABILITY_ID = "C11-non-destructive-interoperability"
DEFAULT_PHI_MIN_AB = DEFAULT_PHI_MIN


@dataclass(frozen=True, slots=True)
class Civilization:
    """Civilization A or B with lineages and invariant law structure Λ."""

    civilization_id: str
    lineages: tuple[Lineage, ...]
    invariant_laws: frozenset[str] = DEFAULT_INVARIANT_LAWS

    def representative_lineage(self) -> Lineage:
        if not self.lineages:
            raise ValueError("civilization requires at least one lineage")
        if len(self.lineages) == 1:
            return self.lineages[0]
        merged, _ = converge_many(list(self.lineages))
        return merged


def cross_civilizational_fitness(civilization_a: Civilization, civilization_b: Civilization) -> float:
    """C11-4: Φ_AB = 1 - d_conv(L_A, L_B)."""

    left = civilization_a.representative_lineage()
    right = civilization_b.representative_lineage()
    return round(1.0 - d_conv(left, right), 6)


def evaluate_interoperability(
    civilization_a: Civilization,
    civilization_b: Civilization,
    *,
    phi_min_ab: float = DEFAULT_PHI_MIN_AB,
) -> dict[str, object]:
    """C11 — non-destructive interoperability between civilizations."""

    lineage_a = civilization_a.representative_lineage()
    lineage_b = civilization_b.representative_lineage()
    trace_a = continuity_trace(lineage_a)
    trace_b = continuity_trace(lineage_b)
    continuity_ok = bool(trace_a) and bool(trace_b)
    invariants_ok = bool(civilization_a.invariant_laws & civilization_b.invariant_laws)
    phi_ab = cross_civilizational_fitness(civilization_a, civilization_b)
    phi_ok = phi_ab >= phi_min_ab
    passed = continuity_ok and invariants_ok and phi_ok
    return {
        "capability_id": C11_CAPABILITY_ID,
        "civilization_a": civilization_a.civilization_id,
        "civilization_b": civilization_b.civilization_id,
        "continuity_non_interference": continuity_ok,
        "invariant_compatibility": invariants_ok,
        "shared_invariants": sorted(civilization_a.invariant_laws & civilization_b.invariant_laws),
        "phi_ab": phi_ab,
        "phi_min_ab": phi_min_ab,
        "passed": passed,
    }
