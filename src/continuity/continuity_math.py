"""CM-0001 — formal mathematical foundation for continuity substrate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.continuity.continuity_lattice import lci_holds, trace_leq
from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, d_conv
from src.continuity.lineage import Lineage, continuity_trace, generativity
from src.continuity.temporal_governance import TemporalState, evaluate_temporal_coherence
from src.continuity.universal_semantics import verify_meaning


CM_0001_ID = "CM-0001"
CM_0001_CAPABILITY_ID = "CM-0001-continuity-math"
DEFAULT_TEMPORAL_EPSILON = 0.35


CM_0001_CANONICAL_TEXT = """CONTINUITY MATH
Codename: CM-0001
Purpose: Formal mathematical foundation for continuity, lineage, convergence, and temporal coherence.

I. Continuity Space — K: O × T → P(E) with K(o,t2) ⊇ K(o,t1).
II. Lineage Space — L = (K_L, M_L, I_L, G_L).
III. Meaning Equivalence — m1 ~ m2 ⟺ V(m1,m2) = 1; M̄ = M/~.
IV. Convergence Metric — d_conv(L1, L2) measures semantic divergence.
V. Convergence Operator — C: L^n → L preserving continuity union and generativity.
VI. Temporal Coherence — K(t1) ⊆ K(t2) and d_conv(L(t1), L(t2)) ≤ ε_T.
"""


@dataclass(frozen=True, slots=True)
class LineageMathView:
    """L = (K_L, M_L, I_L, G_L) projection."""

    lineage_id: str
    continuity: frozenset[str]
    meaning_class: str
    invariant_laws: frozenset[str]
    generativity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "lineage_id": self.lineage_id,
            "continuity": sorted(self.continuity),
            "meaning_class": self.meaning_class,
            "invariant_laws": sorted(self.invariant_laws),
            "generativity": self.generativity,
        }


def lineage_math_view(
    lineage: Lineage,
    *,
    invariant_laws: frozenset[str] | None = None,
) -> LineageMathView:
    laws = invariant_laws or frozenset(
        str(item) for item in (lineage.metadata.get("invariant_laws") or ["UGR-C8"])
    )
    return LineageMathView(
        lineage_id=lineage.lineage_id,
        continuity=continuity_trace(lineage),
        meaning_class=lineage.meaning_class,
        invariant_laws=laws,
        generativity=generativity(lineage),
    )


def continuity_monotone(before: frozenset[str], after: frozenset[str]) -> bool:
    """CM §I — continuity is monotonic in time."""

    return trace_leq(before, after)


def meaning_equivalent(left: str, right: str) -> bool:
    """CM §III — semantic equivalence quotient."""

    return verify_meaning(left, right)


def convergence_distance(left: Lineage, right: Lineage) -> float:
    """CM §IV — d_conv(L1, L2)."""

    return d_conv(left, right)


def temporal_coherence_ok(
    past: TemporalState,
    future: TemporalState,
    *,
    epsilon_t: float = DEFAULT_TEMPORAL_EPSILON,
    phi_min_t: float = DEFAULT_PHI_MIN,
) -> dict[str, Any]:
    """CM §VI — temporal coherence predicate."""

    result = evaluate_temporal_coherence(past, future, phi_min_t=phi_min_t)
    distance = convergence_distance(past.lineage, future.lineage)
    passed = bool(result["passed"]) and distance <= epsilon_t
    return {
        "capability_id": CM_0001_CAPABILITY_ID,
        "continuity_ok": result["continuity_non_annihilation"],
        "distance": distance,
        "epsilon_t": epsilon_t,
        "phi_t1_t2": result["phi_t1_t2"],
        "passed": passed,
    }


def run_continuity_math_proof() -> dict[str, Any]:
    from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture

    lineages = lineages_from_fixture(load_lci_fixture())
    left, right = lineages[0], lineages[1]
    views = [lineage_math_view(item) for item in lineages[:2]]
    monotone = continuity_monotone(continuity_trace(left), continuity_trace(left) | {"evt-cm-proof"})
    lci_ok = lci_holds(left, replace_lineage_events(left, continuity_trace(left) | {"evt-cm-proof"}))
    temporal = temporal_coherence_ok(
        TemporalState("cm-t1", left),
        TemporalState("cm-t2", replace_lineage_events(left, continuity_trace(left) | {"evt-cm-proof"})),
    )
    return {
        "capability_id": CM_0001_CAPABILITY_ID,
        "lineage_views": [view.to_dict() for view in views],
        "continuity_monotone": monotone,
        "lci_ok": lci_ok,
        "convergence_distance": convergence_distance(left, right),
        "temporal_coherence": temporal,
        "passed": monotone and lci_ok and bool(temporal["passed"]),
    }


def replace_lineage_events(lineage: Lineage, events: frozenset[str]) -> Lineage:
    from dataclasses import replace

    return replace(lineage, event_ids=events)
