#!/usr/bin/env python3
"""GA sign-off gate — INFINITY_PILOT_GA_SIGNOFF completeness."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Infinity Pilot GA sign-off document.")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    path = root / "docs" / "audit" / "INFINITY_PILOT_GA_SIGNOFF.md"
    findings: list[str] = []

    if not path.is_file():
        findings.append("missing docs/audit/INFINITY_PILOT_GA_SIGNOFF.md")
    else:
        text = path.read_text(encoding="utf-8")
        if not re.search(r"\[x\]\s*Proven", text, re.IGNORECASE):
            findings.append("GA sign-off must check Proven decision")
        if re.search(r"Reviewer:\s*(pending|TBD|—|\-)\s*$", text, re.IGNORECASE | re.MULTILINE):
            findings.append("GA sign-off reviewer must be filled")
        if "Approval timestamp:" not in text:
            findings.append("GA sign-off missing approval timestamp")

    status = "pass" if not findings else "fail"
    print(f"[ga-signoff-gate] {status} findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")

    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
