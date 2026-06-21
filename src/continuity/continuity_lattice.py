"""Continuity lattice (K, ⪯, ∧, ∨) and LCI monotonicity checks."""

from __future__ import annotations

from src.continuity.lineage import Lineage, continuity_trace, generativity


def trace_leq(left: frozenset[str], right: frozenset[str]) -> bool:
    """K1 ⪯ K2 iff K1 ⊆ K2."""

    return left <= right


def trace_meet(left: frozenset[str], right: frozenset[str]) -> frozenset[str]:
    """K1 ∧ K2 = K1 ∩ K2."""

    return left & right


def trace_join(left: frozenset[str], right: frozenset[str]) -> frozenset[str]:
    """K1 ∨ K2 = K1 ∪ K2."""

    return left | right


def lci_continuity_holds(before: Lineage, after: Lineage) -> bool:
    """Λ = no annihilation of continuity: K(L(t1)) ⊆ K(L(t2))."""

    return trace_leq(continuity_trace(before), continuity_trace(after))


def lci_generativity_holds(before: Lineage, after: Lineage) -> bool:
    """Generativity monotonicity: G(L') ≥ G(L)."""

    return generativity(after) >= generativity(before)


def lci_holds(before: Lineage, after: Lineage) -> bool:
    """Full LCI (C8) at a transition."""

    return lci_continuity_holds(before, after) and lci_generativity_holds(before, after)


def convergence_respects_lattice(left: Lineage, right: Lineage, merged: Lineage) -> bool:
    """K(L1 ⊗ L2) = K(L1) ∨ K(L2)."""

    expected = trace_join(continuity_trace(left), continuity_trace(right))
    return continuity_trace(merged) == expected
