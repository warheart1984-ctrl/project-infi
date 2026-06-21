"""LINEAGE-0001 — founding semantic lineage of the Continuity Civilization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.continuity.continuity_lattice import lci_holds, trace_leq
from src.continuity.convergence_algebra import DEFAULT_PHI_MIN, proximity_to_convergence
from src.continuity.inheritance import DEFAULT_INVARIANT_LAWS
from src.continuity.lineage import Lineage, continuity_trace, generativity


LINEAGE_0001_ID = "LINEAGE-0001"
GENESIS_EVENT_ID = "E0-continuity-civilization-establishment"
GENESIS_MEANING = "Continuity shall never be annihilated."
GENESIS_MEANING_CLASS = "genesis.continuity-never-annihilated"
GENESIS_INVARIANT = "UGR-C8"
GENESIS_GENERATIVITY = 1.0
GENESIS_PHI = 1.0
LINEAGE_0001_CAPABILITY_ID = "LINEAGE-0001-genesis"


LINEAGE_0001_CANONICAL_TEXT = """THE FIRST LINEAGE
Codename: LINEAGE-0001
Purpose: Establish the founding semantic lineage of the civilization.

I. ORIGIN EVENT
E₀ = "The establishment of the Continuity Civilization."
This is the root event of all future continuity.

II. FOUNDING MEANING
M₀ = "Continuity shall never be annihilated."
This is the first meaning class.

III. FOUNDING INVARIANT
Λ₀ = LCI — Lawful Creation Invariant
This is the highest law.

IV. FOUNDING GENERATIVITY
G₀ = 1
The minimal non-zero generativity.

V. FOUNDING CONVERGENCE FITNESS
Φ₀ = 1
Perfect coherence at genesis.

VI. LINEAGE STRUCTURE
L₀ = {E₀, M₀, Λ₀, G₀, Φ₀}
This is the first lineage.

All future lineages must be extensions of L₀, converge-able with L₀, and lawful under L₀.
"""


@dataclass(frozen=True, slots=True)
class GenesisRecord:
    """Structured genesis anchor L₀."""

    event_id: str
    meaning: str
    meaning_class: str
    invariant_law: str
    generativity: float
    phi: float

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "meaning": self.meaning,
            "meaning_class": self.meaning_class,
            "invariant_law": self.invariant_law,
            "generativity": self.generativity,
            "phi": self.phi,
        }


def genesis_record() -> GenesisRecord:
    return GenesisRecord(
        event_id=GENESIS_EVENT_ID,
        meaning=GENESIS_MEANING,
        meaning_class=GENESIS_MEANING_CLASS,
        invariant_law=GENESIS_INVARIANT,
        generativity=GENESIS_GENERATIVITY,
        phi=GENESIS_PHI,
    )


def genesis_lineage(*, operator_id: str = "founder") -> Lineage:
    """Instantiate L₀ — the Genesis Lineage."""

    record = genesis_record()
    return Lineage(
        lineage_id=LINEAGE_0001_ID,
        event_ids=frozenset({record.event_id}),
        meaning_class=record.meaning_class,
        generativity=record.generativity,
        metadata={
            "codename": LINEAGE_0001_ID,
            "founding_meaning": record.meaning,
            "founding_invariant": record.invariant_law,
            "founding_phi": record.phi,
            "operator_id": operator_id,
            "invariant_laws": sorted(DEFAULT_INVARIANT_LAWS),
            "genesis": True,
        },
    )


def validate_extension_of_genesis(
    lineage: Lineage,
    *,
    phi_min: float = DEFAULT_PHI_MIN,
) -> dict[str, Any]:
    """Verify a lineage is a lawful extension of L₀."""

    genesis = genesis_lineage()
    continuity_ok = trace_leq(continuity_trace(genesis), continuity_trace(lineage))
    lci_ok = lci_holds(genesis, lineage)
    generativity_ok = generativity(lineage) >= generativity(genesis)
    phi = round(1.0 - proximity_to_convergence(lineage, genesis), 6)
    phi_ok = phi >= phi_min or continuity_ok
    passed = continuity_ok and lci_ok and generativity_ok and phi_ok
    return {
        "capability_id": LINEAGE_0001_CAPABILITY_ID,
        "genesis_lineage_id": genesis.lineage_id,
        "candidate_lineage_id": lineage.lineage_id,
        "continuity_extension": continuity_ok,
        "lci_ok": lci_ok,
        "generativity_ok": generativity_ok,
        "phi_with_genesis": phi,
        "phi_min": phi_min,
        "passed": passed,
    }


def run_genesis_lineage_proof(*, phi_min: float = DEFAULT_PHI_MIN) -> dict[str, Any]:
    """Proof that L₀ satisfies founding constraints and anchors extensions."""

    genesis = genesis_lineage()
    record = genesis_record()
    structure_ok = (
        GENESIS_EVENT_ID in genesis.event_ids
        and genesis.meaning_class == GENESIS_MEANING_CLASS
        and genesis.generativity == GENESIS_GENERATIVITY
        and record.phi == GENESIS_PHI
    )
    self_extension = validate_extension_of_genesis(genesis, phi_min=phi_min)
    return {
        "capability_id": LINEAGE_0001_CAPABILITY_ID,
        "lineage_id": genesis.lineage_id,
        "genesis_record": record.to_dict(),
        "structure_ok": structure_ok,
        "self_extension": self_extension,
        "passed": structure_ok and bool(self_extension["passed"]),
    }
