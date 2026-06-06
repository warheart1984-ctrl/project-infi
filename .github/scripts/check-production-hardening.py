#!/usr/bin/env python3
"""Production hardening gate — pilot deploy safety invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    findings: list[str] = []

    pilot_env = root / "deploy" / "pilot" / ".env.example"
    if not pilot_env.is_file():
        findings.append("missing deploy/pilot/.env.example")
    else:
        text = pilot_env.read_text(encoding="utf-8")
        if "PLATFORM_REQUIRE_API_KEY=1" not in text:
            findings.append("deploy/pilot/.env.example must set PLATFORM_REQUIRE_API_KEY=1")
        if "PLATFORM_WITNESS_REQUIRED=0" not in text:
            findings.append("deploy/pilot/.env.example must default PLATFORM_WITNESS_REQUIRED=0")
        if re.search(r"PLATFORM_MASTER_API_KEY=(?!change-me)", text):
            findings.append("deploy/pilot/.env.example must use change-me placeholder for master key")

    platform_env = root / "deploy" / "platform" / ".env.example"
    if platform_env.is_file():
        pt = platform_env.read_text(encoding="utf-8")
        if "PLATFORM_REQUIRE_API_KEY" in pt and "PLATFORM_REQUIRE_API_KEY=1" not in pt:
            findings.append("deploy/platform/.env.example should require API key in production")

    ftg = root / "docs" / "operations" / "FIRST_TIME_OPERATOR_GUIDE.md"
    if ftg.is_file():
        if "production" not in ftg.read_text(encoding="utf-8").lower():
            findings.append("FIRST_TIME_OPERATOR_GUIDE must warn about production secrets")
    else:
        findings.append("missing docs/operations/FIRST_TIME_OPERATOR_GUIDE.md")

    baseline = root / "docs" / "baseline" / "INFINITY_PILOT_BASELINE_CHECKLIST.md"
    if not baseline.is_file():
        findings.append("missing INFINITY_PILOT_BASELINE_CHECKLIST.md")

    if findings:
        print("[production-hardening-gate] FAIL")
        for item in findings:
            print(f"  - {item}")
        return 1

    print("[production-hardening-gate] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
