#!/usr/bin/env python3
"""Forge platform-tier gate (P9 superset of shippable gate)."""
from __future__ import annotations

import argparse
import json
import re
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
    parser = argparse.ArgumentParser(description="Check Forge platform-tier readiness.")
    parser.add_argument("--output", default="ci-artifacts/forge-platform-gate-report.json")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument(
        "--skip-shippable",
        action="store_true",
        help="Skip embedded shippable gate (for incremental debugging).",
    )
    return parser.parse_args()


def _run(command: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, check=False, timeout=300)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    tail = output.splitlines()[-3:] if output else []
    return proc.returncode, "\n".join(tail)


def _meta_architect_decision(repo_root: Path) -> str:
    gate_doc = repo_root / "docs/forge-platform-gate.md"
    if not gate_doc.is_file():
        return "pending"
    text = gate_doc.read_text(encoding="utf-8")
    if re.search(r"\|\s*Decision\s*\|\s*\*\*APPROVE\*\*", text, re.IGNORECASE):
        return "approve"
    if re.search(r"\|\s*Decision\s*\|\s*APPROVE\b", text, re.IGNORECASE):
        return "approve"
    return "pending"


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    checks: list[GateCheck] = []
    if not args.skip_shippable:
        checks.append(
            GateCheck(
                "P",
                "Shippable gate baseline",
                [sys.executable, ".github/scripts/check-forge-shippable-gate.py", "--mode", args.mode],
            )
        )
    checks.extend(
        [
            GateCheck("P7", "Pipeline specs v2", [sys.executable, "wolf-cog-os/scripts/validate-pipeline.py", "--all", "--mode", "fail"]),
            GateCheck(
                "P7",
                "Lineage contract tests",
                [sys.executable, "-m", "unittest", "tests.test_forge_lineage"],
            ),
            GateCheck(
                "P7",
                "Nightly lineage emit+validate",
                [
                    sys.executable,
                    "wolf-cog-os/scripts/emit-forge-lineage.py",
                    "--pipeline",
                    "wolf-cog-os/forge/pipelines/daily-driver.yaml",
                    "--output",
                    "ci-artifacts/platform-gate-forge-lineage.json",
                ],
            ),
            GateCheck(
                "P7",
                "Lineage artifact validation",
                [
                    sys.executable,
                    "wolf-cog-os/scripts/validate-forge-lineage.py",
                    "--lineage",
                    "ci-artifacts/platform-gate-forge-lineage.json",
                    "--mode",
                    "fail",
                ],
            ),
            GateCheck(
                "P8",
                "Arch matrix registry",
                [sys.executable, "wolf-cog-os/scripts/validate-arch-matrix.py", "--mode", "fail"],
            ),
            GateCheck(
                "P8",
                "Cloud output registry",
                [
                    sys.executable,
                    "wolf-cog-os/scripts/validate-cloud-output.py",
                    "--format",
                    "raw-img",
                    "--registry-only",
                    "--mode",
                    "fail",
                ],
            ),
            GateCheck(
                "P8",
                "Platform output tests",
                [sys.executable, "-m", "unittest", "tests.test_arch_matrix", "tests.test_cloud_output"],
            ),
            GateCheck(
                "P9",
                "Substrate evolution ledger",
                [sys.executable, ".github/scripts/validate-substrate-evolution-ledger.py", "--mode", "fail"],
            ),
            GateCheck(
                "P9",
                "Backend evolution ledger",
                [sys.executable, ".github/scripts/validate-backend-evolution-ledger.py", "--mode", "fail"],
            ),
            GateCheck(
                "P9",
                "Nightly evolution ledger",
                [sys.executable, ".github/scripts/validate-nightly-evolution-ledger.py", "--mode", "fail"],
            ),
            GateCheck(
                "P9",
                "Nightly evolution dry-run",
                ["bash", "wolf-cog-os/scripts/test/forge-nightly-evolution.sh", "--dry-run"],
            ),
            GateCheck(
                "P9",
                "Platform dashboard",
                [sys.executable, "-m", "unittest", "tests.test_forge_platform_dashboard"],
            ),
            GateCheck(
                "P10",
                "Replay adapter registry",
                [sys.executable, "wolf-cog-os/scripts/validate-replay-adapter.py", "--mode", "fail"],
            ),
            GateCheck(
                "P10",
                "Replay adapter tests",
                [sys.executable, "-m", "unittest", "tests.test_replay_adapter"],
            ),
            GateCheck(
                "P11",
                "Pacstrap backend registry",
                [
                    sys.executable,
                    "wolf-cog-os/scripts/validate-rootfs-backend.py",
                    "--backend",
                    "pacstrap",
                    "--registry-only",
                    "--mode",
                    "fail",
                ],
            ),
            GateCheck(
                "P12",
                "Lineage reproducibility tests",
                [sys.executable, "-m", "unittest", "tests.test_lineage_reproducibility"],
            ),
            GateCheck(
                "P13",
                "Nightly variant matrix",
                [
                    sys.executable,
                    "-c",
                    "import json; json.load(open('wolf-cog-os/forge/nightly/variant-matrix.json'))",
                ],
            ),
            GateCheck(
                "P14",
                "Cloud output production modules",
                [sys.executable, "-m", "unittest", "tests.test_cloud_output"],
            ),
            GateCheck(
                "P14",
                "Pipeline run wiring tests",
                [sys.executable, "-m", "unittest", "tests.test_forge_pipeline_run"],
            ),
            GateCheck(
                "P15",
                "Universal substrate invariants",
                [sys.executable, "wolf-cog-os/scripts/validate-substrate-invariants.py", "--mode", "fail"],
            ),
            GateCheck(
                "P15",
                "Universal substrate tests",
                [sys.executable, "-m", "unittest", "tests.test_universal_substrate"],
            ),
        ]
    )

    rows: list[dict[str, object]] = []
    overall = "pass"
    blockers: list[str] = []

    for check in checks:
        code, tail = _run(check.command, repo_root)
        status = "pass" if code == 0 else "fail"
        if status == "fail" and check.required:
            overall = "fail"
            blockers.append(f"{check.gate_id}:{check.name}")
        rows.append(
            {
                "gate_id": check.gate_id,
                "name": check.name,
                "status": status,
                "required": check.required,
                "command": " ".join(check.command),
                "output_tail": tail.splitlines() if tail else [],
            }
        )

    meta_decision = _meta_architect_decision(repo_root)
    rows.append(
        {
            "gate_id": "G",
            "name": "Platform tier Meta Architect approval",
            "status": "pass" if meta_decision == "approve" else "pending",
            "required": False,
            "command": "docs/forge-platform-gate.md",
            "output_tail": [
                "Meta Architect APPROVE recorded."
                if meta_decision == "approve"
                else "Record APPROVE in docs/forge-platform-gate.md after live platform evidence."
            ],
        }
    )

    report = {
        "schema_version": "forge-platform-gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "status": overall if args.mode == "fail" or overall == "pass" else "warn",
        "checks": rows,
        "blockers": blockers,
        "meta_architect_gate": {
            "gate_id": "G",
            "decision_required": meta_decision != "approve",
            "decision": meta_decision,
            "authority": "Meta Architect",
            "notes": "Platform-tier release channel authorization.",
            "decision_doc": "docs/forge-platform-gate.md",
        },
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"forge platform gate: status={report['status']} output={output_path}")
    if blockers:
        print("blockers: " + ", ".join(blockers))
        return 1 if args.mode == "fail" else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
