#!/usr/bin/env python3
"""Evaluate Forge first-shippable milestone gate checks."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class GateCheck:
    gate_id: str
    name: str
    command: list[str]
    required: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Forge shippable milestone gate readiness.")
    parser.add_argument("--output", default="ci-artifacts/forge-shippable-gate-report.json")
    parser.add_argument(
        "--artifacts-dir",
        default="",
        help="Optional RC artifact directory for promotion readiness checks.",
    )
    parser.add_argument("--source-run-id", default="", help="Expected RC source run id when validating artifacts.")
    parser.add_argument("--expected-profile-id", default="forge-selfhosted")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    return parser.parse_args()


def _run(command: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def _meta_architect_decision(repo_root: Path) -> str:
    gate_doc = repo_root / "docs/forge-shippable-gate.md"
    if not gate_doc.is_file():
        return "pending"
    text = gate_doc.read_text(encoding="utf-8")
    if "**APPROVE**" in text and "| Decision | **APPROVE**" in text:
        return "approve"
    if "| Decision | APPROVE |" in text:
        return "approve"
    return "pending"


def _artifact_gate(repo_root: Path, artifacts_dir: Path, source_run_id: str, profile_id: str) -> tuple[str, str]:
    if not artifacts_dir.is_dir():
        return "fail", f"artifacts dir missing: {artifacts_dir}"

    required = [
        "build-metadata.json",
        "matrix-summary.json",
        "artifact-manifest.json",
        "state.json",
        "profile-attestation.json",
        "profile-validation.json",
        "forge-build-state.json",
        "forge-lineage.json",
    ]
    missing = [name for name in required if not (artifacts_dir / name).is_file()]
    iso_files = list(artifacts_dir.glob("*.iso"))
    sig_files = list(artifacts_dir.glob("*.minisig"))
    if missing:
        return "fail", "missing artifacts: " + ",".join(missing)
    if not iso_files:
        return "fail", "missing promotable ISO"
    if not sig_files:
        return "warn", "missing signature files (.minisig)"

    if not source_run_id:
        return "warn", "source_run_id not provided; skipped promotion identity validation"

    out = artifacts_dir / "promotion-source-validation.json"
    cmd = [
        sys.executable,
        str(repo_root / ".github/scripts/validate-promotion-source.py"),
        "--artifacts-dir",
        str(artifacts_dir),
        "--source-run-id",
        source_run_id,
        "--expected-profile-id",
        profile_id,
        "--required-scenarios",
        "1,3,4,6",
        "--output",
        str(out),
    ]
    code, output = _run(cmd, repo_root)
    if code != 0:
        return "fail", output or "promotion source validation failed"
    return "pass", output or "promotion source validation passed"


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    checks: list[GateCheck] = [
        GateCheck("B", "Governance ledger fail mode", [sys.executable, ".github/scripts/validate-governance-ledger.py", "--mode", "fail", "--summary-only"]),
        GateCheck("B", "Substrate evolution ledger", [sys.executable, ".github/scripts/validate-substrate-evolution-ledger.py", "--mode", "fail"]),
        GateCheck("B", "Rootfs backend registry", [sys.executable, "wolf-cog-os/scripts/validate-rootfs-backend.py", "--backend", "debootstrap", "--registry-only", "--mode", "fail"]),
        GateCheck("B", "Repo safety", [sys.executable, ".github/scripts/check-repo-safety.py", "--summary-only"]),
        GateCheck("C", "Forge ISO contract smoke", ["bash", "wolf-cog-os/scripts/test/forge-iso-smoke.sh"]),
        GateCheck("D", "Promotion dry-run fixture", ["bash", "wolf-cog-os/scripts/test/promotion-dry-run.sh", "--skip-verify"]),
        GateCheck("D", "Promotion source unit tests", [sys.executable, "-m", "unittest", "tests.test_validate_promotion_source"]),
        GateCheck("E", "Forge profile loader tests", ["bash", "wolf-cog-os/scripts/test/test-forge-profile-loader.sh"]),
        GateCheck("E", "Law tooling edge tests", [sys.executable, "-m", "unittest", "tests.test_law_tooling_edge_cases"]),
        GateCheck("E", "Substrate platform tests", [sys.executable, "-m", "unittest", "tests.test_validate_substrate", "tests.test_substrate_evolution_ledger"]),
        GateCheck("E", "Rootfs backend tests", [sys.executable, "-m", "unittest", "tests.test_rootfs_backend"]),
        GateCheck("E", "Forge platform dashboard", [sys.executable, "-m", "unittest", "tests.test_forge_platform_dashboard"]),
    ]

    gate_rows: list[dict[str, object]] = []
    overall = "pass"
    blockers: list[str] = []

    for check in checks:
        code, output = _run(check.command, repo_root)
        status = "pass" if code == 0 else "fail"
        if status == "fail" and check.required:
            overall = "fail"
            blockers.append(f"{check.gate_id}:{check.name}")
        gate_rows.append(
            {
                "gate_id": check.gate_id,
                "name": check.name,
                "status": status,
                "required": check.required,
                "command": " ".join(check.command),
                "output_tail": output.splitlines()[-3:] if output else [],
            }
        )

    artifact_status = "skipped"
    artifact_notes = "no artifacts dir provided"
    if args.artifacts_dir:
        artifact_status, artifact_notes = _artifact_gate(
            repo_root,
            repo_root / args.artifacts_dir,
            args.source_run_id.strip(),
            args.expected_profile_id.strip(),
        )
        gate_rows.append(
            {
                "gate_id": "F",
                "name": "RC artifact promotion readiness",
                "status": artifact_status,
                "required": False,
                "command": f"validate artifacts in {args.artifacts_dir}",
                "output_tail": artifact_notes.splitlines()[-3:] if artifact_notes else [],
            }
        )
        if artifact_status == "fail" and args.mode == "fail":
            overall = "fail"
            blockers.append("F:RC artifact promotion readiness")
    else:
        gate_rows.append(
            {
                "gate_id": "F",
                "name": "RC artifact promotion readiness",
                "status": "pending",
                "required": False,
                "command": "",
                "output_tail": ["Provide --artifacts-dir and --source-run-id after a green Forge RC run."],
            }
        )

    meta_decision = _meta_architect_decision(repo_root)
    meta_architect = {
        "gate_id": "F",
        "decision_required": meta_decision != "approve",
        "decision": meta_decision,
        "authority": "Meta Architect",
        "notes": "Explicit ship approval required after Gate F artifact evidence is green.",
        "decision_doc": "docs/forge-shippable-gate.md",
    }

    report = {
        "schema_version": "forge-shippable-gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "status": overall if args.mode == "fail" or overall == "pass" else "warn",
        "expected_profile_id": args.expected_profile_id,
        "checks": gate_rows,
        "blockers": blockers,
        "meta_architect_gate": meta_architect,
        "live_ci_evidence": {
            "p2_3_workflow_run_url": "",
            "p3_3_promotion_dry_run_url": "",
            "forge_rc_run_url": "",
            "status": "pending",
        },
    }

    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"forge shippable gate: status={report['status']} output={output_path}")
    if blockers:
        print("blockers: " + ", ".join(blockers))
        return 1 if args.mode == "fail" else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
