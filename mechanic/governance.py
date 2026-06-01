"""Governance snapshots and traceability for AI Mechanic."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from pathlib import Path
from typing import Any, Literal

from mechanic.common import ClaimLabel, derive_claim_status, hash_text, json_stable, sha256_file
from mechanic.ledger import ledger_summary

SNAPSHOT_VERSION = "mechanic.snapshot.v1"
PROOF_REPORT_VERSION = "mechanic.proof_report.v1"


def build_proof_report(
    *,
    case_id: str,
    scan_path: Path,
    ledger_path: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    normalized_time = generated_at_utc or datetime.now(UTC).isoformat()
    scan_claim: ClaimLabel = "asserted"
    scan_hash = ""
    if scan_path.exists():
        try:
            import json

            payload = json.loads(scan_path.read_text(encoding="utf-8"))
            scan_claim = "proven" if int(payload.get("drift_count") or 0) > 0 else "asserted"
            scan_hash = sha256_file(scan_path)
        except (OSError, json.JSONDecodeError):
            scan_claim = "rejected"
    ledger_info = ledger_summary(ledger_path)
    ledger_claim: ClaimLabel = (
        "proven" if ledger_info["entries"] > 0 else ("asserted" if ledger_info["exists"] else "rejected")
    )
    overall = derive_claim_status([scan_claim, ledger_claim])
    return {
        "report_version": PROOF_REPORT_VERSION,
        "generated_at_utc": normalized_time,
        "case_id": case_id,
        "claim_label": overall,
        "safety_state": "dry_run_only",
        "scan_artifact": {"path": str(scan_path), "claim_label": scan_claim, "sha256": scan_hash},
        "ledger": {"path": str(ledger_path), "claim_label": ledger_claim, "summary": ledger_info},
    }


def build_snapshot(
    *,
    case_id: str,
    report_path: Path,
    ledger_path: Path,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    import json

    created_at = created_at_utc or datetime.now(UTC).isoformat()
    report_hash = sha256_file(report_path) if report_path.exists() else ""
    ledger_hash = sha256_file(ledger_path) if ledger_path.exists() else ""
    seed = hash_text(json_stable({"case_id": case_id, "report_hash": report_hash, "ledger_hash": ledger_hash}))
    report_claim: ClaimLabel = "asserted"
    if report_path.exists():
        try:
            rep = json.loads(report_path.read_text(encoding="utf-8"))
            parsed = str(rep.get("claim_label") or "asserted")
            report_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            report_claim = "rejected"
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_id": f"mcsnap-{seed[:16]}",
        "case_id": case_id,
        "created_at_utc": created_at,
        "claim_label": report_claim,
        "linkage": {"report_hash": report_hash, "ledger_hash": ledger_hash},
        "safety_state": "dry_run_only",
    }


def status_summary(case_dir: Path) -> dict[str, Any]:
    genome_path = case_dir / "process_genome.v1.json"
    scan_path = case_dir / "mechanic_scan.v1.json"
    return {
        "case_dir": str(case_dir),
        "genome_exists": genome_path.exists(),
        "scan_exists": scan_path.exists(),
        "target_workflow_exists": (case_dir / "target_workflow.v1.json").exists(),
        "runtime_profile_exists": (case_dir / "MECHANIC_RUNTIME_PROFILE.json").exists(),
    }
