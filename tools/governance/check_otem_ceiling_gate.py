#!/usr/bin/env python3
"""OTEM Level 20 constitutional recovery ceiling integration gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

REQUIRED_PATHS = (
    "docs/contracts/OTEM_CEILING_RULES.md",
    "schemas/otem_ceiling_rules.v1.json",
    "src/otem_ceiling.py",
    "src/immune_hardening.py",
    "tests/test_otem_ceiling.py",
    "tests/test_otem_capability.py",
    "frontend/src/pages/OperatorCeilingRecovery.jsx",
    "docs/operations/OTEM_CEILING_OPERATOR_HANDBOOK.md",
)

PYTEST_TARGETS = (
    "tests/test_otem_ceiling.py",
    "tests/test_otem_capability.py",
)


def check_files(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (root / rel).is_file():
            errors.append(f"missing required file: {rel}")
    return errors


def check_contract_surface(root: Path) -> list[str]:
    errors: list[str] = []
    contract = root / "docs/contracts/UGR_OPERATOR_CONSOLE_CONTRACT.md"
    if not contract.is_file():
        errors.append("missing UGR operator console contract")
        return errors
    text = contract.read_text(encoding="utf-8")
    if "1.3" not in text:
        errors.append("UGR operator console contract must document v1.3")
    if "otem_ceiling" not in text:
        errors.append("UGR operator console contract must document otem_ceiling key")
    return errors


def check_snapshot_version() -> list[str]:
    errors: list[str] = []
    from src.ugr.operator_console.snapshot import CONSOLE_VERSION, GATE_COMMANDS

    if CONSOLE_VERSION != "1.3":
        errors.append(f"operator console version must be 1.3 (got {CONSOLE_VERSION})")
    if "make otem-ceiling-gate" not in GATE_COMMANDS:
        errors.append("operator console GATE_COMMANDS must include make otem-ceiling-gate")
    return errors


def main() -> int:
    errors = check_files(_ROOT)
    errors.extend(check_contract_surface(_ROOT))
    errors.extend(check_snapshot_version())
    if errors:
        for err in errors:
            print(f"[otem-ceiling-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST_TARGETS, "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[otem-ceiling-gate] FAIL: pytest")
        return 1

    print("[otem-ceiling-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
