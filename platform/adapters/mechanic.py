"""Mechanic scan adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mechanic.diagnosis.engine import diagnose_genome
from mechanic.mechanic import MechanicRequest, persist_case_artifacts, rebuild_request, scan_request


def run_mechanic_scan(*, case_id: str, repo_path: str, trace_path: str = "", runtime_root: Path | None = None) -> dict[str, Any]:
    repo = Path(repo_path).expanduser().resolve()
    if not repo.is_dir():
        raise ValueError(f"repo not found: {repo}")
    mech_root = runtime_root or Path(".runtime/mechanic")
    request = MechanicRequest(
        case_id=case_id,
        repo_path=str(repo),
        scope="platform",
        goal="platform-scan",
    )
    scan_result = scan_request(request, trace_path=trace_path)
    genome = scan_result["genome"]
    scan = diagnose_genome(genome, case_id=case_id)
    rebuild = rebuild_request(request, genome=genome, scan=scan)
    mech_dir = mech_root / case_id
    persist_case_artifacts(
        case_id=case_id,
        case_dir=mech_dir,
        genome=genome,
        scan=scan,
        rebuild=rebuild,
        ledger_path=mech_dir / "diagnostic_ledger.jsonl",
        drift_index_path=mech_dir / "health_drift_index.jsonl",
    )
    return {
        "case_id": case_id,
        "artifact_dir": str(mech_dir),
        "scan": scan,
        "drift_count": len(scan.get("drifts") or []),
    }
