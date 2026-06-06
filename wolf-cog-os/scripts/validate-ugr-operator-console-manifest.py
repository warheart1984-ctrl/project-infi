#!/usr/bin/env python3
"""Validate UGR operator console artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REQUIRED = [
    "src/ugr/operator_console/snapshot.py",
    "src/ugr/operator_console/readout.py",
    "src/ugr/operator_console/debt_register.py",
    "src/ugr/operator_console/mesh_health.py",
    "src/ugr/operator_console/trace_viewer.py",
    "src/ugr/operator_console/forge_platform.py",
    "docs/contracts/UGR_OPERATOR_CONSOLE_CONTRACT.md",
    "docs/proof/ugr/UGR_OPERATOR_CONSOLE_PROOF.md",
    "frontend/src/pages/OperatorConsole.jsx",
    "frontend/src/components/UGRCloudForgeConsoleCard.jsx",
    "src/operator_infinity1_dashboard.py",
    "docs/contracts/INFINITY1_OPERATOR_DASHBOARD_CONTRACT.md",
    "docs/proof/platform/INFINITY1_OPERATOR_DASHBOARD_V1_PROOF.md",
    "tests/test_ugr_operator_console.py",
    "tests/test_operator_infinity1_dashboard.py",
    "frontend/src/components/operator/MonitoringAlertsPanel.jsx",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR operator console manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings = [f"missing required file: {rel}" for rel in REQUIRED if not (root / rel).exists()]
    status = "pass" if not findings else "fail"
    print(f"ugr operator console manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    return 1 if findings and args.mode == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
