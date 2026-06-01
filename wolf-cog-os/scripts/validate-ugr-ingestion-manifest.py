#!/usr/bin/env python3
"""Validate UGR Phase 3 ingestion artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    "deploy/ugr/ingestion.sources.json",
    "docs/contracts/UGR_INGESTION_CONTRACT.md",
    "src/ugr/ingestion/pipeline.py",
]


def validate_sources(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing ingestion config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources") or {}
    if not sources:
        findings.append(f"{path}: no sources declared")
    enabled = [sid for sid, spec in sources.items() if spec.get("enabled")]
    if not enabled:
        findings.append(f"{path}: no enabled sources")
    for source_id, spec in sources.items():
        if "type" not in spec:
            findings.append(f"{path}: source {source_id} missing type")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR ingestion manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    findings.extend(validate_sources(root / "deploy/ugr/ingestion.sources.json"))
    status = "pass" if not findings else "fail"
    print(f"ugr ingestion manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
