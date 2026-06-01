#!/usr/bin/env python3
"""Validate Forge rootfs backend registry and host tool availability."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge rootfs backend contract.")
    parser.add_argument(
        "--backend",
        default="debootstrap",
        help="Backend id from registry (default: debootstrap).",
    )
    parser.add_argument(
        "--registry",
        default="wolf-cog-os/forge/backends/registry.json",
        help="Backend registry path relative to repo root.",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument(
        "--registry-only",
        action="store_true",
        help="Validate registry contract only (skip host tool checks).",
    )
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    registry_path = repo_root / args.registry
    if not registry_path.is_file():
        print(f"ERROR: backend registry missing: {registry_path}", file=sys.stderr)
        return 2

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    backends = registry.get("backends", {})
    backend_id = args.backend or registry.get("default_backend_id", "debootstrap")
    spec = backends.get(backend_id)
    if not spec:
        print(f"ERROR: backend not registered: {backend_id}", file=sys.stderr)
        return 2

    findings: list[dict[str, str]] = []
    status = "pass"
    impl = spec.get("implementation_status", "unknown")
    if impl == "stub":
        findings.append({"level": "warning", "message": f"backend {backend_id} is stub-only"})
        status = "warn"
    elif impl == "production" and not args.registry_only:
        for tool in spec.get("required_tools", []):
            if not shutil.which(tool):
                findings.append({"level": "error", "message": f"required tool missing: {tool}"})
                status = "fail"

    result = {
        "validator": registry.get("default_contract_version", "forge-rootfs-backend.v1"),
        "registry_version": registry.get("registry_version", ""),
        "status": status if args.mode == "fail" or status == "pass" else "warn",
        "backend_id": backend_id,
        "implementation_status": impl,
        "package_manager": spec.get("package_manager", ""),
        "supported_arches": spec.get("supported_arches", []),
        "findings": findings,
    }

    if args.output:
        out = repo_root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"rootfs backend validation: status={result['status']}, backend={backend_id}, impl={impl}")
    for finding in findings:
        print(f"[{finding['level'].upper()}] {finding['message']}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
