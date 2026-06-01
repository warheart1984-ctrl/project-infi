#!/usr/bin/env python3
"""Validate Forge multi-arch platform matrix."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge arch matrix registry.")
    parser.add_argument(
        "--matrix",
        default="wolf-cog-os/forge/platforms/arch-matrix.json",
        help="Arch matrix path relative to repo root.",
    )
    parser.add_argument(
        "--backend-registry",
        default="wolf-cog-os/forge/backends/registry.json",
        help="Rootfs backend registry for cross-check.",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    matrix_path = repo_root / args.matrix
    backend_path = repo_root / args.backend_registry
    findings: list[str] = []

    if not matrix_path.is_file():
        findings.append(f"arch matrix missing: {matrix_path}")
    if not backend_path.is_file():
        findings.append(f"backend registry missing: {backend_path}")
    if findings:
        for item in findings:
            print(f"[ERROR] {item}")
        return 1 if args.mode == "fail" else 0

    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    backends = json.loads(backend_path.read_text(encoding="utf-8"))
    default_arch = matrix.get("default_arch", "")
    arches = matrix.get("arches", {})
    backend_map = matrix.get("backend_arch_map", {})

    if default_arch not in arches:
        findings.append(f"default_arch {default_arch} not in arches")
    for arch_id, spec in arches.items():
        if not spec.get("status"):
            findings.append(f"{arch_id}: missing status")
        for fmt in spec.get("cloud_outputs", []):
            pass
    for backend_id in backends.get("backends", {}):
        if backend_id not in backend_map:
            findings.append(f"backend {backend_id} missing from backend_arch_map")

    status = "pass" if not findings else "fail"
    print(
        f"arch matrix validation: status={status}, arches={len(arches)},"
        f" backends_mapped={len(backend_map)}, findings={len(findings)}"
    )
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
