"""ROOT-00Y governed evolution and C10 emergent stewardship metrics."""

from __future__ import annotations

from src.continuity.continuity_lattice import lci_holds
from src.continuity.convergence_algebra import (
    DEFAULT_PHI_MIN,
    convergence_fitness,
    converge_many,
    proximity_to_convergence,
)
from src.continuity.lineage import Lineage


DEFAULT_S_MIN = 0.65
GOVERNED_EVOLUTION_CAPABILITY_ID = "ROOT-00Y-governed-evolution"
STEWARDSHIP_CAPABILITY_ID = "C10-emergent-stewardship"


def stewardship_score(operator_lineage: Lineage, converged: Lineage) -> float:
    """C10-3: S(o) = 1 - d_conv(L_o, L*)."""

    return round(1.0 - proximity_to_convergence(operator_lineage, converged), 6)


def evaluate_stewardship(
    lineages: list[Lineage],
    *,
    s_min: float = DEFAULT_S_MIN,
) -> dict[str, object]:
    """C10 — every operator lineage must maintain S(o) >= S_min."""

    if not lineages:
        return {
            "capability_id": STEWARDSHIP_CAPABILITY_ID,
            "passed": True,
            "s_min": s_min,
            "scores": [],
            "merged_lineage_id": None,
        }

    fitness = convergence_fitness(lineages)
    merged_id = fitness.get("merged_lineage_id")
    if len(lineages) == 1:
        converged = lineages[0]
    else:
        converged, _ = converge_many(lineages)

    scores = [
        {
            "lineage_id": item.lineage_id,
            "operator_id": item.metadata.get("operator_id", item.lineage_id),
            "score": stewardship_score(item, converged),
        }
        for item in lineages
    ]
    passed = all(float(row["score"]) >= s_min for row in scores)
    return {
        "capability_id": STEWARDSHIP_CAPABILITY_ID,
        "passed": passed,
        "s_min": s_min,
        "scores": scores,
        "merged_lineage_id": merged_id or converged.lineage_id,
    }


def validate_lineage_evolution(
    before: Lineage,
    after: Lineage,
    active_lineages: list[Lineage],
    *,
    phi_min: float = DEFAULT_PHI_MIN,
) -> dict[str, object]:
    """ROOT-00Y §3 — evolution must extend continuity and preserve Φ."""

    lci_ok = lci_holds(before, after)
    evolved_active = [
        after if item.lineage_id == before.lineage_id else item for item in active_lineages
    ]
    fitness = convergence_fitness(evolved_active, phi_min=phi_min)
    fitness_ok = bool(fitness["passed"])
    return {
        "capability_id": GOVERNED_EVOLUTION_CAPABILITY_ID,
        "lci_ok": lci_ok,
        "fitness_ok": fitness_ok,
        "phi": fitness.get("phi"),
        "phi_min": phi_min,
        "passed": lci_ok and fitness_ok,
    }


def governed_evolution_admissible(
    before: Lineage,
    after: Lineage,
    active_lineages: list[Lineage],
    *,
    phi_min: float = DEFAULT_PHI_MIN,
    s_min: float = DEFAULT_S_MIN,
) -> dict[str, object]:
    """Evolution = Creation ∩ Convergence — LCI-preserving and converge-able."""

    evolution = validate_lineage_evolution(
        before,
        after,
        active_lineages,
        phi_min=phi_min,
    )
    evolved_active = [
        after if item.lineage_id == before.lineage_id else item for item in active_lineages
    ]
    stewardship = evaluate_stewardship(evolved_active, s_min=s_min)
    passed = bool(evolution["passed"]) and bool(stewardship["passed"])
    return {
        "capability_id": GOVERNED_EVOLUTION_CAPABILITY_ID,
        "evolution": evolution,
        "stewardship": stewardship,
        "passed": passed,
    }
