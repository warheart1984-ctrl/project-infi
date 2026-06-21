"""Epoch engine — advances substrate epoch and evaluates sovereign laws."""

from __future__ import annotations

from typing import Any

from src.continuity.comprehension_ledger import (
    ComprehensionLedgerStore,
    bootstrap_comprehension_ledger,
    evaluate_law_comprehension,
)
from src.continuity.evidence_fitness import evaluate_evidence_fitness
from src.continuity.evidence_ledger import (
    EvidenceLedgerStore,
    bootstrap_evidence_ledger,
    evaluate_law_with_evidence,
    evidence_id_for,
)
from src.continuity.law_ledger import (
    LawLedgerStore,
    bootstrap_law_ledger,
)
from src.continuity.mit_ledger import MitLedgerStore, bootstrap_mit_ledger, evaluate_law_meaning


def run_epoch_cycle(*, signer: str = "operator") -> dict[str, Any]:
    """Advance one epoch: evaluate every law record against active LCI lineages."""

    law_store = LawLedgerStore()
    evidence_store = EvidenceLedgerStore()
    comprehension_store = ComprehensionLedgerStore()
    meaning_store = MitLedgerStore()
    bootstrap_law_ledger(law_store)
    bootstrap_evidence_ledger(evidence_store)
    bootstrap_comprehension_ledger(comprehension_store)
    bootstrap_mit_ledger(meaning_store)

    next_epoch = law_store.get_current_epoch() + 1
    lineages = law_store.get_lineages_for_law("PIT-1")
    evaluated: list[dict[str, Any]] = []

    for record in law_store.all_laws():
        updated = evaluate_law_with_evidence(
            record,
            next_epoch,
            lineages,
            signer=signer,
            law_store=law_store,
            evidence_store=evidence_store,
        )
        evidence_id = evidence_id_for(updated.law_id, next_epoch)
        law_dict = updated.to_dict()
        law_dict["_epoch"] = next_epoch

        cit = evaluate_law_comprehension(
            law_dict,
            epoch=next_epoch,
            evidence_id=evidence_id,
            store=comprehension_store,
        )
        mit = evaluate_law_meaning(law_dict, epoch=next_epoch, store=meaning_store)
        stored_evidence = evidence_store.get_evidence(evidence_id)
        eit = None
        if stored_evidence is not None:
            graph = evidence_store.get_lineage_graph(evidence_id)
            eit = evaluate_evidence_fitness(stored_evidence, graph=graph)

        evaluated.append(
            {
                "law_id": updated.law_id,
                "status": updated.status.value,
                "fitness": round(updated.current_fitness, 6),
                "evidence_id": evidence_id,
                "chi": cit["cit_strip"]["chi"],
                "mu": mit["mu"],
                "omega": eit["omega"] if eit else None,
            }
        )

    return {
        "status": "ok",
        "epoch": next_epoch,
        "evaluated": evaluated,
        "lineage_count": len(lineages),
    }
