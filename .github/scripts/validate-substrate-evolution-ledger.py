#!/usr/bin/env python3
"""Validate Forge substrate evolution ledger against live registry."""
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
    "substrate_ids",
    "status",
    "verification",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate substrate evolution ledger.")
    parser.add_argument(
        "--ledger",
        default=".github/governance/substrate-evolution-ledger.json",
        help="Ledger path relative to repo root.",
    )
    parser.add_argument(
        "--registry",
        default="wolf-cog-os/forge/substrates/registry.json",
        help="Substrate registry path relative to repo root.",
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
        return 1 if args.mode == "fail" else 0

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_ids = set(registry.get("substrates", {}))
    registry_version = registry.get("registry_version", "")

    entry_ids: set[str] = set()
    active_ids: set[str] = set()
    for idx, entry in enumerate(ledger.get("entries", [])):
        prefix = f"entries[{idx}]"
        missing = [key for key in REQUIRED_ENTRY_KEYS if key not in entry]
        if missing:
            findings.append(f"{prefix}: missing keys {missing}")
            continue
        entry_id = str(entry["id"])
        if entry_id in entry_ids:
            findings.append(f"{prefix}: duplicate id {entry_id}")
        entry_ids.add(entry_id)
        if entry.get("status") == "active":
            active_ids.update(entry.get("substrate_ids", []))
        for substrate_id in entry.get("substrate_ids", []):
            if substrate_id not in registry_ids:
                findings.append(f"{entry_id}: substrate_id {substrate_id} not in registry")
        for test_path in entry.get("verification", {}).get("tests", []):
            if not (repo_root / test_path).is_file():
                findings.append(f"{entry_id}: verification test missing {test_path}")

    if registry_version and registry_version not in {
        entry.get("registry_version", "") for entry in ledger.get("entries", [])
    }:
        findings.append(f"registry_version {registry_version} has no ledger entry")

    uncovered = registry_ids - active_ids
    experimental = {
        sid
        for entry in ledger.get("entries", [])
        if entry.get("status") == "experimental"
        for sid in entry.get("substrate_ids", [])
    }
    uncovered -= experimental
    if uncovered:
        findings.append(f"registry substrates without active ledger coverage: {sorted(uncovered)}")

    status = "pass" if not findings else "fail"
    print(
        f"substrate evolution ledger: status={status}, entries={len(ledger.get('entries', []))},"
        f" registry_substrates={len(registry_ids)}, findings={len(findings)}"
    )
    for finding in findings:
        print(f"[{'ERROR' if args.mode == 'fail' else 'WARN'}] {finding}")
    if status == "fail" and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
