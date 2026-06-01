#!/usr/bin/env python3
"""Validate UGR embryo v0 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    "deploy/ugr/model-pool.json",
    "docs/contracts/UGR_EMBRYO_V0_CONTRACT.md",
    "src/ugr/embryo/gateway.py",
    "src/ugr/embryo/model_pool.py",
    "src/ugr/embryo/health.py",
]


def validate_model_pool(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing model pool config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    slots = payload.get("slots") or {}
    if not slots:
        findings.append(f"{path}: no slots declared")
    if "rail_caps" not in payload:
        findings.append(f"{path}: rail_caps required")
    for tier, spec in slots.items():
        if not spec.get("proposal_only", False):
            findings.append(f"{path}: slot {tier} must be proposal_only")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR embryo v0 manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    findings.extend(validate_model_pool(root / "deploy/ugr/model-pool.json"))
    status = "pass" if not findings else "fail"
    print(f"ugr embryo v0 manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
