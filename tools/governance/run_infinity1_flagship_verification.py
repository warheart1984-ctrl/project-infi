#!/usr/bin/env python3
"""Infinity 1 full-systems flagship verification orchestrator."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Step:
    label: str
    command: list[str]


CORE_STEPS = [
    Step("governance-check", [sys.executable, ".github/scripts/validate-governance-ledger.py"]),
    Step("ssp-gate", [sys.executable, "tools/governance/check_ssp_completeness.py"]),
    Step("genome-gate", [sys.executable, "tools/governance/check_subsystem_genome.py"]),
    Step("alt4-gate", [sys.executable, "tools/governance/alt4_gate.py"]),
    Step("naming-gate", [sys.executable, "tools/naming_protocol_lint.py"]),
]

OPERATOR_WORKFLOW_STEPS = [
    Step("library-gate", [sys.executable, ".github/scripts/check-library-governance.py"]),
    Step(
        "workflow-family-gate",
        [sys.executable, ".github/scripts/check-workflow-family-governance.py"],
    ),
    Step(
        "brain-proposal-gate",
        [sys.executable, ".github/scripts/check-brain-proposal-governance.py"],
    ),
    Step("plug-adapter-gate", [sys.executable, ".github/scripts/check-plug-adapter-governance.py"]),
    Step("brain-layer-gate", [sys.executable, ".github/scripts/check-brain-layer-governance.py"]),
    Step(
        "operator-decision-ledger-gate",
        [sys.executable, ".github/scripts/check-operator-decision-ledger-governance.py"],
    ),
    Step(
        "operator-decision-ledger-v2-graph-gate",
        [sys.executable, ".github/scripts/check-operator-decision-ledger-v2-graph-governance.py"],
    ),
    Step(
        "operator-workflow-runtime-gate",
        [sys.executable, "-m", "pytest", "tests/test_operator_workflow_api.py", "-q"],
    ),
]


def _run_step(step: Step) -> tuple[bool, str]:
    proc = subprocess.run(
        step.command,
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    output = output.strip()
    return proc.returncode == 0, output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operator-workflow-only",
        action="store_true",
        help="Run only operator workflow structure gates.",
    )
    parser.add_argument(
        "--skip-core",
        action="store_true",
        help="Skip core governance gates (ssp/genome/alt4/naming).",
    )
    args = parser.parse_args()

    if args.operator_workflow_only:
        steps = OPERATOR_WORKFLOW_STEPS
    elif args.skip_core:
        steps = OPERATOR_WORKFLOW_STEPS
    else:
        steps = CORE_STEPS + OPERATOR_WORKFLOW_STEPS

    print("[infinity1-flagship-verification] starting")
    failures: list[str] = []

    for step in steps:
        ok, output = _run_step(step)
        status = "PASS" if ok else "FAIL"
        print(f"[infinity1-flagship-verification] {step.label}: {status}")
        if output:
            for line in output.splitlines()[-3:]:
                print(f"  {line}")
        if not ok:
            failures.append(step.label)

    if failures:
        print(
            "[infinity1-flagship-verification] FAIL "
            f"({len(failures)} step(s): {', '.join(failures)})"
        )
        return 1

    print(f"[infinity1-flagship-verification] PASS ({len(steps)} steps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
