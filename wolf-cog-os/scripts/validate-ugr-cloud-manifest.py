#!/usr/bin/env python3
"""Validate UGR Phase 2 cloud mesh deployment artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_SERVICES = frozenset({
    "orchestrator", "policy", "ledger", "lane_worker", "convergence",
    "ingestion", "platform", "graph_index", "model_pool", "embryo_gateway",
})
REQUIRED_FILES = [
    "deploy/ugr/mesh.local.json",
    "deploy/ugr/mesh.docker.json",
    "deploy/ugr/docker-compose.yml",
    "deploy/ugr/ingestion.sources.json",
    "deploy/ugr/tenants.json",
    "deploy/ugr/graph-shards.json",
    "deploy/ugr/graph-index.json",
    "deploy/ugr/model-pool.json",
    "deploy/ugr/cognition-promotion.json",
    "wolf-cog-os/forge/pipelines/ugr-cloud-cluster.yaml",
    "wolf-cog-os/forge/ugr/mesh.forge-node.json",
    "docs/contracts/UGR_CLOUD_MESH_CONTRACT.md",
    "docs/contracts/UGR_INGESTION_CONTRACT.md",
    "docs/contracts/UGR_PLATFORM_CONTRACT.md",
    "docs/contracts/UGR_GRAPH_INDEX_CONTRACT.md",
    "docs/contracts/UGR_EMBRYO_V0_CONTRACT.md",
]


def validate_mesh(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing mesh config: {path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    services = payload.get("services") or {}
    missing = REQUIRED_SERVICES - set(services.keys())
    if missing:
        findings.append(f"{path}: missing services {sorted(missing)}")
    for name, spec in services.items():
        if name not in REQUIRED_SERVICES:
            continue
        for key in ("host", "port", "role"):
            if key not in spec:
                findings.append(f"{path}: service {name} missing {key}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR cloud mesh manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    for rel in ("deploy/ugr/mesh.local.json", "deploy/ugr/mesh.docker.json", "wolf-cog-os/forge/ugr/mesh.forge-node.json"):
        findings.extend(validate_mesh(root / rel))
    status = "pass" if not findings else "fail"
    print(f"ugr cloud manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
