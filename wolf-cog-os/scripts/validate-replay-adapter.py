#!/usr/bin/env python3
"""Validate Forge replay adapter registry and build wiring (P10)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate replay adapter registry.")
    parser.add_argument("--registry", default="wolf-cog-os/forge/replay-adapters/registry.json")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    registry_path = repo_root / args.registry
    if not registry_path.is_file():
        print(f"ERROR: replay adapter registry missing: {registry_path}", file=sys.stderr)
        return 2

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    findings: list[str] = []
    script_dir = repo_root / "wolf-cog-os/scripts/lib/replay-adapters"
    dispatcher = repo_root / "wolf-cog-os/scripts/lib/replay-adapters.sh"
    if not dispatcher.is_file():
        findings.append("replay adapter dispatcher missing: replay-adapters.sh")

    production_count = 0
    wired_count = 0
    for adapter_id, spec in registry.get("adapters", {}).items():
        module = script_dir / f"{adapter_id}.sh"
        if spec.get("wired_in_build"):
            wired_count += 1
            if not module.is_file():
                findings.append(f"{adapter_id}: wired_in_build but module missing")
        if spec.get("status") == "production":
            production_count += 1
            if not spec.get("wired_in_build"):
                findings.append(f"{adapter_id}: production but not wired_in_build")
            if not module.is_file():
                findings.append(f"{adapter_id}: production module missing")

    if production_count < 2:
        findings.append(f"groundbreaking threshold: need >=2 production adapters (have {production_count})")

    status = "pass" if not findings else "fail"
    print(
        f"replay adapter validation: status={status}, "
        f"adapters={len(registry.get('adapters', {}))}, "
        f"production={production_count}, wired={wired_count}, findings={len(findings)}"
    )
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
