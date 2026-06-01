"""Scorpion Stages 1-4 governed OS anomaly extractor (dry-run defaults)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from src.datetime_compat import UTC
import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Literal

from scorpion.common import ClaimLabel, derive_claim_status, hash_text, json_stable, sha256_file
from scorpion.events import TraceEvent
from scorpion.extractor import extract_anomaly_bundle
from scorpion.governance import (
    append_snapshot_index_record,
    build_snapshot_index_record,
    query_governance_reconciliation,
    query_governance_trace,
    query_snapshot_index,
    status_summary,
    traceability_drift_summary,
)
from scorpion.historian import (
    append_drift_record,
    build_drift_index_record,
    query_drift_window,
    read_drift_index,
)
from scorpion.invariants.evaluators import evaluate_all, load_invariant_catalog
from scorpion.ledger import (
    AnomalyClaimRecord,
    append_claim_record,
    build_claim_record,
    ledger_summary,
)
from scorpion.reconstructor import build_reconstruction_plan
from scorpion.sentinel.registry import get_sentinel, list_sentinels


GateDecision = Literal["approve", "reject"]

ALLOWED_MODES = {
    "observe",
    "ingest",
    "scan",
    "judge",
    "extract",
    "reconstruct",
    "status",
    "report",
    "snapshot",
    "snapshot-index",
    "snapshot-query",
    "trace-query",
    "reconcile-query",
    "drift-window-query",
    "verify",
    "chaos-check",
    "bundle-export",
    "reconcile-artifacts",
    "apply",
}

_DEFAULT_SENTINEL = "fixture"


@dataclass(slots=True)
class ScorpionRequest:
    case_id: str
    goal: str = ""
    scope: str = "."
    trace_path: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JudgeResult:
    case_id: str
    decision: GateDecision
    reason: str
    reviewer: str
    invariant_id: str
    claim_label: ClaimLabel
    mode: str = "judge"

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class ScorpionError(ValueError):
    """Raised when a Scorpion request violates stage gate constraints."""


def _ingest_events(request: ScorpionRequest, *, sentinel_name: str) -> list[TraceEvent]:
    if not request.trace_path.strip():
        raise ScorpionError("trace-path is required for ingest/scan modes.")
    return get_sentinel(sentinel_name).ingest(request.trace_path)


def observe_request(request: ScorpionRequest, *, sentinel_name: str) -> dict[str, Any]:
    catalog = load_invariant_catalog()
    inv_ids = [str(i.get("id")) for i in catalog.get("invariants") or []]
    sentinel = get_sentinel(sentinel_name)
    sentinel_info: dict[str, Any] = {"adapter_id": sentinel.adapter_id, "sentinel": sentinel_name}
    if request.trace_path.strip():
        sentinel_info = sentinel.describe(request.trace_path)
        sentinel_info["sentinel"] = sentinel_name
    return {
        "mode": "observe",
        "case_id": request.case_id,
        "scope": request.scope,
        "goal": request.goal,
        "invariant_ids": inv_ids,
        "available_sentinels": list_sentinels(),
        "sentinel": sentinel_info,
        "claim_label": "proven",
        "safety_state": "dry_run_only",
    }


def ingest_request(request: ScorpionRequest, *, sentinel_name: str) -> dict[str, Any]:
    events = _ingest_events(request, sentinel_name=sentinel_name)
    return {
        "mode": "ingest",
        "case_id": request.case_id,
        "event_count": len(events),
        "events": [e.model_dump() for e in events],
        "claim_label": "proven",
        "safety_state": "dry_run_only",
    }


def scan_request(request: ScorpionRequest, *, sentinel_name: str) -> dict[str, Any]:
    events = _ingest_events(request, sentinel_name=sentinel_name)
    drifts = evaluate_all(events)
    scan_hash = hash_text(json_stable({"drifts": drifts, "count": len(events)}))
    claim: ClaimLabel = "proven" if drifts else "asserted"
    return {
        "mode": "scan",
        "case_id": request.case_id,
        "drift_count": len(drifts),
        "drifts": drifts,
        "scan_hash": scan_hash,
        "claim_label": claim,
        "safety_state": "dry_run_only",
    }


def judge_request(
    request: ScorpionRequest,
    *,
    decision: GateDecision,
    reason: str,
    reviewer: str,
    invariant_id: str,
    drift_summary: str,
    evidence_hash: str,
    allow_approve: bool,
) -> JudgeResult:
    if decision == "approve" and not allow_approve:
        raise ScorpionError("approve decision requires --allow-approve flag.")
    if decision == "approve" and not reviewer.strip():
        raise ScorpionError("approve decision requires reviewer identity.")
    claim: ClaimLabel = "rejected" if decision == "reject" else "asserted"
    if decision == "approve" and evidence_hash:
        claim = "proven"
    return JudgeResult(
        case_id=request.case_id,
        decision=decision,
        reason=reason or "no reason provided",
        reviewer=reviewer,
        invariant_id=invariant_id or "unknown",
        claim_label=claim,
    )


def build_ledger_record(result: JudgeResult, *, evidence_refs: list[str]) -> AnomalyClaimRecord:
    return build_claim_record(
        case_id=result.case_id,
        mode="judge",
        invariant_id=result.invariant_id,
        decision=result.decision,
        claim_label=result.claim_label,
        reviewer=result.reviewer,
        reason=result.reason,
        drift_summary=result.reason,
        evidence_hash=hash_text(result.reason),
        evidence_refs=evidence_refs,
    )


def extract_request(request: ScorpionRequest, *, sentinel_name: str) -> dict[str, Any]:
    events = _ingest_events(request, sentinel_name=sentinel_name)
    drifts = evaluate_all(events)
    return extract_anomaly_bundle(
        case_id=request.case_id,
        drifts=drifts,
        events=[e.model_dump() for e in events],
    )


def reconstruct_request(request: ScorpionRequest, *, sentinel_name: str) -> dict[str, Any]:
    events = _ingest_events(request, sentinel_name=sentinel_name)
    drifts = evaluate_all(events)
    plan = build_reconstruction_plan(case_id=request.case_id, drifts=drifts)
    payload = plan.model_dump()
    payload["mode"] = "reconstruct"
    return payload


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
            payload = json.loads(scan_path.read_text(encoding="utf-8"))
            scan_claim = "proven" if int(payload.get("drift_count") or 0) > 0 else "asserted"
            scan_hash = sha256_file(scan_path)
        except (OSError, json.JSONDecodeError):
            scan_claim = "rejected"
    ledger_info = ledger_summary(ledger_path)
    ledger_claim: ClaimLabel = "proven" if ledger_info["entries"] > 0 else ("asserted" if ledger_info["exists"] else "rejected")
    overall = derive_claim_status([scan_claim, ledger_claim])
    return {
        "report_version": "scorpion.proof_report.v1",
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
        "snapshot_version": "scorpion.snapshot.v1",
        "snapshot_id": f"scsnap-{seed[:16]}",
        "case_id": case_id,
        "created_at_utc": created_at,
        "claim_label": report_claim,
        "linkage": {"report_hash": report_hash, "ledger_hash": ledger_hash},
        "safety_state": "dry_run_only",
    }


def build_verification_report(
    *,
    case_id: str,
    proof_dir: Path,
    ledger_path: Path,
    fixed_timestamp: str | None = None,
) -> dict[str, Any]:
    report_path = proof_dir / "scorpion_report.json"
    snapshot_path = proof_dir / "scorpion_snapshot.json"
    index_path = proof_dir / "scorpion_snapshot_index.jsonl"
    drift_path = proof_dir / "health_drift_index.jsonl"
    trace = query_governance_trace(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
    )
    replay_env = os.environ.get("SCORPION_REPLAY_ENV", "").strip().lower()
    cross_status = "active" if replay_env == "active" else "inactive"
    artifact_sync: ClaimLabel = "proven"
    if not report_path.exists() or not snapshot_path.exists():
        artifact_sync = "rejected"
    overall = derive_claim_status([str(trace.get("claim_label") or "asserted"), artifact_sync])
    return {
        "report_version": "scorpion.verify_report.v1",
        "generated_at_utc": fixed_timestamp or datetime.now(UTC).isoformat(),
        "case_id": case_id,
        "claim_label": overall,
        "artifact_sync_claim_label": artifact_sync,
        "trace_summary": trace,
        "cross_machine_replay": {"operational_status": cross_status},
        "paths": {
            "report": str(report_path),
            "snapshot": str(snapshot_path),
            "snapshot_index": str(index_path),
            "health_drift_index": str(drift_path),
        },
    }


def run_chaos_checks() -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []

    def _missing_ledger(root: Path) -> dict[str, Any]:
        trace = query_governance_trace(
            ledger_path=root / "missing.jsonl",
            report_path=root / "report.json",
            snapshot_path=root / "snap.json",
        )
        actual = str(trace.get("claim_label") or "")
        return {"scenario_id": "missing_ledger", "expected_claim_label": "rejected", "actual_claim_label": actual, "passed": actual == "rejected"}

    def _corrupt_report(root: Path) -> dict[str, Any]:
        (root / "ledger.jsonl").write_text(
            json.dumps({"record_id": "x", "claim_label": "proven"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (root / "report.json").write_text("{bad", encoding="utf-8")
        (root / "snap.json").write_text("{}", encoding="utf-8")
        trace = query_governance_trace(
            ledger_path=root / "ledger.jsonl",
            report_path=root / "report.json",
            snapshot_path=root / "snap.json",
        )
        report_claim = str((trace.get("report") or {}).get("claim_label") or "")
        return {
            "scenario_id": "corrupt_report",
            "expected_claim_label": "rejected",
            "actual_claim_label": report_claim,
            "passed": report_claim == "rejected",
        }

    def _hash_drift(root: Path) -> dict[str, Any]:
        ledger = root / "ledger.jsonl"
        ledger.write_text(
            json.dumps({"record_id": "r1", "claim_label": "proven"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (root / "report.json").write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
        (root / "snap.json").write_text(
            json.dumps({"claim_label": "proven", "linkage": {"report_hash": "dead", "ledger_hash": "beef"}}, sort_keys=True),
            encoding="utf-8",
        )
        drift = traceability_drift_summary(ledger_path=ledger, report_path=root / "report.json", snapshot_path=root / "snap.json")
        actual = str(drift.get("claim_label") or "")
        return {
            "scenario_id": "hash_drift",
            "expected_claim_label": "rejected",
            "actual_claim_label": actual,
            "passed": actual == "rejected" and bool(drift.get("drift_detected")),
        }

    with tempfile.TemporaryDirectory(prefix="scorpion-chaos-") as temp_dir:
        root = Path(temp_dir)
        for runner in (_missing_ledger, _corrupt_report, _hash_drift):
            scenarios.append(runner(root))
    passed = sum(1 for s in scenarios if s.get("passed"))
    total = len(scenarios)
    if passed == total:
        claim: ClaimLabel = "proven"
    elif passed == 0:
        claim = "rejected"
    else:
        claim = "asserted"
    return {
        "mode": "chaos-check",
        "claim_label": claim,
        "safety_state": "dry_run_only",
        "scenarios_run": total,
        "scenarios_passed": passed,
        "results": scenarios,
    }


def run_reconcile_artifacts(
    *,
    request: ScorpionRequest,
    proof_dir: Path,
    ledger_path: Path,
    fixed_timestamp: str | None,
    sentinel_name: str = _DEFAULT_SENTINEL,
) -> dict[str, Any]:
    trace_path = Path(request.trace_path) if request.trace_path else None
    scan_payload: dict[str, Any] = {"mode": "scan", "case_id": request.case_id, "drift_count": 0, "claim_label": "asserted"}
    if trace_path and trace_path.exists():
        scan_payload = scan_request(request, sentinel_name=sentinel_name)
    scan_file = proof_dir / "scorpion_scan.json"
    scan_file.write_text(json_stable(scan_payload, pretty=True), encoding="utf-8")
    report = build_proof_report(
        case_id=request.case_id,
        scan_path=scan_file,
        ledger_path=ledger_path,
        generated_at_utc=fixed_timestamp,
    )
    report_path = proof_dir / "scorpion_report.json"
    report_path.write_text(json_stable(report, pretty=True), encoding="utf-8")
    snapshot = build_snapshot(
        case_id=request.case_id,
        report_path=report_path,
        ledger_path=ledger_path,
        created_at_utc=fixed_timestamp,
    )
    snapshot_path = proof_dir / "scorpion_snapshot.json"
    snapshot_path.write_text(json_stable(snapshot, pretty=True), encoding="utf-8")
    index_path = proof_dir / "scorpion_snapshot_index.jsonl"
    previous = query_snapshot_index(index_path, limit=1).get("entries") or []
    prev_entry = previous[-1] if previous else None
    index_record = build_snapshot_index_record(
        snapshot_path=snapshot_path,
        report_path=report_path,
        ledger_path=ledger_path,
        case_id=request.case_id,
        previous_entry=prev_entry if isinstance(prev_entry, dict) else None,
        created_at_utc=fixed_timestamp,
    )
    append_snapshot_index_record(index_record, index_path)
    post = traceability_drift_summary(ledger_path=ledger_path, report_path=report_path, snapshot_path=snapshot_path)
    return {
        "mode": "reconcile-artifacts",
        "claim_label": "proven" if not post.get("drift_detected") else "rejected",
        "post_reconcile": {"drift_count": 1 if post.get("drift_detected") else 0, "drift": post},
    }


def _emit(payload: dict[str, Any], output: str) -> None:
    if output == "text":
        for key, value in payload.items():
            print(f"{key}: {value}")
    else:
        print(json_stable(payload, pretty=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scorpion governed OS anomaly extractor.")
    parser.add_argument("--mode", choices=sorted(ALLOWED_MODES), default="observe")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--scope", default=".")
    parser.add_argument("--trace-path", default="")
    parser.add_argument("--decision", choices=["approve", "reject"], default="reject")
    parser.add_argument("--reason", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--invariant-id", default="")
    parser.add_argument("--allow-approve", action="store_true")
    parser.add_argument("--allow-apply", action="store_true")
    parser.add_argument("--output", choices=["json", "text"], default="json")
    parser.add_argument("--ledger-path", default=".runtime/scorpion/anomaly_ledger.jsonl")
    parser.add_argument("--proof-dir", default="docs/proof/scorpion")
    parser.add_argument("--drift-index-path", default="docs/proof/scorpion/health_drift_index.jsonl")
    parser.add_argument("--fixed-timestamp", default="")
    parser.add_argument("--write-report", default="")
    parser.add_argument("--write-plan", default="")
    parser.add_argument("--write-verify-report", default="")
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--query-claim", default="asserted")
    parser.add_argument(
        "--sentinel",
        default=_DEFAULT_SENTINEL,
        choices=list_sentinels(),
        help="trace adapter: fixture, audit, or kernel (stub/ndjson bridge)",
    )
    parser.add_argument("--snapshot-id", default="", help="snapshot-query filter")
    parser.add_argument("--write-bundle-export", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    mode = str(args.mode)
    if mode == "apply" or args.allow_apply:
        raise ScorpionError("apply mode is disabled in stages 1-4; dry-run only.")
    sentinel_name = str(args.sentinel)
    if mode not in ALLOWED_MODES:
        raise ScorpionError(f"unsupported mode: {mode}")

    request = ScorpionRequest(
        case_id=str(args.case_id),
        goal=str(args.goal),
        scope=str(args.scope),
        trace_path=str(args.trace_path),
    )
    ledger_path = Path(str(args.ledger_path))
    proof_dir = Path(str(args.proof_dir))
    fixed_ts = str(args.fixed_timestamp).strip() or None

    try:
        if mode == "observe":
            _emit(observe_request(request, sentinel_name=sentinel_name), str(args.output))
        elif mode == "ingest":
            _emit(ingest_request(request, sentinel_name=sentinel_name), str(args.output))
        elif mode == "scan":
            payload = scan_request(request, sentinel_name=sentinel_name)
            _emit(payload, str(args.output))
            if request.trace_path:
                prev = read_drift_index(Path(str(args.drift_index_path)))
                record = build_drift_index_record(
                    case_id=request.case_id,
                    drift_count=int(payload.get("drift_count") or 0),
                    claim_label=str(payload.get("claim_label") or "asserted"),  # type: ignore[arg-type]
                    scan_hash=str(payload.get("scan_hash") or ""),
                    previous=prev[-1] if prev else None,
                    created_at_utc=fixed_ts,
                )
                append_drift_record(record, Path(str(args.drift_index_path)))
        elif mode == "judge":
            result = judge_request(
                request,
                decision=str(args.decision),  # type: ignore[arg-type]
                reason=str(args.reason),
                reviewer=str(args.reviewer),
                invariant_id=str(args.invariant_id),
                drift_summary=str(args.reason),
                evidence_hash=hash_text(str(args.reason)),
                allow_approve=bool(args.allow_approve),
            )
            record = build_ledger_record(result, evidence_refs=[str(args.proof_dir)])
            append_claim_record(record, ledger_path)
            _emit({"mode": "judge", "result": result.model_dump(), "record": record.model_dump()}, str(args.output))
        elif mode == "extract":
            _emit(extract_request(request, sentinel_name=sentinel_name), str(args.output))
        elif mode == "reconstruct":
            payload = reconstruct_request(request, sentinel_name=sentinel_name)
            _emit(payload, str(args.output))
            if str(args.write_plan).strip():
                Path(str(args.write_plan)).write_text(json_stable(payload, pretty=True), encoding="utf-8")
        elif mode == "status":
            _emit(
                status_summary(case_id=request.case_id, proof_dir=proof_dir, ledger_path=ledger_path),
                str(args.output),
            )
        elif mode == "report":
            scan_path = proof_dir / "scorpion_scan.json"
            report = build_proof_report(case_id=request.case_id, scan_path=scan_path, ledger_path=ledger_path, generated_at_utc=fixed_ts)
            out = str(args.write_report).strip() or str(proof_dir / "scorpion_report.json")
            Path(out).write_text(json_stable(report, pretty=True), encoding="utf-8")
            _emit(report, str(args.output))
        elif mode == "snapshot":
            report_path = proof_dir / "scorpion_report.json"
            snap = build_snapshot(case_id=request.case_id, report_path=report_path, ledger_path=ledger_path, created_at_utc=fixed_ts)
            out = proof_dir / "scorpion_snapshot.json"
            out.write_text(json_stable(snap, pretty=True), encoding="utf-8")
            _emit(snap, str(args.output))
        elif mode == "snapshot-index":
            snap_path = proof_dir / "scorpion_snapshot.json"
            report_path = proof_dir / "scorpion_report.json"
            index_path = proof_dir / "scorpion_snapshot_index.jsonl"
            previous = query_snapshot_index(index_path, limit=1).get("entries") or []
            prev_entry = previous[-1] if previous else None
            record = build_snapshot_index_record(
                snapshot_path=snap_path,
                report_path=report_path,
                ledger_path=ledger_path,
                case_id=request.case_id,
                previous_entry=prev_entry if isinstance(prev_entry, dict) else None,
                created_at_utc=fixed_ts,
            )
            append_snapshot_index_record(record, index_path)
            _emit(record, str(args.output))
        elif mode == "snapshot-query":
            _emit(
                query_snapshot_index(
                    proof_dir / "scorpion_snapshot_index.jsonl",
                    snapshot_id=str(args.snapshot_id),
                    case_id=request.case_id,
                    limit=int(args.window),
                ),
                str(args.output),
            )
        elif mode == "trace-query":
            _emit(
                query_governance_trace(
                    ledger_path=ledger_path,
                    report_path=proof_dir / "scorpion_report.json",
                    snapshot_path=proof_dir / "scorpion_snapshot.json",
                ),
                str(args.output),
            )
        elif mode == "reconcile-query":
            _emit(
                query_governance_reconciliation(
                    ledger_path=ledger_path,
                    report_path=proof_dir / "scorpion_report.json",
                    snapshot_path=proof_dir / "scorpion_snapshot.json",
                ),
                str(args.output),
            )
        elif mode == "drift-window-query":
            _emit(query_drift_window(Path(str(args.drift_index_path)), window=int(args.window)), str(args.output))
        elif mode == "chaos-check":
            _emit(run_chaos_checks(), str(args.output))
        elif mode == "verify":
            report = build_verification_report(
                case_id=request.case_id,
                proof_dir=proof_dir,
                ledger_path=ledger_path,
                fixed_timestamp=fixed_ts,
            )
            out = str(args.write_verify_report).strip()
            if out:
                Path(out).write_text(json_stable(report, pretty=True), encoding="utf-8")
            _emit(report, str(args.output))
        elif mode == "bundle-export":
            verify_path = proof_dir / "scorpion_verify_report.json"
            if verify_path.exists():
                verify_payload = json.loads(verify_path.read_text(encoding="utf-8"))
            else:
                verify_payload = build_verification_report(
                    case_id=request.case_id,
                    proof_dir=proof_dir,
                    ledger_path=ledger_path,
                    fixed_timestamp=fixed_ts,
                )
            chaos = run_chaos_checks()
            manifest = {
                "manifest_version": "scorpion.bundle_export.v1",
                "case_id": request.case_id,
                "claim_label": str(verify_payload.get("claim_label") or "asserted"),
                "chaos_summary": chaos,
                "verify_summary": verify_payload,
            }
            out_bundle = str(args.write_bundle_export).strip()
            if out_bundle:
                Path(out_bundle).write_text(json_stable(manifest, pretty=True), encoding="utf-8")
            _emit(manifest, str(args.output))
        elif mode == "reconcile-artifacts":
            _emit(
                run_reconcile_artifacts(
                    request=request,
                    proof_dir=proof_dir,
                    ledger_path=ledger_path,
                    fixed_timestamp=fixed_ts,
                    sentinel_name=sentinel_name,
                ),
                str(args.output),
            )
        else:
            raise ScorpionError(f"mode not implemented: {mode}")
        return 0
    except ScorpionError as exc:
        print(f"scorpion_error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
