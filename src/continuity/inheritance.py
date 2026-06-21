"""ROOT-00Z inheritable continuity and operator succession."""

from __future__ import annotations

from dataclasses import dataclass

from src.continuity.continuity_lattice import lci_holds, trace_leq
from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, convergence_fitness
from src.continuity.lineage import Lineage, continuity_trace, generativity


ROOT_00Z_CAPABILITY_ID = "ROOT-00Z-inheritable-continuity"

DEFAULT_INVARIANT_LAWS: frozenset[str] = frozenset(
    {
        "UGR-C8",
        "UGR-C9",
        "UGR-C10",
        "ugr.continuity",
        "ugr.constitution",
    }
)


@dataclass(frozen=True, slots=True)
class OperatorState:
    """Operator o with continuity trace K_o and invariant structure Λ(o)."""

    operator_id: str
    lineage: Lineage
    invariant_laws: frozenset[str] = DEFAULT_INVARIANT_LAWS

    def continuity(self) -> frozenset[str]:
        return continuity_trace(self.lineage)


def validate_operator_succession(
    predecessor: OperatorState,
    successor: OperatorState,
    civilization_lineages: list[Lineage],
    *,
    phi_min: float = DEFAULT_PHI_MIN,
) -> dict[str, object]:
    """ROOT-00Z — lawful operator succession o → o'."""

    continuity_ok = trace_leq(predecessor.continuity(), successor.continuity())
    invariants_ok = predecessor.invariant_laws == successor.invariant_laws
    generativity_ok = generativity(successor.lineage) >= generativity(predecessor.lineage)
    lci_ok = lci_holds(predecessor.lineage, successor.lineage)
    fitness = convergence_fitness(civilization_lineages, phi_min=phi_min)
    fitness_ok = bool(fitness["passed"])
    passed = continuity_ok and invariants_ok and generativity_ok and lci_ok and fitness_ok
    return {
        "capability_id": ROOT_00Z_CAPABILITY_ID,
        "predecessor_id": predecessor.operator_id,
        "successor_id": successor.operator_id,
        "continuity_ok": continuity_ok,
        "invariants_ok": invariants_ok,
        "generativity_ok": generativity_ok,
        "lci_ok": lci_ok,
        "fitness_ok": fitness_ok,
        "phi": fitness.get("phi"),
        "phi_min": phi_min,
        "passed": passed,
    }


def operator_state_from_lineage(lineage: Lineage) -> OperatorState:
    operator_id = str(lineage.metadata.get("operator_id") or lineage.metadata.get("operator") or lineage.lineage_id)
    declared = lineage.metadata.get("invariant_laws")
    laws = frozenset(str(item) for item in declared) if declared else DEFAULT_INVARIANT_LAWS
    return OperatorState(operator_id=operator_id, lineage=lineage, invariant_laws=laws)
