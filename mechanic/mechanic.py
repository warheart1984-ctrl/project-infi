"""AI Mechanic MVP — scan, diagnose, rebuild (dry-run defaults)."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from mechanic.common import ClaimLabel, json_stable
from mechanic.diagnosis.engine import diagnose_genome
from mechanic.genome.extractor import extract_process_genome
from mechanic.governance import build_proof_report, build_snapshot, status_summary
from mechanic.historian import append_drift_record, build_drift_index_record, read_drift_index
from mechanic.ledger import append_claim_record, build_claim_record, ledger_summary
from mechanic.rebuild.planner import build_rebuild_bundle

ALLOWED_MODES = {
    "observe",
    "scan",
    "diagnose",
    "rebuild",
    "extract",
    "status",
    "verify",
    "chaos-check",
    "apply",
    "apply-review",
    "report",
}


class MechanicError(ValueError):
    """Raised when a Mechanic request violates gate constraints."""


@dataclass(slots=True)
class MechanicRequest:
    case_id: str
    repo_path: str = ""
    scope: str = "ai"
    goal: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def default_case_dir(case_id: str, *, runtime_root: Path | None = None) -> Path:
    root = runtime_root or Path(".runtime/mechanic")
    return root / case_id


def _load_profile_metadata(repo_path: Path) -> dict[str, Any]:
    profile = repo_path / ".mechanic-profile.json"
    if profile.is_file():
        try:
            payload = json.loads(profile.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def observe_request(request: MechanicRequest) -> dict[str, Any]:
    from mechanic.genome.adapters.registry import list_adapter_ids

    return {
        "mode": "observe",
        "case_id": request.case_id,
        "scope": request.scope,
        "goal": request.goal,
        "repo_path": request.repo_path,
        "adapters": list_adapter_ids(),
        "claim_label": "proven",
        "safety_state": "dry_run_only",
    }


def scan_request(request: MechanicRequest, *, trace_path: str = "") -> dict[str, Any]:
    if not request.repo_path.strip():
        raise MechanicError("repo-path is required for scan mode.")
    genome = extract_process_genome(
        case_id=request.case_id,
        repo_path=request.repo_path,
        trace_path=trace_path or None,
    )
    profile_meta = _load_profile_metadata(Path(request.repo_path))
    if profile_meta:
        genome["metadata"] = {**(genome.get("metadata") or {}), **profile_meta}
    return {
        "mode": "scan",
        "case_id": request.case_id,
        "genome": genome,
        "genome_hash": genome.get("genome_hash"),
        "node_count": len(genome.get("nodes") or []),
        "edge_count": len(genome.get("edges") or []),
        "claim_label": "proven",
        "safety_state": "dry_run_only",
    }


def diagnose_request(request: MechanicRequest, *, genome: dict[str, Any] | None = None) -> dict[str, Any]:
    if genome is None:
        case_dir = default_case_dir(request.case_id)
        genome_path = case_dir / "process_genome.v1.json"
        if not genome_path.exists():
            raise MechanicError("genome not found; run scan first or pass repo-path to scan+diagnose.")
        genome = json.loads(genome_path.read_text(encoding="utf-8"))
    return diagnose_genome(genome, case_id=request.case_id)


def rebuild_request(
    request: MechanicRequest,
    *,
    genome: dict[str, Any] | None = None,
    scan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if genome is None:
        case_dir = default_case_dir(request.case_id)
        genome = json.loads((case_dir / "process_genome.v1.json").read_text(encoding="utf-8"))
    if scan is None:
        case_dir = default_case_dir(request.case_id)
        scan = json.loads((case_dir / "mechanic_scan.v1.json").read_text(encoding="utf-8"))
    drifts = list(scan.get("drifts") or [])
    return build_rebuild_bundle(case_id=request.case_id, genome=genome, drifts=drifts)


def extract_request(request: MechanicRequest) -> dict[str, Any]:
    scan = diagnose_request(request)
    drifts = scan.get("drifts") or []
    return {
        "mode": "extract",
        "case_id": request.case_id,
        "drift_count": len(drifts),
        "codes": sorted({str(d.get("code")) for d in drifts}),
        "claim_label": scan.get("claim_label", "asserted"),
        "safety_state": "dry_run_only",
    }


def verify_request(
    *,
    case_id: str,
    case_dir: Path,
    ledger_path: Path,
) -> dict[str, Any]:
    scan_path = case_dir / "mechanic_scan.v1.json"
    report = build_proof_report(case_id=case_id, scan_path=scan_path, ledger_path=ledger_path)
    snapshot = build_snapshot(
        case_id=case_id,
        report_path=case_dir / "mechanic_proof_report.json",
        ledger_path=ledger_path,
    )
    ok = scan_path.exists() and (case_dir / "process_genome.v1.json").exists()
    return {
        "mode": "verify",
        "case_id": case_id,
        "ok": ok,
        "claim_label": report.get("claim_label"),
        "proof_report": report,
        "snapshot": snapshot,
        "safety_state": "dry_run_only",
    }


def persist_case_artifacts(
    *,
    case_id: str,
    case_dir: Path,
    genome: dict[str, Any] | None = None,
    scan: dict[str, Any] | None = None,
    rebuild: dict[str, Any] | None = None,
    ledger_path: Path | None = None,
    drift_index_path: Path | None = None,
) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    if genome is not None:
        (case_dir / "process_genome.v1.json").write_text(
            json.dumps(genome, sort_keys=True, indent=2),
            encoding="utf-8",
        )
    if scan is not None:
        (case_dir / "mechanic_scan.v1.json").write_text(
            json.dumps(scan, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        if ledger_path and int(scan.get("drift_count") or 0) > 0:
            for drift in scan.get("drifts") or []:
                code = str(drift.get("code") or "")
                record = build_claim_record(
                    case_id=case_id,
                    mode="diagnose",
                    invariant_id=code,
                    code=code,
                    claim_label="asserted",
                    reviewer="mechanic",
                    reason=str(drift.get("drift_summary") or ""),
                    drift_summary=str(drift.get("drift_summary") or ""),
                    evidence_hash=str(drift.get("code") or ""),
                )
                append_claim_record(record, ledger_path)
        if drift_index_path is not None:
            previous = read_drift_index(drift_index_path)
            prev = previous[-1] if previous else None
            record = build_drift_index_record(
                case_id=case_id,
                drift_count=int(scan.get("drift_count") or 0),
                claim_label=scan.get("claim_label", "asserted"),
                scan_hash=str(scan.get("scan_hash") or ""),
                previous=prev,
            )
            append_drift_record(record, drift_index_path)
    if rebuild is not None:
        (case_dir / "target_workflow.v1.json").write_text(
            json.dumps(rebuild["target_workflow"], sort_keys=True, indent=2),
            encoding="utf-8",
        )
        (case_dir / "patch_plan.v1.json").write_text(
            json.dumps(rebuild["patch_plan"], sort_keys=True, indent=2),
            encoding="utf-8",
        )
        (case_dir / "MECHANIC_RUNTIME_PROFILE.json").write_text(
            json.dumps(rebuild["runtime_profile"], sort_keys=True, indent=2),
            encoding="utf-8",
        )
        (case_dir / "reconstruction_plan.v1.json").write_text(
            json.dumps(rebuild["reconstruction_plan"], sort_keys=True, indent=2),
            encoding="utf-8",
        )


def run_chaos_checks() -> dict[str, Any]:
    """Deterministic self-check for CI."""
    from mechanic.invariants.evaluators import evaluate_all
    from mechanic.genome.schema import empty_genome, add_node

    genome = empty_genome(case_id="chaos", repo_path=".")
    add_node(genome, node_id="mc1", node_type="model_call", label="x", source_path="a.py")
    add_node(genome, node_id="mc2", node_type="model_call", label="y", source_path="a.py")
    drifts = evaluate_all(genome)
    ok = any(str(d.get("code")) == "CST-07" for d in drifts)
    return {
        "mode": "chaos-check",
        "claim_label": "proven" if ok else "rejected",
        "drift_count": len(drifts),
        "safety_state": "dry_run_only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Mechanic — governed AI workflow forensics")
    parser.add_argument("--mode", required=True, choices=sorted(ALLOWED_MODES))
    parser.add_argument("--case-id", default="mechanic-default")
    parser.add_argument("--repo-path", default="")
    parser.add_argument("--scope", default="ai")
    parser.add_argument("--goal", default="")
    parser.add_argument("--runtime-dir", default=".runtime/mechanic")
    parser.add_argument("--ledger-path", default=".runtime/mechanic/diagnostic_ledger.jsonl")
    parser.add_argument("--drift-index", default="docs/proof/mechanic/health_drift_index.jsonl")
    parser.add_argument("--write-json", action="store_true", help="Persist artifacts to case dir")
    parser.add_argument("--trace-path", default="", help="Optional NDJSON trace file for scan")
    parser.add_argument(
        "--create-review",
        action="store_true",
        help="Required for apply-review mode to create patch review records",
    )
    args = parser.parse_args(argv)

    mode: Literal[str] = args.mode
    request = MechanicRequest(case_id=args.case_id, repo_path=args.repo_path, scope=args.scope, goal=args.goal)
    runtime_root = Path(args.runtime_dir)
    case_dir = default_case_dir(request.case_id, runtime_root=runtime_root)
    ledger_path = Path(args.ledger_path)
    drift_index_path = Path(args.drift_index)

    try:
        if mode == "apply":
            raise MechanicError("apply mode is blocked in MVP (dry-run only).")
        if mode == "apply-review":
            if not args.create_review:
                raise MechanicError("apply-review requires --create-review (review records only).")
            from mechanic.apply.review_gated import create_apply_review

            payload = create_apply_review(case_id=request.case_id, case_dir=case_dir)
            if args.write_json:
                (case_dir / "mechanic_apply_review.json").write_text(
                    json.dumps(payload, sort_keys=True, indent=2),
                    encoding="utf-8",
                )
        elif mode == "report":
            from mechanic.report import build_report_payload

            payload = build_report_payload(case_id=request.case_id, case_dir=case_dir)
            if args.write_json:
                (case_dir / "report.md").write_text(payload["report_markdown"], encoding="utf-8")
        elif mode == "observe":
            payload = observe_request(request)
        elif mode == "scan":
            result = scan_request(request, trace_path=args.trace_path)
            genome = result.pop("genome")
            payload = result
            if args.write_json:
                persist_case_artifacts(case_id=request.case_id, case_dir=case_dir, genome=genome)
            else:
                payload["genome"] = genome
        elif mode == "diagnose":
            if request.repo_path.strip():
                scan_result = scan_request(request, trace_path=args.trace_path)
                genome = scan_result["genome"]
                payload = diagnose_genome(genome, case_id=request.case_id)
                if args.write_json:
                    persist_case_artifacts(
                        case_id=request.case_id,
                        case_dir=case_dir,
                        genome=genome,
                        scan=payload,
                        ledger_path=ledger_path,
                        drift_index_path=drift_index_path,
                    )
            else:
                payload = diagnose_request(request)
                if args.write_json:
                    persist_case_artifacts(
                        case_id=request.case_id,
                        case_dir=case_dir,
                        scan=payload,
                        ledger_path=ledger_path,
                        drift_index_path=drift_index_path,
                    )
        elif mode == "rebuild":
            if request.repo_path.strip():
                scan_result = scan_request(request, trace_path=args.trace_path)
                genome = scan_result["genome"]
                scan_payload = diagnose_genome(genome, case_id=request.case_id)
            else:
                genome = None
                scan_payload = None
            payload = rebuild_request(request, genome=genome, scan=scan_payload)
            if args.write_json:
                if genome is None:
                    genome = json.loads((case_dir / "process_genome.v1.json").read_text(encoding="utf-8"))
                if scan_payload is None:
                    scan_payload = json.loads((case_dir / "mechanic_scan.v1.json").read_text(encoding="utf-8"))
                persist_case_artifacts(
                    case_id=request.case_id,
                    case_dir=case_dir,
                    genome=genome,
                    scan=scan_payload,
                    rebuild=payload,
                    ledger_path=ledger_path,
                    drift_index_path=drift_index_path,
                )
        elif mode == "extract":
            if request.repo_path.strip():
                scan_result = scan_request(request, trace_path=args.trace_path)
                genome = scan_result["genome"]
                scan_payload = diagnose_genome(genome, case_id=request.case_id)
                payload = {
                    "mode": "extract",
                    "case_id": request.case_id,
                    "drift_count": scan_payload.get("drift_count"),
                    "codes": sorted({str(d.get("code")) for d in scan_payload.get("drifts") or []}),
                    "claim_label": scan_payload.get("claim_label"),
                    "safety_state": "dry_run_only",
                }
            else:
                payload = extract_request(request)
        elif mode == "status":
            payload = {
                "mode": "status",
                "case_id": request.case_id,
                **status_summary(case_dir),
                "ledger": ledger_summary(ledger_path),
            }
        elif mode == "chaos-check":
            payload = run_chaos_checks()
        elif mode == "verify":
            payload = verify_request(case_id=request.case_id, case_dir=case_dir, ledger_path=ledger_path)
            if args.write_json:
                (case_dir / "mechanic_proof_report.json").write_text(
                    json.dumps(payload["proof_report"], sort_keys=True, indent=2),
                    encoding="utf-8",
                )
                (case_dir / "mechanic_snapshot.json").write_text(
                    json.dumps(payload["snapshot"], sort_keys=True, indent=2),
                    encoding="utf-8",
                )
        else:
            raise MechanicError(f"unsupported mode: {mode}")
    except MechanicError as exc:
        print(json.dumps({"error": str(exc), "mode": mode, "case_id": request.case_id}, sort_keys=True))
        return 1

    print(json.dumps(payload, sort_keys=True, indent=2 if mode in {"status", "verify"} else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
