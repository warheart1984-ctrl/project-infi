"""Catalog + evaluators → mechanic_scan.v1 report."""

from __future__ import annotations

from typing import Any

from mechanic.common import SCAN_REPORT_VERSION, hash_text, json_stable
from mechanic.invariants.evaluators import evaluate_all, load_invariant_catalog


def diagnose_genome(
    genome: dict[str, Any],
    *,
    case_id: str | None = None,
) -> dict[str, Any]:
    drifts = evaluate_all(genome)
    return run_diagnosis(
        case_id=case_id or str(genome.get("case_id") or ""),
        genome_hash=str(genome.get("genome_hash") or ""),
        drifts=drifts,
        repo_path=str(genome.get("repo_path") or ""),
    )


def run_diagnosis(
    *,
    case_id: str,
    genome_hash: str,
    drifts: list[dict[str, Any]],
    repo_path: str = "",
) -> dict[str, Any]:
    catalog = load_invariant_catalog()
    scan_hash = hash_text(json_stable({"drifts": drifts, "genome_hash": genome_hash}))
    families = sorted({str(d.get("family") or "") for d in drifts if d.get("family")})
    claim_label = "proven" if drifts else "asserted"
    return {
        "schema_version": SCAN_REPORT_VERSION,
        "mode": "diagnose",
        "case_id": case_id,
        "repo_path": repo_path,
        "genome_hash": genome_hash,
        "catalog_version": str(catalog.get("schema_version") or ""),
        "drift_count": len(drifts),
        "drifts": drifts,
        "families_triggered": families,
        "scan_hash": scan_hash,
        "claim_label": claim_label,
        "safety_state": "dry_run_only",
    }
