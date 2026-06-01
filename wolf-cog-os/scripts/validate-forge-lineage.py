#!/usr/bin/env python3
"""Validate forge-lineage.json artifact contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SCRIPT_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from forge_lineage import LINEAGE_SCHEMA, compute_lineage_id  # noqa: E402


REQUIRED_KEYS = (
    "schema_version",
    "lineage_id",
    "pipeline_name",
    "variant_id",
    "profile_id",
    "reproducibility_seed",
    "lineage_hash_alg",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge lineage artifact.")
    parser.add_argument("--lineage", default="ci-artifacts/forge-lineage.json")
    parser.add_argument("--expected-lineage-id", default="")
    parser.add_argument("--require-parent", action="store_true")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def validate_lineage(path: Path, expected_id: str = "", require_parent: bool = False) -> tuple[str, list[str]]:
    findings: list[str] = []
    if not path.is_file():
        return "fail", [f"lineage artifact missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "fail", [f"invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        return "fail", ["lineage root must be object"]
    for key in REQUIRED_KEYS:
        if key not in payload:
            findings.append(f"missing key: {key}")
    if payload.get("schema_version") != LINEAGE_SCHEMA:
        findings.append(f"schema_version must be {LINEAGE_SCHEMA}")
    observed_id = str(payload.get("lineage_id", ""))
    recomputed = compute_lineage_id(payload)
    if observed_id and observed_id != recomputed:
        findings.append("lineage_id does not match recomputed hash")
    if expected_id and observed_id != expected_id:
        findings.append(f"lineage_id mismatch: expected={expected_id} observed={observed_id or 'missing'}")
    if require_parent and not str(payload.get("parent_lineage_id", "")).strip():
        findings.append("parent_lineage_id required but empty")
    status = "pass" if not findings else "fail"
    return status, findings


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    lineage_path = repo_root / args.lineage
    status, findings = validate_lineage(
        lineage_path,
        expected_id=args.expected_lineage_id.strip(),
        require_parent=args.require_parent,
    )
    result = {
        "validator": "forge-lineage-validator.v1",
        "status": status if args.mode == "fail" or status == "pass" else "warn",
        "lineage_path": str(lineage_path),
        "findings": findings,
    }
    if args.output:
        out = repo_root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"forge lineage validation: status={result['status']} findings={len(findings)}")
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
