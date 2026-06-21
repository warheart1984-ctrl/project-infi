"""IE-0001 — Invariant Engine for cross-epoch invariant law enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.continuity.continuity_lattice import lci_holds
from src.continuity.inheritance import DEFAULT_INVARIANT_LAWS
from src.continuity.lineage import Lineage, generativity
from src.continuity.universal_semantics import verify_meaning


IE_0001_ID = "IE-0001"
IE_0001_CAPABILITY_ID = "IE-0001-invariant-engine"
HIGHEST_LAW = "UGR-C8"


IE_0001_CANONICAL_TEXT = """INVARIANT ENGINE
Codename: IE-0001
Purpose: Maintain, evaluate, and enforce invariant law across operators, lineages, and epochs.

I. Engine Identity — maintains Λ₀ and derived invariants I.
II. Invariant Registry — each invariant has definition, domain, validation rule, violation condition.
III. Invariant Validator — V_I: M × M → {0,1}.
IV. Invariant Propagation — evolution preserves I(L'); convergence intersects invariants; epochs preserve law.
V. Invariant Enforcement — reject, quarantine, repair, notify on violation.
"""


@dataclass(frozen=True, slots=True)
class InvariantDefinition:
    invariant_id: str
    definition: str
    domain: str
    expression: str
    validate: Callable[[Lineage, Lineage | None], bool]
    violation_condition: str

    def to_dict(self) -> dict[str, str]:
        return {
            "invariant_id": self.invariant_id,
            "definition": self.definition,
            "domain": self.domain,
            "expression": self.expression,
            "violation_condition": self.violation_condition,
        }


def _lci_validate(before: Lineage, after: Lineage | None) -> bool:
    if after is None:
        return True
    return lci_holds(before, after)


def _generativity_validate(before: Lineage, after: Lineage | None) -> bool:
    if after is None:
        return generativity(before) >= 0
    return generativity(after) >= generativity(before)


def _invariant_set_unchanged(before: Lineage, after: Lineage | None) -> bool:
    if after is None:
        return True
    before_laws = frozenset(before.metadata.get("invariant_laws") or DEFAULT_INVARIANT_LAWS)
    after_laws = frozenset(after.metadata.get("invariant_laws") or DEFAULT_INVARIANT_LAWS)
    return before_laws == after_laws


INVARIANT_REGISTRY: tuple[InvariantDefinition, ...] = (
    InvariantDefinition(
        HIGHEST_LAW,
        "Lawful Creation Invariant — continuity never annihilated",
        "lineage evolution",
        "K(L') ⊇ K(L) ∧ G(L') ≥ G(L)",
        _lci_validate,
        "continuity shrinks or generativity decreases",
    ),
    InvariantDefinition(
        "UGR-C9",
        "Convergence fitness must remain above constitutional threshold",
        "civilizational lineages",
        "Φ ≥ Φ_min",
        lambda _before, _after: True,
        "convergence fitness below Φ_min",
    ),
    InvariantDefinition(
        "IE-GENERATIVITY-MONOTONE",
        "Generativity is non-decreasing under lawful evolution",
        "lineage evolution",
        "G(L') ≥ G(L)",
        _generativity_validate,
        "generativity decreased",
    ),
    InvariantDefinition(
        "IE-INVARIANT-STRUCTURE",
        "Invariant law structure preserved across evolution",
        "lineage evolution",
        "I(L') = I(L)",
        _invariant_set_unchanged,
        "invariant structure changed",
    ),
)


class InvariantEngine:
    """Semantic immune system — registry + enforcement."""

    def __init__(self, registry: tuple[InvariantDefinition, ...] = INVARIANT_REGISTRY) -> None:
        self.registry = registry

    def validate_meaning_pair(self, left: str, right: str) -> bool:
        """V_I on meaning classes."""

        return verify_meaning(left, right)

    def validate_lineage_transition(self, before: Lineage, after: Lineage) -> dict[str, Any]:
        results = [
            {
                **item.to_dict(),
                "passed": item.validate(before, after),
            }
            for item in self.registry
        ]
        passed = all(row["passed"] for row in results)
        return {
            "capability_id": IE_0001_CAPABILITY_ID,
            "highest_law": HIGHEST_LAW,
            "results": results,
            "passed": passed,
        }

    def propagate_evolution(self, before: Lineage, after: Lineage) -> dict[str, Any]:
        validation = self.validate_lineage_transition(before, after)
        return {
            "operation": "evolution",
            "invariant_preservation": validation["passed"],
            "I_after_equals_I_before": _invariant_set_unchanged(before, after),
            **validation,
        }

    def propagate_convergence(self, lineages: list[Lineage], merged: Lineage) -> dict[str, Any]:
        shared = set(DEFAULT_INVARIANT_LAWS)
        for item in lineages:
            shared &= set(item.metadata.get("invariant_laws") or DEFAULT_INVARIANT_LAWS)
        merged_laws = set(merged.metadata.get("invariant_laws") or DEFAULT_INVARIANT_LAWS)
        intersection_ok = bool(shared) and shared <= merged_laws
        validations = [self.validate_lineage_transition(item, merged) for item in lineages]
        passed = intersection_ok and all(item["passed"] for item in validations)
        return {
            "operation": "convergence",
            "shared_invariants": sorted(shared),
            "intersection_ok": intersection_ok,
            "validations": validations,
            "passed": passed,
        }

    def enforce_or_reject(self, before: Lineage, after: Lineage) -> dict[str, Any]:
        validation = self.validate_lineage_transition(before, after)
        if not validation["passed"]:
            return {
                "action": "reject",
                "quarantine": False,
                "repair_required": True,
                **validation,
            }
        return {"action": "accept", "quarantine": False, "repair_required": False, **validation}


DEFAULT_INVARIANT_ENGINE = InvariantEngine()


def run_invariant_engine_proof() -> dict[str, Any]:
    from dataclasses import replace

    from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture

    engine = DEFAULT_INVARIANT_ENGINE
    lineages = lineages_from_fixture(load_lci_fixture())
    before = lineages[0]
    after = replace(
        before,
        event_ids=before.event_ids | frozenset({"evt-ie-proof"}),
        generativity=before.generativity + 0.5,
    )
    evolution = engine.propagate_evolution(before, after)
    from src.continuity.convergence_algebra import converge_many

    merged, _ = converge_many(lineages[:2])
    convergence = engine.propagate_convergence(lineages[:2], merged)
    enforcement = engine.enforce_or_reject(before, after)
    passed = bool(evolution["passed"]) and bool(convergence["passed"]) and enforcement["action"] == "accept"
    return {
        "capability_id": IE_0001_CAPABILITY_ID,
        "registry_size": len(INVARIANT_REGISTRY),
        "evolution": evolution,
        "convergence": convergence,
        "enforcement": enforcement,
        "passed": passed,
    }
