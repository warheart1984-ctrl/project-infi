#!/usr/bin/env python3
"""Read-only AI Mechanic governance gate for CI."""

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


def _pipeline(
    *,
    python: str,
    repo_root: Path,
    case_id: str,
    fixture: Path,
    runtime: Path,
    ledger: Path,
    drift_index: Path,
    trace_path: str = "",
) -> tuple[bool, str]:
    for mode in ("scan", "diagnose", "rebuild"):
        cmd = [
            python,
            "-m",
            "mechanic.mechanic",
            "--mode",
            mode,
            "--case-id",
            case_id,
            "--repo-path",
            str(fixture),
            "--runtime-dir",
            str(runtime),
            "--ledger-path",
            str(ledger),
            "--drift-index",
            str(drift_index),
            "--write-json",
        ]
        if trace_path and mode == "scan":
            cmd.extend(["--trace-path", trace_path])
        code, output = _run(cmd, cwd=repo_root)
        if code != 0:
            return False, f"{mode} failed:\n{output}"

    case_dir = runtime / case_id
    scan_path = case_dir / "mechanic_scan.v1.json"
    if not scan_path.exists():
        return False, "mechanic_scan missing"
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    if int(scan.get("drift_count") or 0) < 1:
        return False, "expected drifts on fixture"
    for artifact in (
        "target_workflow.v1.json",
        "patch_plan.v1.json",
        "MECHANIC_RUNTIME_PROFILE.json",
        "reconstruction_plan.v1.json",
    ):
        if not (case_dir / artifact).exists():
            return False, f"missing {artifact}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Mechanic read-only governance gate.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--case-id", default="mechanic-ci-gate")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    python = str(args.python)
    case_id = str(args.case_id)
    fixture_v1 = repo_root / "mechanic" / "fixtures" / "sample-customer-repo"
    fixture_v2 = repo_root / "mechanic" / "fixtures" / "sample-customer-repo-v2"
    sample_trace = repo_root / "mechanic" / "fixtures" / "traces" / "sample_trace.ndjson"

    print("[mechanic-gate] running pytest tests.test_mechanic tests.test_mechanic_chat_hook")
    code, output = _run(
        [python, "-m", "pytest", "tests/test_mechanic.py", "tests/test_mechanic_chat_hook.py", "-q"],
        cwd=repo_root,
    )
    if code != 0:
        print(output)
        print("[mechanic-gate] FAIL: mechanic tests failed")
        return 1

    print("[mechanic-gate] running chaos-check")
    code, output = _run(
        [python, "-m", "mechanic.mechanic", "--mode", "chaos-check", "--case-id", case_id],
        cwd=repo_root,
    )
    if code != 0:
        print(output)
        return 1
    chaos = json.loads(output)
    if str(chaos.get("claim_label")) != "proven":
        print("[mechanic-gate] FAIL: chaos-check not proven")
        return 1

    with tempfile.TemporaryDirectory(prefix="mechanic-ci-") as temp_dir:
        runtime = Path(temp_dir) / "runtime"
        ledger = Path(temp_dir) / "ledger.jsonl"
        drift_index = Path(temp_dir) / "drift.jsonl"

        print("[mechanic-gate] v1 fixture pipeline")
        ok, msg = _pipeline(
            python=python,
            repo_root=repo_root,
            case_id=case_id,
            fixture=fixture_v1,
            runtime=runtime,
            ledger=ledger,
            drift_index=drift_index,
            trace_path=str(sample_trace),
        )
        if not ok:
            print(msg)
            print("[mechanic-gate] FAIL: v1 pipeline")
            return 1

        print("[mechanic-gate] v2 fixture pipeline")
        ok, msg = _pipeline(
            python=python,
            repo_root=repo_root,
            case_id=f"{case_id}-v2",
            fixture=fixture_v2,
            runtime=runtime,
            ledger=ledger,
            drift_index=drift_index,
        )
        if not ok:
            print(msg)
            print("[mechanic-gate] FAIL: v2 pipeline")
            return 1
        v2_scan = json.loads((runtime / f"{case_id}-v2" / "mechanic_scan.v1.json").read_text(encoding="utf-8"))
        v2_codes = {str(d.get("code")) for d in v2_scan.get("drifts") or []}
        if not v2_codes & {"GOV-20", "RNT-04", "RNT-15", "HUM-05"}:
            print(f"[mechanic-gate] FAIL: v2 expected distinct codes, got {sorted(v2_codes)}")
            return 1

        print("[mechanic-gate] report mode smoke")
        code, output = _run(
            [
                python,
                "-m",
                "mechanic.mechanic",
                "--mode",
                "report",
                "--case-id",
                case_id,
                "--runtime-dir",
                str(runtime),
                "--write-json",
            ],
            cwd=repo_root,
        )
        if code != 0:
            print(output)
            print("[mechanic-gate] FAIL: report mode")
            return 1
        if not (runtime / case_id / "report.md").is_file():
            print("[mechanic-gate] FAIL: report.md missing")
            return 1

        print("[mechanic-gate] apply-review smoke")
        code, output = _run(
            [
                python,
                "-m",
                "mechanic.mechanic",
                "--mode",
                "apply-review",
                "--case-id",
                case_id,
                "--runtime-dir",
                str(runtime),
                "--create-review",
                "--write-json",
            ],
            cwd=repo_root,
        )
        if code != 0:
            print(output)
            print("[mechanic-gate] FAIL: apply-review")
            return 1

        code, output = _run(
            [
                python,
                "-m",
                "mechanic.mechanic",
                "--mode",
                "apply",
                "--case-id",
                case_id,
            ],
            cwd=repo_root,
        )
        if code == 0:
            print("[mechanic-gate] FAIL: apply must be blocked")
            return 1

    print("[mechanic-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
