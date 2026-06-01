#!/usr/bin/env python3
"""Validate UGR Phase 4 platform scale artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    "deploy/ugr/tenants.json",
    "deploy/ugr/graph-shards.json",
    "deploy/ugr/cognition-promotion.json",
    "docs/contracts/UGR_PLATFORM_CONTRACT.md",
    "src/ugr/platform/sharded_ledger.py",
    "src/ugr/platform/shadow_runtime.py",
    "src/ugr/platform/cognition_cicd.py",
]


def validate_tenants(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing tenants config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    tenants = payload.get("tenants") or {}
    if "global" not in tenants:
        findings.append(f"{path}: missing global tenant")
    enabled = [tid for tid, spec in tenants.items() if spec.get("enabled")]
    if not enabled:
        findings.append(f"{path}: no enabled tenants")
    return findings


def validate_shards(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing graph shards config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    shards = payload.get("shards") or {}
    if "shard-global" not in shards:
        findings.append(f"{path}: missing shard-global")
    return findings


def validate_promotion(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing cognition promotion config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    promotion = payload.get("promotion") or {}
    if "min_belief_match_rate" not in promotion:
        findings.append(f"{path}: promotion.min_belief_match_rate required")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR platform manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    findings.extend(validate_tenants(root / "deploy/ugr/tenants.json"))
    findings.extend(validate_shards(root / "deploy/ugr/graph-shards.json"))
    findings.extend(validate_promotion(root / "deploy/ugr/cognition-promotion.json"))
    status = "pass" if not findings else "fail"
    print(f"ugr platform manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
