#!/usr/bin/env python3
"""Validate Forge nightly evolution ledger."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_ENTRY_KEYS = ("id", "date", "author", "change_type", "status", "targets", "verification")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate nightly evolution ledger.")
    parser.add_argument(
        "--ledger",
        default=".github/governance/nightly-evolution-ledger.json",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    ledger_path = repo_root / args.ledger
    findings: list[str] = []

    if not ledger_path.is_file():
        print(f"ERROR: ledger missing: {ledger_path}", file=sys.stderr)
        return 1

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for idx, entry in enumerate(ledger.get("entries", [])):
        prefix = f"entries[{idx}]"
        missing = [key for key in REQUIRED_ENTRY_KEYS if key not in entry]
        if missing:
            findings.append(f"{prefix}: missing keys {missing}")
        script = entry.get("verification", {}).get("scripts", [""])[0]
        if script and not (repo_root / script).is_file():
            findings.append(f"{entry.get('id', prefix)}: script missing {script}")
        for test_path in entry.get("verification", {}).get("tests", []):
            if not (repo_root / test_path).is_file():
                findings.append(f"{entry.get('id', prefix)}: test missing {test_path}")

    status = "pass" if not findings else "fail"
    print(f"nightly evolution ledger: status={status}, entries={len(ledger.get('entries', []))}, findings={len(findings)}")
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
