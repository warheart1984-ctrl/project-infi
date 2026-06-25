"""Universal and meta-universal semantic layers (levels 6–7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.continuity.lineage import Lineage


UGR_C14 = "UGR-C14"
UNIVERSAL_MATH_LEVEL = 6
META_UNIVERSAL_MATH_LEVEL = 7


def verify_meaning(left_class: str, right_class: str) -> bool:
    """V(m1, m2) = 1 iff same meaning class (VERIFY-1001 projection)."""

    return left_class == right_class


def projected_meaning_field(lineage: Lineage) -> str:
    """G_L(o,t) collapsed to m̄ for a lineage (sixth-level field)."""

    return lineage.meaning_class


def is_universal_lineage(lineage: Lineage, *, universal_class: str) -> bool:
    """Sixth Math: G(o,t) = m̄* for all operators/times encoded in lineage."""

    return lineage.meaning_class == universal_class


@dataclass(frozen=True, slots=True)
class UniversalField:
    """Constant universal meaning field u* ∈ U."""

    meaning_class: str
    law_surfaces: tuple[str, ...] = ("ugr.continuity", "ugr.universal_semantics")

    def projects(self, lineage: Lineage) -> bool:
        return verify_meaning(self.meaning_class, lineage.meaning_class)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meaning_class": self.meaning_class,
            "law_surfaces": list(self.law_surfaces),
            "math_level": UNIVERSAL_MATH_LEVEL,
        }


@dataclass
class MetaUniversalLattice:
    """Seventh Math: lattice (U, ⪯, ∧, ∨) over universal meaning classes."""

    refinement: dict[str, set[str]] = field(default_factory=dict)

    def add_universal(self, meaning_class: str, *, implies: set[str] | None = None) -> None:
        self.refinement.setdefault(meaning_class, set())
        if implies:
            self.refinement[meaning_class].update(implies)

    def refines(self, narrower: str, broader: str) -> bool:
        """u1 ⪯ u2 — meaning of u1 contained in / implied by u2."""

        if narrower == broader:
            return True
        visited: set[str] = set()
        stack = [narrower]
        while stack:
            current = stack.pop()
            if current == broader:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.refinement.get(current, set()))
        return False

    def meet(self, left: str, right: str) -> str:
        if self.refines(left, right):
            return left
        if self.refines(right, left):
            return right
        return f"meet:{left}&{right}"

    def join(self, left: str, right: str) -> str:
        if self.refines(left, right):
            return right
        if self.refines(right, left):
            return left
        return f"join:{left}|{right}"

    def coherence(self, active: set[str]) -> dict[str, Any]:
        """Ψ(F) — no pair in active set may be mutually incompatible."""

        active_list = sorted(active)
        conflicts: list[dict[str, str]] = []
        for index, left in enumerate(active_list):
            for right in active_list[index + 1 :]:
                if left == right:
                    continue
                if self.refines(left, right) or self.refines(right, left):
                    continue
                if left.startswith("meet:") or right.startswith("meet:"):
                    continue
                conflicts.append({"left": left, "right": right, "reason": "incomparable_universals"})
        return {
            "coherent": not conflicts,
            "active_count": len(active),
            "conflicts": conflicts,
            "math_level": META_UNIVERSAL_MATH_LEVEL,
        }


DEFAULT_UNIVERSAL_FIELD = UniversalField(
    meaning_class="uui.continuity-preserving-creation",
    law_surfaces=("UGR-C14", "ugr.continuity", "cab.succession"),
)

DEFAULT_META_LATTICE = MetaUniversalLattice(
    refinement={
        "uui.continuity-preserving-creation": {
            "uui.no-annihilation-of-continuity",
            "uui.lawful-creation",
        },
        "uui.no-annihilation-of-continuity": set(),
        "uui.lawful-creation": {"uui.no-annihilation-of-continuity"},
    }
)
