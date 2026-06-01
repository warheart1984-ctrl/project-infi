"""Provenance link discovery and causal edge materialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def discover_provenance_paths(runtime_root: Path) -> list[Path]:
    base = Path(runtime_root) / "collective-pattern-ledger"
    if not base.exists():
        return []
    return sorted({path for path in base.glob("**/provenance.jsonl") if path.is_file()})


def _read_jsonl(path: Path, *, max_rows: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if str(payload.get("record_type") or "") == "provenance_link":
                rows.append(payload)
    if max_rows is not None and max_rows > 0:
        return rows[-max_rows:]
    return rows


def load_provenance_links(
    paths: list[Path],
    *,
    max_rows_per_path: int | None = None,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        for row in _read_jsonl(path, max_rows=max_rows_per_path):
            key = str(row.get("provenance_id") or row.get("timestamp") or "")
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)
    return merged


def materialize_causal_edges(
    *,
    claims: list[dict[str, Any]],
    provenance_links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build persistent causal edges from claims and provenance links."""
    edges: list[dict[str, Any]] = []
    claim_ids = {str(row.get("claim_id") or "") for row in claims if row.get("claim_id")}

    for link in provenance_links:
        from_id = str(link.get("node_or_edge_id") or "")
        to_id = str(link.get("evidence_id") or "")
        if not from_id or not to_id:
            continue
        support = str(link.get("support_type") or "supports")
        edge_type = "evidences" if to_id.startswith("evidence-") else support
        edges.append(
            {
                "edge_id": str(link.get("provenance_id") or f"edge-{from_id}-{to_id}"),
                "from_id": from_id,
                "to_id": to_id,
                "edge_type": edge_type,
                "support_type": support,
                "weight": float(link.get("weight") or 0.5),
                "tenant_scope": "global",
                "source": "provenance_link",
            }
        )

    for claim in claims:
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id:
            continue
        tenant_scope = str(claim.get("tenant_scope") or "global")
        for ref in list(claim.get("evidence_refs") or []):
            ref_id = str(ref)
            if not ref_id:
                continue
            edges.append(
                {
                    "edge_id": f"edge-{claim_id}-{ref_id}",
                    "from_id": claim_id,
                    "to_id": ref_id,
                    "edge_type": "evidences",
                    "support_type": "supports",
                    "weight": float(claim.get("confidence") or 0.5),
                    "tenant_scope": tenant_scope,
                    "source": "claim_evidence_ref",
                }
            )
        subject = str(claim.get("subject") or "").strip().lower()
        predicate = str(claim.get("predicate") or "").strip().lower()
        for other in claims:
            other_id = str(other.get("claim_id") or "")
            if not other_id or other_id == claim_id:
                continue
            if str(other.get("object") or "").strip().lower() == subject:
                edges.append(
                    {
                        "edge_id": f"edge-causal-{other_id}-{claim_id}",
                        "from_id": other_id,
                        "to_id": claim_id,
                        "edge_type": "caused_by",
                        "support_type": "refines",
                        "weight": min(float(other.get("confidence") or 0.5), float(claim.get("confidence") or 0.5)),
                        "tenant_scope": tenant_scope,
                        "source": "subject_object_chain",
                        "meta": {"subject": subject, "predicate": predicate},
                    }
                )
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for edge in edges:
        key = str(edge.get("edge_id") or "")
        if key in seen:
            continue
        seen.add(key)
        if edge.get("from_id") in claim_ids or edge.get("to_id") in claim_ids:
            deduped.append(edge)
    return deduped
