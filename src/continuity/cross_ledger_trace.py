"""Cross-ledger trace and minimal replay for constitutional spine (Law ↔ Evidence ↔ CIT ↔ MIT)."""

from __future__ import annotations

from typing import Any

from src.continuity.evidence_fitness import (
    EvidenceFitnessConfig,
    build_evidence_eit_strip,
    evaluate_evidence_fitness,
)
from src.continuity.evidence_ledger import (
    EvidenceLedgerStore,
    build_evidence_from_lineages,
    evidence_id_for,
    operator_replay_equivalent,
)
from src.continuity.law_ledger import LawLedgerStore, LawLedgerEntryType


def build_cross_ledger_trace(
    law_id: str,
    *,
    law_store: LawLedgerStore | None = None,
    evidence_store: EvidenceLedgerStore | None = None,
    comprehension_store: Any | None = None,
    mit_store: Any | None = None,
    epoch: int | None = None,
) -> dict[str, Any]:
    from src.continuity.comprehension_ledger import ComprehensionLedgerStore
    from src.continuity.mit_ledger import MitLedgerStore

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    comprehension = comprehension_store or ComprehensionLedgerStore()
    meaning = mit_store or MitLedgerStore()

    record = laws.get_law_record(law_id)
    if record is None:
        return {"law_id": law_id, "found": False, "nodes": [], "edges": []}

    resolved_epoch = epoch if epoch is not None else laws.get_current_epoch()
    evidence_id = evidence_id_for(law_id, resolved_epoch)
    ev = evidence.get_evidence(evidence_id)
    if ev is None:
        for entry in reversed(laws.ledger_entries()):
            if entry.law_id != law_id:
                continue
            bound = (entry.payload or {}).get("evidence_id")
            if bound:
                ev = evidence.get_evidence(str(bound))
                if ev is not None:
                    evidence_id = ev.evidence_id
                    resolved_epoch = ev.source_epoch
                    break
    graph = evidence.get_lineage_graph(evidence_id) if ev else {"nodes": [], "edges": [], "found": False}

    chi_record = comprehension.get_latest_record("law", law_id)
    mu_record = meaning.get_latest_record("law", law_id)

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def add_node(node_id: str, *, layer: str, label: str, **extra: Any) -> None:
        if node_id in nodes:
            existing = nodes[node_id]
            if layer == "evidence" and existing.get("layer") in {"evidence_ref", "lineage"}:
                existing["layer"] = layer
                existing.update(extra)
            return
        nodes[node_id] = {"id": node_id, "layer": layer, "label": label, **extra}

    add_node(
        law_id,
        layer="law",
        label=law_id,
        status=record.status.value,
        fitness=round(record.current_fitness, 6),
        epoch=resolved_epoch,
    )

    law_entries = [
        item
        for item in laws.ledger_entries()
        if item.law_id == law_id
        and item.entry_type in {LawLedgerEntryType.LAW_EVAL, LawLedgerEntryType.LAW_STATUS_CHANGE}
    ][-6:]

    for entry in law_entries:
        add_node(entry.entry_id, layer="law_ledger", label=entry.entry_type.value, epoch=entry.epoch)
        edges.append({"from": law_id, "to": entry.entry_id, "kind": "law_ledger"})
        bound_evidence = (entry.payload or {}).get("evidence_id")
        if bound_evidence:
            add_node(bound_evidence, layer="evidence_ref", label=bound_evidence)
            edges.append({"from": entry.entry_id, "to": bound_evidence, "kind": "evidence_bound"})

    if ev:
        add_node(
            ev.evidence_id,
            layer="evidence",
            label=ev.evidence_id,
            confidence=round(ev.confidence, 6),
            evidence_type=ev.evidence_type.value,
        )
        edges.append({"from": law_id, "to": ev.evidence_id, "kind": "evaluated_with"})
        eit = evaluate_evidence_fitness(ev, graph=graph)
        add_node(
            f"OMEGA-{ev.evidence_id}",
            layer="eit",
            label=f"Ω={eit['omega']:.3f}",
            omega=eit["omega"],
            status=eit["status"],
        )
        edges.append({"from": ev.evidence_id, "to": f"OMEGA-{ev.evidence_id}", "kind": "fitness"})

        for node in graph.get("nodes") or []:
            add_node(node["id"], layer="lineage", label=node.get("label", node["id"]))
        for edge in graph.get("edges") or []:
            edges.append(
                {
                    "from": edge["from"],
                    "to": edge["to"],
                    "kind": edge.get("kind", "lineage"),
                }
            )

    if chi_record:
        chi_id = chi_record.id if hasattr(chi_record, "id") else f"CHI-law-{law_id}"
        add_node(
            chi_id,
            layer="cit",
            label=f"Χ={chi_record.chi:.3f}",
            chi=round(chi_record.chi, 6),
        )
        edges.append({"from": law_id, "to": chi_id, "kind": "comprehension"})

    if mu_record:
        add_node(
            mu_record.id,
            layer="mit",
            label=f"Μ={mu_record.mu:.3f}",
            mu=round(mu_record.mu, 6),
        )
        edges.append({"from": law_id, "to": mu_record.id, "kind": "meaning"})

    strip = build_evidence_eit_strip(ev, graph=graph) if ev else None

    return {
        "law_id": law_id,
        "epoch": resolved_epoch,
        "found": True,
        "evidence_id": ev.evidence_id if ev else None,
        "nodes": list(nodes.values()),
        "edges": edges,
        "eit_strip": strip.to_dict() if strip else None,
        "chi": chi_record.chi if chi_record else None,
        "mu": mu_record.mu if mu_record else None,
        "law_ledger_tail": [entry.to_dict() for entry in law_entries],
    }


def replay_law_evidence(
    law_id: str,
    *,
    epoch: int | None = None,
    signer: str = "operator",
    law_store: LawLedgerStore | None = None,
    evidence_store: EvidenceLedgerStore | None = None,
) -> dict[str, Any]:
    """Minimal EIT-2 replay — rebuild evidence and verify operator convergence."""

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    record = laws.get_law_record(law_id)
    if record is None:
        return {"law_id": law_id, "found": False, "passed": False, "reason": "law not found"}

    resolved_epoch = epoch if epoch is not None else laws.get_current_epoch()
    stored = evidence.get_evidence(evidence_id_for(law_id, resolved_epoch))
    if stored is None:
        return {
            "law_id": law_id,
            "epoch": resolved_epoch,
            "found": True,
            "passed": False,
            "reason": f"no evidence at epoch {resolved_epoch}",
        }

    lineages = laws.get_lineages_for_law(law_id)
    replayed = build_evidence_from_lineages(record, resolved_epoch, lineages, signer=signer)
    operator_ok = operator_replay_equivalent(stored, replayed)
    graph = evidence.get_lineage_graph(stored.evidence_id)
    fitness = evaluate_evidence_fitness(
        stored,
        graph=graph,
        replayed=replayed,
        cfg=EvidenceFitnessConfig(),
    )

    return {
        "law_id": law_id,
        "epoch": resolved_epoch,
        "evidence_id": stored.evidence_id,
        "found": True,
        "passed": operator_ok and fitness["status"] != "breach",
        "operator_convergent": operator_ok,
        "stored_hash": stored.canonical_hash,
        "replayed_hash": replayed.canonical_hash,
        "omega": fitness["omega"],
        "convergence": fitness["convergence"],
        "status": fitness["status"],
        "warnings": fitness["warnings"],
    }
