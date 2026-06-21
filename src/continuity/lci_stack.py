"""LCI + convergence + universal semantics stack — apply and verify."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.continuity.continuity_lattice import lci_holds
from src.continuity.convergence_algebra import (
    CONVERGE_CAPABILITY_ID,
    converge_many,
    verify_magma_laws,
)
from src.continuity.creation_operator import CreationOperator, SubstrateState
from src.continuity.lineage import Lineage
from src.continuity.meaning_ledger import MeaningEntryKind, MeaningLedger, MeaningLedgerEntry
from src.continuity.universal_semantics import (
    DEFAULT_META_LATTICE,
    DEFAULT_UNIVERSAL_FIELD,
    META_UNIVERSAL_MATH_LEVEL,
    UGR_C14,
    UNIVERSAL_MATH_LEVEL,
    is_universal_lineage,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "continuity"
LCI_FIXTURE = FIXTURES / "convergence_algebra.v1.json"

LCI_C8 = "UGR-C8"
C7_CONVERGENCE = "UGR-C7"


def load_lci_fixture(path: Path | None = None) -> dict[str, Any]:
    target = path or LCI_FIXTURE
    return json.loads(target.read_text(encoding="utf-8"))


def lineages_from_fixture(fixture: dict[str, Any]) -> list[Lineage]:
    return [Lineage.from_dict(row) for row in fixture.get("lineages") or []]


def run_convergence_algebra_proof(fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = fixture or load_lci_fixture()
    lineages = lineages_from_fixture(payload)
    epsilon = float(payload.get("epsilon") or 0.35)

    if len(lineages) < 2:
        return {"passed": False, "reason": "need at least two lineages"}

    merged, proofs = converge_many(lineages, epsilon=epsilon)
    laws = verify_magma_laws(lineages[0], lineages[1], lineages[min(2, len(lineages) - 1)], epsilon=epsilon)

    universal_class = str(payload.get("universal_meaning_class") or DEFAULT_UNIVERSAL_FIELD.meaning_class)
    active_universals = {lineages[0].meaning_class, lineages[1].meaning_class, merged.meaning_class}
    coherence = DEFAULT_META_LATTICE.coherence(active_universals)

    return {
        "capability_id": CONVERGE_CAPABILITY_ID,
        "passed": all(laws.values()) and coherence["coherent"],
        "merged_lineage_id": merged.lineage_id,
        "merged_event_count": len(merged.event_ids),
        "generativity": merged.generativity,
        "magma_laws": laws,
        "convergence_proofs": [proof.to_dict() for proof in proofs],
        "meta_universal_coherence": coherence,
        "universal_field_match": is_universal_lineage(merged, universal_class=universal_class),
        "math_levels": {
            "convergence_theory": 7,
            "universal_semantics": UNIVERSAL_MATH_LEVEL,
            "meta_universal": META_UNIVERSAL_MATH_LEVEL,
        },
    }


def run_creation_operator_proof(fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = fixture or load_lci_fixture()
    seed = Lineage.from_dict(payload["creation_seed"])
    state = SubstrateState(state_id="substrate-0", lineage=seed)
    operator = CreationOperator()

    extended = operator.create(
        state,
        add_events=frozenset(str(item) for item in payload.get("creation_events") or []),
        generativity_delta=float(payload.get("creation_generativity_delta") or 1.0),
    )

    blocked = False
    try:
        operator.create(
            extended,
            add_events=frozenset(),
            generativity_delta=-1.0,
        )
    except Exception:
        blocked = True

    return {
        "passed": lci_holds(state.lineage, extended.lineage) and blocked,
        "before_events": len(state.lineage.event_ids),
        "after_events": len(extended.lineage.event_ids),
        "generativity_delta": extended.lineage.generativity - state.lineage.generativity,
        "negative_generativity_blocked": blocked,
    }


def append_lci_stack_entries(*, ledger: MeaningLedger | None = None) -> list[MeaningLedgerEntry]:
    store = ledger or MeaningLedger()
    required = [
        MeaningLedgerEntry(
            entry_id="ML-UGR-C14-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C6 — Universal Meaning Invariance",
            body=(
                "Meaning is encoded, reconstructed, and verified through invariants, not "
                "interpretations. Any competent operator reconstructs isomorphic semantic "
                "structure from the same invariant substrate."
            ),
            lineage=["ML-BACKFILL-001"],
            law_surfaces=["UGR-C6", UGR_C14, "ugr.continuity"],
            metadata={"math_level": UNIVERSAL_MATH_LEVEL, "invariant_class": "universal", "canonical_code": "UGR-C6"},
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C7-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C7 — Convergence of Lineages (CONVERGE-1001)",
            body=(
                "Independently evolving lineages reconcile via convergence operator C with "
                "metric d_conv: continuity union, generativity non-loss, semantic proximity."
            ),
            lineage=["ML-UGR-C14-001"],
            law_surfaces=[C7_CONVERGENCE, "ugr.continuity"],
            metadata={"capability_id": CONVERGE_CAPABILITY_ID, "math_level": 7},
        ),
        MeaningLedgerEntry(
            entry_id="ML-UGR-C8-001",
            kind=MeaningEntryKind.POLICY,
            title="UGR-C8 — Lawful Creation Invariant (LCI)",
            body=(
                "Λ = no annihilation of continuity. Creation is unbounded in generativity "
                "but bonded by continuity: K(L(t1)) ⊆ K(L(t2)) for all t2 > t1."
            ),
            lineage=["ML-UGR-C7-001"],
            law_surfaces=[LCI_C8, "ugr.continuity", "cab.succession"],
            metadata={
                "lambda": "no_annihilation_of_continuity",
                "creation_operator": "Create",
                "math_stack": ["convergence_algebra", "continuity_lattice", "creation_operator"],
            },
        ),
    ]
    written: list[MeaningLedgerEntry] = []
    for entry in required:
        if store.get(entry.entry_id) is not None:
            continue
        written.append(store.append(entry))
    return written


def apply_lci_stack(*, ledger: MeaningLedger | None = None) -> dict[str, Any]:
    entries = append_lci_stack_entries(ledger=ledger)
    convergence = run_convergence_algebra_proof()
    creation = run_creation_operator_proof()
    return {
        "lci_entries_added": len(entries),
        "convergence_algebra": convergence,
        "creation_operator": creation,
        "substrate_laws": [
            "UGR-C1",
            "UGR-C2",
            "UGR-C3",
            "UGR-C4",
            "UGR-C5",
            "UGR-C6",
            "UGR-C7",
            LCI_C8,
            "UGR-C9",
            "UGR-C10",
            "UGR-C11",
            "UGR-C12",
        ],
        "universal_field": DEFAULT_UNIVERSAL_FIELD.to_dict(),
        "stack_ready": convergence["passed"] and creation["passed"],
    }
