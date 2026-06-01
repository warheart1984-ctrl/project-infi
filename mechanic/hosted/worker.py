"""Hosted worker wrapper around the local Mechanic pipeline."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from mechanic.common import sha256_file
from mechanic.governance import build_proof_report, build_snapshot
from mechanic.hosted.models import (
    EvidenceBundle,
    SignoffPolicy,
    build_artifact_manifest,
    trace_input_manifest,
)
from mechanic.hosted.obd_report import build_obd_report, render_obd_markdown
from mechanic.hosted.security import scrub_artifact_tree
from mechanic.mechanic import (
    MechanicRequest,
    persist_case_artifacts,
    rebuild_request,
    scan_request,
)
from mechanic.diagnosis.engine import diagnose_genome

ARTIFACT_NAMES = [
    "process_genome.v1.json",
    "mechanic_scan.v1.json",
    "target_workflow.v1.json",
    "patch_plan.v1.json",
    "MECHANIC_RUNTIME_PROFILE.json",
    "reconstruction_plan.v1.json",
    "report.md",
    "mechanic_proof_report.json",
    "mechanic_snapshot.json",
    "mechanic_obd_report.v1.json",
    "mechanic_obd_report.md",
    "replay_result.v1.json",
]


def run_hosted_scan(
    *,
    case_id: str,
    scan_id: str,
    repo_path: str | Path,
    artifact_dir: str | Path,
    repo_ref: str = "",
    trace_paths: list[str | Path] | None = None,
    policy: SignoffPolicy | None = None,
    proof_tier: str = "local",
    max_repo_bytes: int = 25_000_000,
) -> EvidenceBundle:
    root = Path(repo_path).expanduser().resolve()
    repo_bytes = _repo_size(root)
    if repo_bytes > max_repo_bytes:
        raise ValueError(f"repo exceeds hosted pilot size limit: {repo_bytes} > {max_repo_bytes}")
    case_dir = Path(artifact_dir).expanduser().resolve() / case_id
    ledger_path = case_dir / "diagnostic_ledger.jsonl"
    drift_index_path = case_dir / "health_drift_index.jsonl"
    trace_inputs = list(trace_paths or [])
    trace_path = str(trace_inputs[0]) if trace_inputs else ""
    signoff_policy = policy or SignoffPolicy()

    before = _repo_fingerprint(root)
    request = MechanicRequest(case_id=case_id, repo_path=str(root), scope="ai-platform", goal="hosted-pilot-scan")
    scan_result = scan_request(request, trace_path=trace_path)
    genome = scan_result["genome"]
    scan = diagnose_genome(genome, case_id=case_id)
    rebuild = rebuild_request(request, genome=genome, scan=scan)
    persist_case_artifacts(
        case_id=case_id,
        case_dir=case_dir,
        genome=genome,
        scan=scan,
        rebuild=rebuild,
        ledger_path=ledger_path,
        drift_index_path=drift_index_path,
    )

    from mechanic.report import build_report_payload

    report_payload = build_report_payload(case_id=case_id, case_dir=case_dir)
    (case_dir / "report.md").write_text(report_payload["report_markdown"], encoding="utf-8")

    proof_report = build_proof_report(
        case_id=case_id,
        scan_path=case_dir / "mechanic_scan.v1.json",
        ledger_path=ledger_path,
    )
    (case_dir / "mechanic_proof_report.json").write_text(json.dumps(proof_report, sort_keys=True, indent=2), encoding="utf-8")
    snapshot = build_snapshot(
        case_id=case_id,
        report_path=case_dir / "mechanic_proof_report.json",
        ledger_path=ledger_path,
    )
    (case_dir / "mechanic_snapshot.json").write_text(json.dumps(snapshot, sort_keys=True, indent=2), encoding="utf-8")

    replay = replay_scan(case_id=case_id, repo_path=root, original_case_dir=case_dir, trace_path=trace_path, tier=proof_tier)
    (case_dir / "replay_result.v1.json").write_text(json.dumps(replay, sort_keys=True, indent=2), encoding="utf-8")
    confidence = _confidence_from_replay(replay)
    scrubbed = scrub_artifact_tree(case_dir)
    artifacts = build_artifact_manifest(case_dir, artifact_names=ARTIFACT_NAMES)
    links = {name: meta["path"] for name, meta in artifacts.items() if not meta.get("missing")}
    obd = build_obd_report(
        case_id=case_id,
        scan=scan,
        policy=signoff_policy,
        confidence_label=confidence,
        artifact_links=links,
    )
    (case_dir / "mechanic_obd_report.v1.json").write_text(json.dumps(obd, sort_keys=True, indent=2), encoding="utf-8")
    (case_dir / "mechanic_obd_report.md").write_text(render_obd_markdown(obd), encoding="utf-8")

    after = _repo_fingerprint(root)
    bundle = EvidenceBundle(
        bundle_version="mechanic.evidence_bundle.v1",
        case_id=case_id,
        scan_id=scan_id,
        artifact_dir=str(case_dir),
        confidence_label=confidence,
        artifacts=build_artifact_manifest(case_dir, artifact_names=ARTIFACT_NAMES),
        trace_inputs=trace_input_manifest(trace_inputs),
        repo_ref=repo_ref,
        customer_repo_mutated=before != after,
    )
    payload = bundle.model_dump()
    payload["security"] = {"secret_scrubbed_files": scrubbed, "tenant_isolated": True}
    (case_dir / "evidence_bundle.v1.json").write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return bundle


def replay_scan(
    *,
    case_id: str,
    repo_path: str | Path,
    original_case_dir: Path,
    trace_path: str = "",
    tier: str = "local",
) -> dict[str, Any]:
    if tier in {"ci", "second_machine"}:
        env_key = "MECHANIC_CI_REPLAY_COMMAND" if tier == "ci" else "MECHANIC_SECOND_MACHINE_REPLAY_COMMAND"
        command = os.environ.get(env_key, "").strip()
        if not command:
            return {
                "schema_version": "mechanic.replay_result.v1",
                "case_id": case_id,
                "tier": tier,
                "matched": False,
                "claim_label": "asserted",
                "external_runner_unavailable": True,
                "reason": f"{env_key} is not configured",
            }
        completed = subprocess.run(
            command.split() + [str(repo_path), str(original_case_dir), trace_path],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        return {
            "schema_version": "mechanic.replay_result.v1",
            "case_id": case_id,
            "tier": tier,
            "matched": completed.returncode == 0,
            "claim_label": "proven" if completed.returncode == 0 else "rejected",
            "external_runner_command": command,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }

    replay_case = f"{case_id}-replay"
    request = MechanicRequest(case_id=replay_case, repo_path=str(repo_path), scope="ai-platform", goal="proof-replay")
    scan_result = scan_request(request, trace_path=trace_path)
    genome = scan_result["genome"]
    scan = diagnose_genome(genome, case_id=case_id)
    original_scan_path = original_case_dir / "mechanic_scan.v1.json"
    original_genome_path = original_case_dir / "process_genome.v1.json"
    replay_scan_hash = str(scan.get("scan_hash") or "")
    replay_genome_hash = str(genome.get("genome_hash") or "")
    original_scan = json.loads(original_scan_path.read_text(encoding="utf-8")) if original_scan_path.is_file() else {}
    original_genome = json.loads(original_genome_path.read_text(encoding="utf-8")) if original_genome_path.is_file() else {}
    matched = (
        replay_scan_hash == str(original_scan.get("scan_hash") or "")
        and replay_genome_hash == str(original_genome.get("genome_hash") or "")
    )
    return {
        "schema_version": "mechanic.replay_result.v1",
        "case_id": case_id,
        "tier": tier,
        "matched": matched,
        "claim_label": "proven" if matched else "rejected",
        "original_scan_hash": str(original_scan.get("scan_hash") or ""),
        "replay_scan_hash": replay_scan_hash,
        "original_genome_hash": str(original_genome.get("genome_hash") or ""),
        "replay_genome_hash": replay_genome_hash,
    }


def _confidence_from_replay(replay: dict[str, Any]) -> str:
    if replay.get("external_runner_unavailable"):
        return "asserted"
    if not replay.get("matched"):
        return "rejected"
    tier = str(replay.get("tier") or "local")
    if tier == "second_machine":
        return "second_machine_proven"
    if tier == "ci":
        return "ci_proven"
    return "local_proven"


def _repo_fingerprint(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if not item.is_file():
            continue
        rel = str(item.relative_to(path)).replace("\\", "/")
        if rel.startswith(".git/"):
            continue
        try:
            result[rel] = sha256_file(item)
        except OSError:
            result[rel] = "unreadable"
    return result


def _repo_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        rel = str(item.relative_to(path)).replace("\\", "/")
        if rel.startswith(".git/"):
            continue
        try:
            total += item.stat().st_size
        except OSError:
            continue
    return total
