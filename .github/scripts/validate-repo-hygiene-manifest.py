#!/usr/bin/env python3
"""Validate REPO_HYGIENE_MANIFEST.json against schema and registered checkers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MANIFEST_REL = "docs/audit/REPO_HYGIENE_MANIFEST.json"
SCHEMA_REL = "schemas/repo_hygiene_manifest.v1.json"

REGISTERED_CHECKS = frozenset(
    {
        "forbidden_root_names",
        "forbidden_root_globs",
        "poison_dir_markers",
        "forbidden_tracked_prefixes",
        "local_work_dirs",
        "stale_payload_runtime",
        "forbidden_root_argv_globs",
    }
)

REQUIRED_LIST_KEYS = frozenset(
    {
        "forbidden_root_names",
        "forbidden_root_globs",
        "forbidden_root_argv_globs",
        "forbidden_tracked_prefixes",
        "poison_dir_markers",
        "allowed_bundle_roots",
        "local_work_dirs",
    }
)


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object root: {path}")
    return data


def _validate_schema(manifest: dict, schema: dict) -> list[str]:
    errors: list[str] = []

    if manifest.get("manifest_version") != schema.get("properties", {}).get("manifest_version", {}).get("const"):
        errors.append("manifest_version must be repo_hygiene_manifest.v1")

    for key in schema.get("required", []):
        if key not in manifest:
            errors.append(f"missing required key: {key}")

    rules = manifest.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rules[{idx}] must be an object")
            continue
        for req in ("id", "severity", "check", "remediation"):
            if req not in rule:
                errors.append(f"rules[{idx}] missing {req}")
        rule_id = str(rule.get("id", ""))
        if rule_id in seen_ids:
            errors.append(f"duplicate rule id: {rule_id}")
        seen_ids.add(rule_id)
        if rule.get("severity") not in ("error", "warn"):
            errors.append(f"rules[{idx}] invalid severity")
        if not str(rule.get("id", "")).startswith("hygiene."):
            errors.append(f"rules[{idx}] id must start with hygiene.")

    for key in REQUIRED_LIST_KEYS:
        value = manifest.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"{key} must be a non-empty array")

    return errors


def _validate_check_registry(manifest: dict) -> list[str]:
    errors: list[str] = []
    rules = manifest.get("rules") or []
    checks_in_rules = {str(r.get("check")) for r in rules if isinstance(r, dict)}
    for check in checks_in_rules:
        if check not in REGISTERED_CHECKS:
            errors.append(f"unknown check '{check}' — not in REGISTERED_CHECKS")
    for check in REGISTERED_CHECKS:
        if check == "stale_payload_runtime":
            continue
        if check not in checks_in_rules:
            errors.append(f"registered check '{check}' missing from rules[]")
    rule_ids = {str(r.get("id")) for r in rules if isinstance(r, dict)}
    expected_ids = {
        "hygiene.forbidden_root_name",
        "hygiene.forbidden_root_glob",
        "hygiene.poison_dir",
        "hygiene.forbidden_tracked",
        "hygiene.local_work_dir",
        "hygiene.stale_payload_runtime",
        "hygiene.stray_root_argv",
    }
    missing = expected_ids - rule_ids
    if missing:
        errors.append(f"missing expected rule ids: {', '.join(sorted(missing))}")
    return errors


def validate_manifest(repo_root: Path) -> list[str]:
    manifest_path = repo_root / MANIFEST_REL
    schema_path = repo_root / SCHEMA_REL
    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]
    if not schema_path.is_file():
        return [f"missing schema: {schema_path}"]
    manifest = _load_json(manifest_path)
    schema = _load_json(schema_path)
    errors = _validate_schema(manifest, schema)
    errors.extend(_validate_check_registry(manifest))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repo hygiene manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors = validate_manifest(repo_root)

    if errors and not args.summary_only:
        for err in errors:
            print(f"[ERROR] manifest: {err}")

    print(f"Repo hygiene manifest: errors={len(errors)}, mode={args.mode}")
    if errors and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
