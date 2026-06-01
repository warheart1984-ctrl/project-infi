#!/usr/bin/env python3
"""Validate Forge variant pipeline specs (v2 contract)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SCRIPT_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from forge_pipeline import parse_simple_yaml  # noqa: E402


REQUIRED_TOP = ("schema_version", "name", "variant", "substrate", "output")
REQUIRED_VARIANT = ("id", "channel")
ALLOWED_CHANNELS = {"dev", "rc", "stable", "nightly"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge pipeline YAML spec.")
    parser.add_argument("pipeline", nargs="?", default="", help="Pipeline YAML path.")
    parser.add_argument("--all", action="store_true", help="Validate all pipelines in forge/pipelines.")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def validate_pipeline(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.is_file():
        return [f"pipeline missing: {path}"]
    spec = parse_simple_yaml(path)
    for key in REQUIRED_TOP:
        if key not in spec:
            findings.append(f"{path.name}: missing top-level key {key}")
    schema_version = str(spec.get("schema_version", ""))
    if schema_version != "forge-pipeline.v2":
        findings.append(f"{path.name}: schema_version must be forge-pipeline.v2 (got {schema_version or 'missing'})")
    variant = spec.get("variant", {})
    if not isinstance(variant, dict):
        findings.append(f"{path.name}: variant must be a mapping")
        variant = {}
    for key in REQUIRED_VARIANT:
        if key not in variant:
            findings.append(f"{path.name}: variant.{key} required")
    channel = str(variant.get("channel", ""))
    if channel and channel not in ALLOWED_CHANNELS:
        findings.append(f"{path.name}: invalid variant.channel {channel}")
    repro = spec.get("reproducibility", {})
    if isinstance(repro, dict) and repro.get("deterministic") is True:
        if not str(repro.get("seed", "")).strip():
            findings.append(f"{path.name}: reproducibility.seed required when deterministic=true")
    output = spec.get("output", {})
    if isinstance(output, dict):
        if not str(output.get("iso_name", "")).strip():
            findings.append(f"{path.name}: output.iso_name required")
    return findings


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    paths: list[Path] = []
    if args.all:
        paths = sorted((repo_root / "wolf-cog-os/forge/pipelines").glob("*.yaml"))
    elif args.pipeline:
        paths = [repo_root / args.pipeline]
    else:
        print("ERROR: provide pipeline path or --all", file=sys.stderr)
        return 2

    all_findings: list[str] = []
    for path in paths:
        if path.name == "schema":
            continue
        all_findings.extend(validate_pipeline(path))

    status = "pass" if not all_findings else "fail"
    result = {
        "validator": "forge-pipeline.v2",
        "status": status if args.mode == "fail" or status == "pass" else "warn",
        "pipelines_checked": len(paths),
        "findings": all_findings,
    }
    if args.output:
        out = repo_root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"pipeline validation: status={result['status']} checked={len(paths)} findings={len(all_findings)}")
    for finding in all_findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
