#!/usr/bin/env python3
"""Validate UGR graph index v1 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    "deploy/ugr/graph-index.json",
    "docs/contracts/UGR_GRAPH_INDEX_CONTRACT.md",
    "src/ugr/graph_index/index.py",
    "src/ugr/graph_index/store.py",
    "src/ugr/graph_index/sync.py",
]


def validate_config(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing graph index config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "max_rows_per_path" not in payload:
        findings.append(f"{path}: max_rows_per_path required")
    if str(payload.get("canonical_backend") or "") != "jsonl":
        findings.append(f"{path}: canonical_backend must be jsonl")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR graph index manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    findings.extend(validate_config(root / "deploy/ugr/graph-index.json"))
    status = "pass" if not findings else "fail"
    print(f"ugr graph index manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
