#!/usr/bin/env python3
"""Read-only Scorpion governance gate for CI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str]:
    completed = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scorpion read-only governance gate.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--case-id", default="sc-ci-gate")
    parser.add_argument("--fixed-timestamp", default="2026-05-29T12:00:00Z")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    python = str(args.python)
    case_id = str(args.case_id)
    fixed_ts = str(args.fixed_timestamp)
    trace = repo_root / "scorpion" / "fixtures" / "traces" / "fd_leak.ndjson"

    print("[scorpion-gate] running unittest tests.test_scorpion")
    code, output = _run([python, "-m", "unittest", "tests.test_scorpion", "-v"], cwd=repo_root)
    if code != 0:
        print(output)
        print("[scorpion-gate] FAIL: scorpion tests failed")
        return 1

    print("[scorpion-gate] running chaos-check")
    code, output = _run(
        [python, "-m", "scorpion.scorpion", "--mode", "chaos-check", "--case-id", case_id],
        cwd=repo_root,
    )
    if code != 0:
        print(output)
        return 1
    chaos = json.loads(output)
    if str(chaos.get("claim_label")) != "proven":
        print("[scorpion-gate] FAIL: chaos-check not proven")
        return 1

    print("[scorpion-gate] running reconcile-artifacts")
    code, output = _run(
        [
            python,
            "-m",
            "scorpion.scorpion",
            "--mode",
            "reconcile-artifacts",
            "--case-id",
            case_id,
            "--trace-path",
            str(trace),
            "--fixed-timestamp",
            fixed_ts,
            "--proof-dir",
            "docs/proof/scorpion",
            "--ledger-path",
            ".runtime/scorpion/anomaly_ledger.jsonl",
        ],
        cwd=repo_root,
    )
    if code != 0:
        print(output)
        return 1
    reconcile = json.loads(output)
    if int((reconcile.get("post_reconcile") or {}).get("drift_count") or 0) != 0:
        print("[scorpion-gate] FAIL: reconcile left drift")
        return 1

    with tempfile.TemporaryDirectory(prefix="scorpion-ci-") as temp_dir:
        verify_path = Path(temp_dir) / "scorpion_verify_report.json"
        code, output = _run(
            [
                python,
                "-m",
                "scorpion.scorpion",
                "--mode",
                "verify",
                "--case-id",
                case_id,
                "--fixed-timestamp",
                fixed_ts,
                "--write-verify-report",
                str(verify_path),
            ],
            cwd=repo_root,
        )
        if code != 0 or not verify_path.exists():
            print(output)
            return 1
        verify = json.loads(verify_path.read_text(encoding="utf-8"))
        if str((verify.get("cross_machine_replay") or {}).get("operational_status")) != "inactive":
            print("[scorpion-gate] FAIL: cross-machine must be inactive")
            return 1

        code, output = _run(
            [
                python,
                "-m",
                "scorpion.scorpion",
                "--mode",
                "bundle-export",
                "--case-id",
                case_id,
                "--fixed-timestamp",
                fixed_ts,
            ],
            cwd=repo_root,
        )
        if code != 0:
            print(output)
            return 1
        bundle = json.loads(output)
        if str((bundle.get("chaos_summary") or {}).get("claim_label")) != "proven":
            print("[scorpion-gate] FAIL: bundle chaos_summary not proven")
            return 1

    print("[scorpion-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
