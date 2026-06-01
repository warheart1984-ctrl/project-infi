#!/usr/bin/env python3
"""Validate Forge backend evolution ledger against backend registry."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_ENTRY_KEYS = (
    "id",
    "date",
    "author",
    "change_type",
    "registry_version",
    "contract_version",
    "backend_ids",
    "status",
    "verification",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate backend evolution ledger.")
    parser.add_argument(
        "--ledger",
        default=".github/governance/backend-evolution-ledger.json",
    )
    parser.add_argument(
        "--registry",
        default="wolf-cog-os/forge/backends/registry.json",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    ledger_path = repo_root / args.ledger
    registry_path = repo_root / args.registry
    findings: list[str] = []

    if not ledger_path.is_file():
        findings.append(f"ledger missing: {ledger_path}")
    if not registry_path.is_file():
        findings.append(f"registry missing: {registry_path}")
    if findings:
        for item in findings:
            print(f"[ERROR] {item}", file=sys.stderr)
        return 1

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    backend_ids = set(registry.get("backends", {}))
    active_ids: set[str] = set()

    for idx, entry in enumerate(ledger.get("entries", [])):
        prefix = f"entries[{idx}]"
        missing = [key for key in REQUIRED_ENTRY_KEYS if key not in entry]
        if missing:
            findings.append(f"{prefix}: missing keys {missing}")
            continue
        if entry.get("status") in {"active", "experimental"}:
            active_ids.update(entry.get("backend_ids", []))
        for backend_id in entry.get("backend_ids", []):
            if backend_id not in backend_ids:
                findings.append(f"{entry['id']}: backend_id {backend_id} not in registry")
        for test_path in entry.get("verification", {}).get("tests", []):
            if not (repo_root / test_path).is_file():
                findings.append(f"{entry['id']}: verification test missing {test_path}")

    uncovered = backend_ids - active_ids
    if uncovered:
        findings.append(f"registry backends without active ledger coverage: {sorted(uncovered)}")

    status = "pass" if not findings else "fail"
    print(f"backend evolution ledger: status={status}, findings={len(findings)}")
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
