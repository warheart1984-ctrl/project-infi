"""ReasoningGraph normalization and flat-text adapters."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

GRAPH_VERSION = "1.0"
EVIDENCE_REF_PREFIXES = ("odl:", "ugr:", "ir:", "log:", "external:")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug_id(prefix: str, *parts: str) -> str:
    raw = "|".join(str(p) for p in parts if p)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def normalize_reasoning_graph(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a ReasoningGraph dict."""
    graph = dict(raw or {})
    graph_id = str(graph.get("id") or _slug_id("rg", graph.get("timestamp", "")))
    nodes = list(graph.get("nodes") or [])
    edges = list(graph.get("edges") or [])
    conclusion_id = str(graph.get("conclusion_id") or "").strip()

    if not nodes:
        raise ValueError("reasoning graph requires at least one node")

    node_ids = {str(n.get("id")) for n in nodes if n.get("id")}
    if not conclusion_id:
        for node in nodes:
            if str(node.get("kind") or "").lower() == "conclusion":
                conclusion_id = str(node["id"])
                break
        if not conclusion_id:
            conclusion_id = str(nodes[-1].get("id") or "conclusion")

    normalized_nodes: list[dict[str, Any]] = []
    for node in nodes:
        nid = str(node.get("id") or "").strip()
        if not nid:
            continue
        kind = str(node.get("kind") or "inference").strip().lower()
        if kind not in ("premise", "inference", "conclusion"):
            kind = "inference"
        refs = [str(r).strip() for r in (node.get("evidence_refs") or []) if str(r).strip()]
        normalized_nodes.append(
            {
                "id": nid,
                "kind": kind,
                "text": str(node.get("text") or "").strip(),
                "evidence_refs": refs,
            }
        )

    normalized_edges: list[dict[str, Any]] = []
    for edge in edges:
        src = str(edge.get("from") or "").strip()
        dst = str(edge.get("to") or "").strip()
        relation = str(edge.get("relation") or "supports").strip().lower()
        if relation not in ("supports", "derives"):
            relation = "supports"
        if src and dst and src in node_ids and dst in node_ids:
            normalized_edges.append({"from": src, "to": dst, "relation": relation})

    source = str(graph.get("source") or "external").strip().lower()
    if source not in ("jarvis", "external", "otem_justification"):
        source = "external"

    return {
        "id": graph_id,
        "version": str(graph.get("version") or GRAPH_VERSION),
        "timestamp": str(graph.get("timestamp") or _utc_now_iso()),
        "source": source,
        "nodes": normalized_nodes,
        "edges": normalized_edges,
        "conclusion_id": conclusion_id,
        "proposed_action": dict(graph.get("proposed_action") or {}) or None,
    }


def normalize_evidence_refs(refs: list[str] | None) -> list[str]:
    """Prefix bare exchange/local evidence tokens with external: for RLS validation."""
    out: list[str] = []
    for raw in refs or []:
        ref = str(raw).strip()
        if not ref:
            continue
        if is_valid_evidence_ref(ref):
            out.append(ref)
        else:
            out.append(f"external:{ref}")
    return out


def build_graph_from_flat_text(
    *,
    claim: str,
    reasoning: str,
    evidence: list[str] | None = None,
    source: str = "external",
    proposed_action: dict[str, Any] | None = None,
    graph_id: str | None = None,
) -> dict[str, Any]:
    """Build a minimal ReasoningGraph from flat claim/reasoning/evidence."""
    claim_text = str(claim or "").strip()
    reasoning_text = str(reasoning or "").strip()
    refs = normalize_evidence_refs([str(e) for e in (evidence or []) if str(e).strip()])

    premise_id = "premise-1"
    inference_id = "inference-1"
    conclusion_id = "conclusion-1"

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    if reasoning_text:
        nodes.append(
            {
                "id": premise_id,
                "kind": "premise",
                "text": reasoning_text,
                "evidence_refs": refs,
            }
        )
        if claim_text and claim_text.lower() != reasoning_text.lower():
            nodes.append(
                {
                    "id": inference_id,
                    "kind": "inference",
                    "text": f"Therefore: {claim_text}",
                    "evidence_refs": refs,
                }
            )
            edges.append({"from": premise_id, "to": inference_id, "relation": "derives"})
            nodes.append(
                {
                    "id": conclusion_id,
                    "kind": "conclusion",
                    "text": claim_text,
                    "evidence_refs": refs,
                }
            )
            edges.append({"from": inference_id, "to": conclusion_id, "relation": "supports"})
        else:
            nodes.append(
                {
                    "id": conclusion_id,
                    "kind": "conclusion",
                    "text": claim_text or reasoning_text,
                    "evidence_refs": refs,
                }
            )
            edges.append({"from": premise_id, "to": conclusion_id, "relation": "supports"})
    else:
        nodes.append(
            {
                "id": conclusion_id,
                "kind": "conclusion",
                "text": claim_text,
                "evidence_refs": refs,
            }
        )

    return normalize_reasoning_graph(
        {
            "id": graph_id or _slug_id("rg", claim_text, reasoning_text),
            "version": GRAPH_VERSION,
            "timestamp": _utc_now_iso(),
            "source": source,
            "nodes": nodes,
            "edges": edges,
            "conclusion_id": conclusion_id,
            "proposed_action": proposed_action,
        }
    )


def claim_fingerprint(text: str) -> str:
    """Normalized fingerprint for falsity registry keys."""
    normalized = re.sub(r"\s+", " ", str(text or "").strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def is_valid_evidence_ref(ref: str) -> bool:
    ref_s = str(ref or "").strip().lower()
    return any(ref_s.startswith(p) for p in EVIDENCE_REF_PREFIXES)
