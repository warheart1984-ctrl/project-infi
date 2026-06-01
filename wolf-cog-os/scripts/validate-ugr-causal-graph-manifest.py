#!/usr/bin/env python3
"""Validate UGR causal graph v1 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    "deploy/ugr/causal-graph.json",
    "deploy/ugr/regions.json",
    "docs/contracts/UGR_CAUSAL_GRAPH_V1_CONTRACT.md",
    "src/ugr/causal_graph/store.py",
    "src/ugr/causal_graph/provenance.py",
    "src/ugr/causal_graph/region_health.py",
    "src/ugr/embryo/gateway_v1.py",
]


def validate_config(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing causal graph config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if str(payload.get("canonical_claim_backend") or "") != "jsonl":
        findings.append(f"{path}: canonical_claim_backend must be jsonl")
    if "persistent_edge_log" not in payload:
        findings.append(f"{path}: persistent_edge_log required")
    return findings


def validate_regions(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing regions config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("regions"):
        findings.append(f"{path}: regions map required")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR causal graph v1 manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    findings.extend(validate_config(root / "deploy/ugr/causal-graph.json"))
    findings.extend(validate_regions(root / "deploy/ugr/regions.json"))
    status = "pass" if not findings else "fail"
    print(f"ugr causal graph manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
