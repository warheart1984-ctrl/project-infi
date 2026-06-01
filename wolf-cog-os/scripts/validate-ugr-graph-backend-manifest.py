#!/usr/bin/env python3
"""Validate UGR graph backend artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED = [
    "deploy/ugr/graph-backend.json",
    "src/ugr/graph_backends/sqlite_backend.py",
    "docs/contracts/UGR_GRAPH_BACKEND_CONTRACT.md",
    "tests/test_ugr_graph_backend.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings = [f"missing required file: {rel}" for rel in REQUIRED if not (root / rel).exists()]
    config_path = root / "deploy/ugr/graph-backend.json"
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if str(payload.get("canonical_backend") or "") != "jsonl":
            findings.append(f"{config_path}: canonical_backend must be jsonl")
        if str(payload.get("selected_external_db") or "") != "sqlite":
            findings.append(f"{config_path}: selected_external_db must be sqlite")
    status = "pass" if not findings else "fail"
    print(f"ugr graph backend manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    return 1 if findings and args.mode == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
