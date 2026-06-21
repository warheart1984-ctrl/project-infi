"""CONVERGE-1001 — convergence algebra, metric, and reconciliation operator."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.continuity.continuity_lattice import convergence_respects_lattice, trace_join
from src.continuity.lineage import Lineage, continuity_trace, generativity


CONVERGE_CAPABILITY_ID = "CONVERGE-1001"
DEFAULT_CONVERGENCE_EPSILON = 0.35


class ConvergenceError(RuntimeError):
    """Raised when lineages cannot be lawfully reconciled."""


@dataclass(frozen=True, slots=True)
class ConvergenceProof:
    """Audit record for a convergence product."""

    left_id: str
    right_id: str
    result_id: str
    epsilon: float
    distance_left: float
    distance_right: float
    idempotent: bool
    commutative: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": CONVERGE_CAPABILITY_ID,
            "left_id": self.left_id,
            "right_id": self.right_id,
            "result_id": self.result_id,
            "epsilon": self.epsilon,
            "distance_left": self.distance_left,
            "distance_right": self.distance_right,
            "idempotent": self.idempotent,
            "commutative": self.commutative,
        }


def _meanings_compatible(left: str, right: str) -> bool:
    if left == right:
        return True
    return left.startswith("conv:") or right.startswith("conv:")


def d_conv(left: Lineage, right: Lineage) -> float:
    """General divergence between lineages (symmetric trace + semantic)."""

    if not _meanings_compatible(left.meaning_class, right.meaning_class):
        return 1.0

    union = continuity_trace(left) | continuity_trace(right)
    if not union:
        return 0.0
    intersection = len(continuity_trace(left) & continuity_trace(right))
    return 1.0 - (intersection / len(union))


def proximity_to_convergence(source: Lineage, converged: Lineage) -> float:
    """d_conv(L_i, L1 ⊗ L2) — distance from lineage to its converged product."""

    if not _meanings_compatible(source.meaning_class, converged.meaning_class):
        return 1.0
    if not continuity_trace(source) <= continuity_trace(converged):
        missing = len(continuity_trace(source) - continuity_trace(converged))
        return missing / max(1, len(continuity_trace(source)))
    return 0.0


def _merged_meaning_class(left: Lineage, right: Lineage) -> str:
    if left.meaning_class == right.meaning_class:
        return left.meaning_class
    ordered = sorted({left.meaning_class, right.meaning_class})
    return f"conv:{'+'.join(ordered)}"


def _lineage_id_from_events(*parts: Lineage) -> str:
    payload = "|".join(
        sorted(
            event_id
            for part in parts
            for event_id in sorted(continuity_trace(part))
        )
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"L-conv-{digest}"


def converge_pair(
    left: Lineage,
    right: Lineage,
    *,
    epsilon: float = DEFAULT_CONVERGENCE_EPSILON,
) -> tuple[Lineage, ConvergenceProof]:
    """Binary convergence product L1 ⊗ L2 = C(L1, L2)."""

    merged_events = trace_join(continuity_trace(left), continuity_trace(right))
    merged_generativity = max(generativity(left), generativity(right))
    merged = Lineage(
        lineage_id=_lineage_id_from_events(left, right),
        event_ids=merged_events,
        meaning_class=_merged_meaning_class(left, right),
        generativity=merged_generativity,
        metadata={
            "converged_from": [left.lineage_id, right.lineage_id],
            "operator": "convergence_algebra.converge_pair",
        },
    )

    if not convergence_respects_lattice(left, right, merged):
        raise ConvergenceError("convergence violated continuity lattice join")

    dist_left = proximity_to_convergence(left, merged)
    dist_right = proximity_to_convergence(right, merged)
    if dist_left > epsilon or dist_right > epsilon:
        raise ConvergenceError(
            f"semantic proximity failed: d_conv(left)={dist_left:.3f}, "
            f"d_conv(right)={dist_right:.3f}, epsilon={epsilon}"
        )

    proof = ConvergenceProof(
        left_id=left.lineage_id,
        right_id=right.lineage_id,
        result_id=merged.lineage_id,
        epsilon=epsilon,
        distance_left=dist_left,
        distance_right=dist_right,
        idempotent=left.lineage_id == right.lineage_id,
        commutative=True,
    )
    return merged, proof


def converge_many(
    lineages: list[Lineage],
    *,
    epsilon: float = DEFAULT_CONVERGENCE_EPSILON,
) -> tuple[Lineage, list[ConvergenceProof]]:
    """Associative n-ary convergence C(L1, ..., Ln)."""

    if not lineages:
        raise ConvergenceError("at least one lineage required")
    if len(lineages) == 1:
        only = lineages[0]
        _, proof = converge_pair(only, only, epsilon=epsilon)
        return only, [proof]

    current = lineages[0]
    proofs: list[ConvergenceProof] = []
    for nxt in lineages[1:]:
        current, proof = converge_pair(current, nxt, epsilon=epsilon)
        proofs.append(proof)
    return current, proofs


def verify_magma_laws(
    left: Lineage,
    middle: Lineage,
    right: Lineage,
    *,
    epsilon: float = DEFAULT_CONVERGENCE_EPSILON,
) -> dict[str, bool]:
    """Check idempotence, commutativity, and associativity on sample triple."""

    idem, _ = converge_pair(left, left, epsilon=epsilon)
    ab, _ = converge_pair(left, middle, epsilon=epsilon)
    ba, _ = converge_pair(middle, left, epsilon=epsilon)
    ab_c, _ = converge_pair(ab, right, epsilon=epsilon)
    a_bc, _ = converge_pair(left, converge_pair(middle, right, epsilon=epsilon)[0], epsilon=epsilon)

    return {
        "idempotent": (
            continuity_trace(idem) == continuity_trace(left)
            and generativity(idem) == generativity(left)
        ),
        "commutative": (
            continuity_trace(ab) == continuity_trace(ba)
            and generativity(ab) == generativity(ba)
        ),
        "associative": (
            continuity_trace(ab_c) == continuity_trace(a_bc)
            and generativity(ab_c) == generativity(a_bc)
        ),
    }


DEFAULT_PHI_MIN = 0.65
DEFAULT_DELTA_MAX = 0.05


def convergence_fitness(
    lineages: list[Lineage],
    *,
    epsilon: float = DEFAULT_CONVERGENCE_EPSILON,
    phi_min: float = DEFAULT_PHI_MIN,
) -> dict[str, object]:
    """C9 — Φ({L1,...,Ln}) = 1 - (1/n) Σ d_conv(Li, C(...))."""

    if not lineages:
        return {
            "capability_id": "C9-convergence-fitness",
            "phi": 1.0,
            "phi_min": phi_min,
            "passed": True,
            "lineage_count": 0,
            "distances": [],
        }

    if len(lineages) == 1:
        return {
            "capability_id": "C9-convergence-fitness",
            "phi": 1.0,
            "phi_min": phi_min,
            "passed": True,
            "lineage_count": 1,
            "distances": [0.0],
            "merged_lineage_id": lineages[0].lineage_id,
        }

    merged, _proofs = converge_many(lineages, epsilon=epsilon)
    distances = [proximity_to_convergence(item, merged) for item in lineages]
    phi = 1.0 - (sum(distances) / len(distances))
    return {
        "capability_id": "C9-convergence-fitness",
        "phi": round(phi, 6),
        "phi_min": phi_min,
        "passed": phi >= phi_min,
        "lineage_count": len(lineages),
        "distances": [round(item, 6) for item in distances],
        "merged_lineage_id": merged.lineage_id,
        "merged_event_count": len(merged.event_ids),
    }


def fitness_within_tolerance(
    history: list[float],
    new_phi: float,
    *,
    delta_max: float = DEFAULT_DELTA_MAX,
) -> bool:
    """C9-3: Φ(t2) ≮ Φ(t1) - Δ_max."""

    if not history:
        return True
    return new_phi + 1e-9 >= history[-1] - delta_max


def fitness_not_monotonically_decaying(history: list[float], new_phi: float) -> bool:
    """Strict monotonic non-decrease (Δ_max = 0)."""

    return fitness_within_tolerance(history, new_phi, delta_max=0.0)
