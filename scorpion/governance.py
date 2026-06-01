"""Governance traceability: snapshot index, status, snapshot-query."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
from pathlib import Path
from typing import Any

from scorpion.common import ClaimLabel, derive_claim_status, hash_text, json_stable, sha256_file
from scorpion.ledger import ledger_summary


def traceability_drift_summary(
    *,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
) -> dict[str, Any]:
    ledger_hash = sha256_file(ledger_path) if ledger_path.exists() else ""
    report_hash = sha256_file(report_path) if report_path.exists() else ""
    snapshot_hash = ""
    linkage_ok = True
    snapshot_claim: ClaimLabel = "asserted"
    if snapshot_path.exists():
        try:
            snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
            linkage = snap.get("linkage") or {}
            snapshot_hash = sha256_file(snapshot_path)
            if linkage.get("report_hash") and linkage["report_hash"] != report_hash:
                linkage_ok = False
            if linkage.get("ledger_hash") and linkage["ledger_hash"] != ledger_hash:
                linkage_ok = False
            parsed = str(snap.get("claim_label") or "asserted")
            snapshot_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            linkage_ok = False
            snapshot_claim = "rejected"
    drift = not linkage_ok
    claim: ClaimLabel = "rejected" if drift else derive_claim_status(
        [snapshot_claim, "proven" if ledger_path.exists() else "asserted"]
    )
    return {
        "drift_detected": drift,
        "claim_label": claim,
        "ledger_hash": ledger_hash,
        "report_hash": report_hash,
        "snapshot_hash": snapshot_hash,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return rows


def build_snapshot_index_record(
    *,
    snapshot_path: Path,
    report_path: Path,
    ledger_path: Path,
    case_id: str,
    previous_entry: dict[str, Any] | None = None,
    supersedes_snapshot_id: str = "",
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    created_at = created_at_utc or datetime.now(UTC).isoformat()
    snapshot_hash = sha256_file(snapshot_path) if snapshot_path.exists() else ""
    report_hash = sha256_file(report_path) if report_path.exists() else ""
    ledger_hash = sha256_file(ledger_path) if ledger_path.exists() else ""
    snapshot_id = ""
    snapshot_claim: ClaimLabel = "rejected"
    if snapshot_path.exists():
        try:
            snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot_id = str(snap.get("snapshot_id") or "")
            parsed = str(snap.get("claim_label") or "asserted")
            snapshot_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            snapshot_claim = "rejected"
    report_claim: ClaimLabel = "asserted" if report_path.exists() else "rejected"
    if report_path.exists():
        try:
            rep = json.loads(report_path.read_text(encoding="utf-8"))
            parsed = str(rep.get("claim_label") or "asserted")
            report_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            report_claim = "rejected"
    ledger_info = ledger_summary(ledger_path)
    ledger_claim: ClaimLabel = (
        "proven" if int(ledger_info.get("entries") or 0) > 0 else ("asserted" if ledger_info["exists"] else "rejected")
    )
    overall = derive_claim_status([snapshot_claim, report_claim, ledger_claim])
    prior = str((previous_entry or {}).get("claim_label") or "origin")
    transition = f"{prior}->{overall}"
    supersedes = supersedes_snapshot_id.strip() or str((previous_entry or {}).get("snapshot_id") or "")
    seed = hash_text(
        json_stable(
            {
                "case_id": case_id,
                "snapshot_id": snapshot_id,
                "created_at_utc": created_at,
                "transition": transition,
            }
        )
    )
    return {
        "index_version": "scorpion.snapshot_index.v1",
        "index_id": f"scidx-{seed[:16]}",
        "created_at_utc": created_at,
        "case_id": case_id,
        "claim_label": overall,
        "claim_transition": transition,
        "snapshot_id": snapshot_id,
        "snapshot_sha256": snapshot_hash,
        "report_sha256": report_hash,
        "ledger_sha256": ledger_hash,
        "supersedes_snapshot_id": supersedes,
    }


def append_snapshot_index_record(record: dict[str, Any], index_path: Path) -> None:
    target = index_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json_stable(record))
        handle.write("\n")


def query_snapshot_index(
    index_path: Path,
    *,
    snapshot_id: str = "",
    case_id: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    entries = _read_jsonl(index_path)
    if snapshot_id.strip():
        entries = [e for e in entries if str(e.get("snapshot_id") or "") == snapshot_id.strip()]
    if case_id.strip():
        entries = [e for e in entries if str(e.get("case_id") or "") == case_id.strip()]
    if limit > 0:
        entries = entries[-limit:]
    claim: ClaimLabel = "proven" if entries else "asserted"
    return {
        "mode": "snapshot-query",
        "claim_label": claim,
        "entry_count": len(entries),
        "entries": entries,
    }


def status_summary(
    *,
    case_id: str,
    proof_dir: Path,
    ledger_path: Path,
) -> dict[str, Any]:
    drift = traceability_drift_summary(
        ledger_path=ledger_path,
        report_path=proof_dir / "scorpion_report.json",
        snapshot_path=proof_dir / "scorpion_snapshot.json",
    )
    index_entries = _read_jsonl(proof_dir / "scorpion_snapshot_index.jsonl")
    health_entries = _read_jsonl(proof_dir / "health_drift_index.jsonl")
    stages = {
        "stage_1_observation": {"claim_label": "proven", "sentinels": ["fixture", "audit", "kernel"]},
        "stage_2_historian": {
            "claim_label": "proven" if health_entries else "asserted",
            "health_drift_rows": len(health_entries),
        },
        "stage_3_wolf_seam": {
            "claim_label": "asserted",
            "ingest_activation": "SCORPION_WOLF_INGEST=active",
        },
        "stage_4_kernel_sentinel": {
            "claim_label": "asserted",
            "native_ebpf": "not_in_tree",
            "audit_export_adapter": "proven",
        },
    }
    return {
        "mode": "status",
        "case_id": case_id,
        "claim_label": str(drift.get("claim_label") or "asserted"),
        "safety_state": "dry_run_only",
        "traceability": drift,
        "snapshot_index_rows": len(index_entries),
        "stages": stages,
    }


def query_governance_trace(
    *,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
) -> dict[str, Any]:
    if not ledger_path.exists():
        return {"mode": "trace-query", "claim_label": "rejected", "reason": "ledger missing"}
    report_claim: ClaimLabel = "rejected"
    if report_path.exists():
        try:
            rep = json.loads(report_path.read_text(encoding="utf-8"))
            parsed = str(rep.get("claim_label") or "asserted")
            report_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            report_claim = "rejected"
    drift = traceability_drift_summary(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
    )
    overall = derive_claim_status([report_claim, str(drift.get("claim_label") or "asserted")])
    return {
        "mode": "trace-query",
        "claim_label": overall,
        "ledger": ledger_summary(ledger_path),
        "report": {"path": str(report_path), "claim_label": report_claim},
        "drift": drift,
    }


def query_governance_reconciliation(
    *,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
) -> dict[str, Any]:
    drift = traceability_drift_summary(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
    )
    hints: list[str] = []
    if drift.get("drift_detected"):
        hints.append("regenerate report then snapshot then snapshot-index")
    return {
        "mode": "reconcile-query",
        "claim_label": str(drift.get("claim_label") or "asserted"),
        "drift_count": 1 if drift.get("drift_detected") else 0,
        "remediation_hints": hints,
        "drift": drift,
    }
