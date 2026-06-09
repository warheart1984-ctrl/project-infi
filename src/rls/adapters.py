"""Adapters from exchange, Jarvis, and OTEM payloads to ReasoningGraph."""

from __future__ import annotations

from typing import Any

from src.rls.reasoning_graph import build_graph_from_flat_text, normalize_reasoning_graph


def from_reasoning_exchange_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Build ReasoningGraph from a normalized reasoning exchange packet."""
    payload = dict(packet.get("payload") or {})
    meta = dict(packet.get("meta") or {})
    claim = str(payload.get("claim") or "").strip()
    reasoning = str(payload.get("reasoning") or "").strip()
    evidence = [str(e) for e in (payload.get("evidence") or []) if str(e).strip()]
    source = str(meta.get("source") or "external").strip().lower()
    if source not in ("jarvis", "external", "otem_justification"):
        source = "external"
    packet_id = str(packet.get("id") or packet.get("packet_id") or "").strip()
    return build_graph_from_flat_text(
        claim=claim,
        reasoning=reasoning,
        evidence=evidence,
        source=source,
        graph_id=packet_id or None,
    )


def from_jarvis_reasoning_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Build ReasoningGraph from Jarvis reasoning packet export."""
    if packet.get("reasoning_graph"):
        return normalize_reasoning_graph(dict(packet["reasoning_graph"]))

    objective_val = packet.get("objective")
    risks = list(packet.get("risks") or [])
    workspace_refs = list(packet.get("workspace_refs") or [])

    premises: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    evidence_refs: list[str] = []
    for ref in workspace_refs:
        if isinstance(ref, dict):
            file_path = str(ref.get("file_path") or "").strip()
            if file_path:
                evidence_refs.append(f"log:{file_path}")
        elif str(ref).strip():
            evidence_refs.append(str(ref).strip())

    for idx, risk in enumerate(risks[:5], start=1):
        pid = f"premise-{idx}"
        if isinstance(risk, dict):
            text = str(risk.get("message") or risk.get("summary") or risk.get("risk") or "").strip()
        else:
            text = str(risk).strip()
        if text:
            premises.append(
                {
                    "id": pid,
                    "kind": "premise",
                    "text": text,
                    "evidence_refs": evidence_refs,
                }
            )

    if isinstance(objective_val, dict):
        objective_text = str(objective_val.get("summary") or objective_val.get("goal") or "").strip()
    elif isinstance(objective_val, str):
        objective_text = objective_val.strip()
    else:
        objective_text = ""
    if not objective_text:
        objective_text = str(packet.get("summary") or packet.get("intent") or "deliberation objective").strip()

    inference_id = "inference-1"
    conclusion_id = "conclusion-1"
    nodes = list(premises)
    if premises:
        nodes.append(
            {
                "id": inference_id,
                "kind": "inference",
                "text": f"Synthesis toward: {objective_text}",
                "evidence_refs": evidence_refs,
            }
        )
        for p in premises:
            edges.append({"from": p["id"], "to": inference_id, "relation": "supports"})
    nodes.append(
        {
            "id": conclusion_id,
            "kind": "conclusion",
            "text": objective_text,
            "evidence_refs": evidence_refs,
        }
    )
    if premises:
        edges.append({"from": inference_id, "to": conclusion_id, "relation": "derives"})

    return normalize_reasoning_graph(
        {
            "id": str(packet.get("id") or packet.get("packet_id") or "jarvis-reasoning"),
            "version": "1.0",
            "source": "jarvis",
            "nodes": nodes,
            "edges": edges,
            "conclusion_id": conclusion_id,
            "proposed_action": dict(packet.get("proposed_action") or {}) or None,
        }
    )


def from_otem_justification(payload: dict[str, Any]) -> dict[str, Any]:
    """Build ReasoningGraph from OTEM escalation justification attachment."""
    if payload.get("reasoning_graph"):
        graph = normalize_reasoning_graph(dict(payload["reasoning_graph"]))
        graph["source"] = "otem_justification"
        return graph

    return build_graph_from_flat_text(
        claim=str(payload.get("claim") or payload.get("justification") or "").strip(),
        reasoning=str(payload.get("reasoning") or payload.get("rationale") or "").strip(),
        evidence=[str(e) for e in (payload.get("evidence") or payload.get("evidence_refs") or [])],
        source="otem_justification",
        proposed_action=dict(payload.get("proposed_action") or {}) or None,
        graph_id=str(payload.get("graph_id") or payload.get("approval_id") or "") or None,
    )
