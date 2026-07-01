#!/usr/bin/env python3
"""Read-only Forgekeeper governance gate for CI (tests, verify export, chaos-check)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Forgekeeper read-only governance gate.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="repository root (default: current directory)",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="python executable for forgekeeper invocations",
    )
    parser.add_argument(
        "--plan-id",
        default="bf-ci-gate",
        help="plan id used for verify/chaos invocations",
    )
    parser.add_argument(
        "--fixed-timestamp",
        default="2026-05-28T12:00:00Z",
        help="fixed UTC timestamp for deterministic verify export",
    )
    parser.add_argument(
        "--strict-verify-claim",
        action="store_true",
        default=True,
        help="fail when verify artifact sync is rejected (default: enabled)",
    )
    parser.add_argument(
        "--no-strict-verify-claim",
        action="store_false",
        dest="strict_verify_claim",
        help="allow verify artifact sync rejected with warning only",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    python = str(args.python)
    plan_id = str(args.plan_id)
    fixed_ts = str(args.fixed_timestamp)

    print("[forgekeeper-gate] running unittest tests.test_forgekeeper")
    code, output = _run([python, "-m", "unittest", "tests.test_forgekeeper", "-v"], cwd=repo_root)
    if code != 0:
        print(output)
        print("[forgekeeper-gate] FAIL: forgekeeper tests failed")
        return 1

    print("[forgekeeper-gate] running chaos-check")
    code, output = _run(
        [python, "-m", "forge.forgekeeper", "--mode", "chaos-check", "--plan-id", plan_id, "--scope", "."],
        cwd=repo_root,
    )
    if code != 0:
        print(output)
        print("[forgekeeper-gate] FAIL: chaos-check command failed")
        return 1
    try:
        chaos_payload = json.loads(output)
    except json.JSONDecodeError:
        chaos_payload = {}
    if str(chaos_payload.get("claim_label") or "") != "proven":
        print(output)
        print("[forgekeeper-gate] FAIL: chaos-check claim_label is not proven")
        return 1

    print("[forgekeeper-gate] running reconcile-artifacts (refresh linkage after tests)")
    code, output = _run(
        [
            python,
            "-m",
            "forge.forgekeeper",
            "--mode",
            "reconcile-artifacts",
            "--plan-id",
            plan_id,
            "--scope",
            ".",
            "--fixed-timestamp",
            fixed_ts,
            "--proof-dir",
            "docs/proof/bumblebee-forge",
            "--plan-artifact",
            "docs/proof/bumblebee-forge/stage2_attested_plan.json",
            "--ledger-path",
            ".runtime/forgekeeper/decision_ledger.jsonl",
            "--report-path",
            "docs/proof/bumblebee-forge/forgekeeper_report.json",
            "--snapshot-path",
            "docs/proof/bumblebee-forge/forgekeeper_snapshot.json",
            "--snapshot-index-path",
            "docs/proof/bumblebee-forge/forgekeeper_snapshot_index.jsonl",
        ],
        cwd=repo_root,
    )
    if code != 0:
        print(output)
        print("[forgekeeper-gate] FAIL: reconcile-artifacts command failed")
        return 1
    try:
        reconcile_payload = json.loads(output)
    except json.JSONDecodeError:
        reconcile_payload = {}
    post = reconcile_payload.get("post_reconcile") or {}
    drift_count = post.get("drift_count")
    if drift_count is None or int(drift_count) != 0:
        print(output)
        print("[forgekeeper-gate] FAIL: reconcile-artifacts left artifact drift")
        return 1

    with tempfile.TemporaryDirectory(prefix="forgekeeper-ci-") as temp_dir:
        verify_path = Path(temp_dir) / "forgekeeper_verify_report.json"
        print("[forgekeeper-gate] running verify --write-report")
        code, output = _run(
            [
                python,
                "-m",
                "forge.forgekeeper",
                "--mode",
                "verify",
                "--plan-id",
                plan_id,
                "--scope",
                ".",
                "--fixed-timestamp",
                fixed_ts,
                "--write-report",
                str(verify_path),
            ],
            cwd=repo_root,
        )
        if code != 0:
            print(output)
            print("[forgekeeper-gate] FAIL: verify command failed")
            return 1
        if not verify_path.exists():
            print("[forgekeeper-gate] FAIL: verify report was not written")
            return 1
        verify_payload = json.loads(verify_path.read_text(encoding="utf-8"))
        verify_claim = str(verify_payload.get("claim_label") or "asserted")
        cross_machine = verify_payload.get("cross_machine_replay") or {}
        if str(cross_machine.get("operational_status") or "") != "inactive":
            print("[forgekeeper-gate] FAIL: cross-machine replay must remain inactive in CI")
            return 1
        artifact_sync = str(verify_payload.get("artifact_sync_claim_label") or verify_claim)
        if artifact_sync == "rejected" and args.strict_verify_claim:
            print(output)
            print("[forgekeeper-gate] FAIL: verify artifact sync rejected under --strict-verify-claim")
            return 1
        if artifact_sync == "rejected":
            print("[forgekeeper-gate] WARN: verify artifact sync rejected; gate continues")
        elif verify_claim == "rejected":
            print("[forgekeeper-gate] NOTE: verify overall rejected but artifact sync ok (claim trend only)")

        bundle_path = Path(temp_dir) / "forgekeeper_bundle_manifest.json"
        print("[forgekeeper-gate] running bundle-export")
        code, output = _run(
            [
                python,
                "-m",
                "forge.forgekeeper",
                "--mode",
                "bundle-export",
                "--plan-id",
                plan_id,
                "--scope",
                ".",
                "--fixed-timestamp",
                fixed_ts,
                "--verify-report-path",
                str(verify_path),
                "--write-bundle-export",
                str(bundle_path),
            ],
            cwd=repo_root,
        )
        if code != 0 or not bundle_path.exists():
            print(output)
            print("[forgekeeper-gate] FAIL: bundle-export failed")
            return 1
        bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
        if str(bundle_payload.get("chaos_summary", {}).get("claim_label") or "") != "proven":
            print("[forgekeeper-gate] FAIL: bundle chaos_summary is not proven")
            return 1

    print("[forgekeeper-gate] OK: tests, chaos-check, verify export, bundle-export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
