"""Phase 1 — Pullback: preload governance frame from Mechanic forensics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mechanic.hosted.models import SignoffPolicy
from mechanic.mechanic import MechanicRequest, persist_case_artifacts, rebuild_request, scan_request
from mechanic.diagnosis.engine import diagnose_genome

from slingshot.common import (
    DEFAULT_MECHANIC_ROOT,
    DEFAULT_SLINGSHOT_ROOT,
    FRAME_VERSION,
    _slingshot_cache_get,
    _slingshot_cache_put,
    frame_path,
    json_stable,
    mechanic_case_dir,
    slingshot_case_dir,
    slingshot_json_cache_key,
)


def _ma13_summary(drifts: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"I": 0, "II": 0, "III": 0}
    for drift in drifts:
        cls = str(drift.get("ma13_class") or "").upper()
        if cls in counts:
            counts[cls] += 1
    return counts


def _launch_blocked(drifts: list[dict[str, Any]], *, policy: SignoffPolicy | None = None) -> tuple[bool, list[str]]:
    """Return (blocked, reasons)."""
    signoff = policy or SignoffPolicy()
    reasons: list[str] = []
    for drift in drifts:
        ma13 = str(drift.get("ma13_class") or "").upper()
        if ma13 == "III":
            code = str(drift.get("code") or drift.get("invariant_id") or "unknown")
            reasons.append(f"class_III_drift:{code}")
        elif signoff.requires_signoff(drift):
            code = str(drift.get("code") or drift.get("invariant_id") or "unknown")
            reasons.append(f"signoff_required:{code}")
    return bool(reasons), reasons


def build_slingshot_frame(
    *,
    case_id: str,
    repo_path: str | Path,
    trace_path: str = "",
    slingshot_root: Path | None = None,
    mechanic_root: Path | None = None,
    signoff_policy: SignoffPolicy | None = None,
) -> dict[str, Any]:
    """Run Mechanic scan→diagnose→rebuild and emit SLINGSHOT_FRAME.v1."""
    repo = Path(repo_path).expanduser().resolve()
    if not repo.is_dir():
        raise ValueError(f"repo path not found: {repo}")

    shot_root = slingshot_root or DEFAULT_SLINGSHOT_ROOT
    mech_root = mechanic_root or DEFAULT_MECHANIC_ROOT
    mech_dir = mechanic_case_dir(case_id, runtime_root=mech_root)
    shot_dir = slingshot_case_dir(case_id, runtime_root=shot_root)
    shot_dir.mkdir(parents=True, exist_ok=True)

    request = MechanicRequest(
        case_id=case_id,
        repo_path=str(repo),
        scope="ai-platform",
        goal="slingshot-preload",
    )
    scan_result = scan_request(request, trace_path=trace_path)
    genome = scan_result["genome"]
    scan = diagnose_genome(genome, case_id=case_id)
    rebuild = rebuild_request(request, genome=genome, scan=scan)

    ledger_path = mech_dir / "diagnostic_ledger.jsonl"
    drift_index_path = mech_dir / "health_drift_index.jsonl"
    persist_case_artifacts(
        case_id=case_id,
        case_dir=mech_dir,
        genome=genome,
        scan=scan,
        rebuild=rebuild,
        ledger_path=ledger_path,
        drift_index_path=drift_index_path,
    )

    drifts = list(scan.get("drifts") or [])
    profile = rebuild.get("runtime_profile") or {}
    profile_rel = str(Path(".runtime/mechanic") / case_id / "MECHANIC_RUNTIME_PROFILE.json")
    blocked, block_reasons = _launch_blocked(drifts, policy=signoff_policy)

    frame: dict[str, Any] = {
        "frame_version": FRAME_VERSION,
        "case_id": case_id,
        "repo_path": str(repo),
        "genome_hash": str(genome.get("genome_hash") or scan.get("genome_hash") or ""),
        "scan_hash": str(scan.get("scan_hash") or ""),
        "active_invariants": sorted({str(d.get("code") or "") for d in drifts if d.get("code")}),
        "ma13_summary": _ma13_summary(drifts),
        "launch_blocked": blocked,
        "launch_block_reasons": block_reasons,
        "runtime_profile_path": profile_rel,
        "mechanic_case_dir": str(mech_dir),
        "zero_write_constraints": True,
        "drift_count": len(drifts),
        "claim_label": "asserted",
        "safety_state": "dry_run_only",
    }
    if profile:
        frame["runtime_profile_hash"] = json_stable(profile)

    target = frame_path(case_id, runtime_root=shot_root)
    target.write_text(json.dumps(frame, sort_keys=True, indent=2), encoding="utf-8")
    return frame


def load_slingshot_frame(case_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    path = frame_path(case_id, runtime_root=runtime_root)
    if not path.is_file():
        raise FileNotFoundError(f"SLINGSHOT_FRAME not found for case {case_id}")
    cache_key = slingshot_json_cache_key("frame", path)
    cached = _slingshot_cache_get(cache_key)
    if cached is not None:
        return cached
    payload = json.loads(path.read_text(encoding="utf-8"))
    if str(payload.get("frame_version") or "") != FRAME_VERSION:
        raise ValueError("invalid slingshot frame version")
    _slingshot_cache_put(cache_key, payload)
    return payload
