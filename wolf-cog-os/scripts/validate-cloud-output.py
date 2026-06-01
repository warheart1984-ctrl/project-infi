#!/usr/bin/env python3
"""Validate Forge cloud output format registry."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge cloud output registry.")
    parser.add_argument(
        "--registry",
        default="wolf-cog-os/forge/outputs/registry.json",
        help="Cloud output registry path.",
    )
    parser.add_argument("--format", default="", help="Optional format id to validate.")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument(
        "--registry-only",
        action="store_true",
        help="Skip host tool availability checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    registry_path = repo_root / args.registry
    if not registry_path.is_file():
        print(f"ERROR: cloud output registry missing: {registry_path}", file=sys.stderr)
        return 2

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    formats = registry.get("formats", {})
    format_id = args.format or registry.get("default_format", "raw-img")
    spec = formats.get(format_id)
    findings: list[str] = []
    status = "pass"

    if not spec:
        findings.append(f"format not registered: {format_id}")
        status = "fail"
    else:
        impl = spec.get("implementation_status", "unknown")
        if impl == "stub":
            findings.append(f"format {format_id} is stub-only")
            if not args.registry_only:
                status = "warn"
        elif impl == "production" and not args.registry_only:
            for tool in spec.get("required_tools", []):
                if not shutil.which(tool):
                    findings.append(f"required tool missing: {tool}")
                    status = "fail"

    print(f"cloud output validation: status={status}, format={format_id}, findings={len(findings)}")
    for finding in findings:
        level = "WARN" if status in {"pass", "warn"} and "stub-only" in finding else ("WARN" if status == "warn" else "ERROR")
        print(f"[{level}] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
