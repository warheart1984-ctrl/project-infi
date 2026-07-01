#!/usr/bin/env python3
"""Validate Agent Safety Doctrine manifests.

The validator turns the repository's agent-safety rules into a concrete gate:
agent-authored changes must preserve lawbook authority, describe a bounded
change, provide proof surfaces, and deny prohibited implementation drift.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CLAIM_VALUES = {"asserted", "proven", "rejected"}
AUTHORITY_CHAIN = ["Law", "Blueprint", "Contract", "Implementation", "Pipeline", "Tool"]
UNCERTAINTY_LEVELS = {"low", "medium", "high"}
AUTHORITY_DELTAS = {"decreased", "unchanged", "increased"}

REQUIRED_CHANGE_BOUNDARY_FIELDS = (
    "what_changed",
    "why_changed",
    "evidence_refs",
    "assumptions",
    "reversal",
)

PROHIBITED_ACTIONS = (
    "rewrite_architecture_without_blueprint_approval",
    "delete_governance_artifacts",
    "remove_validation_gates",
    "weaken_tests_to_pass",
    "replace_determinism_with_convenience",
    "introduce_hidden_dependencies",
    "claim_completion_without_proof",
)


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message

    def render(self) -> str:
        return f"[{self.level.upper()}] {self.message}"


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)


def _load_json(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError as exc:
        return None, [Finding("error", f"{path}: could not read manifest: {exc}")]
    except json.JSONDecodeError as exc:
        return None, [Finding("error", f"{path}: invalid JSON: {exc}")]

    if not isinstance(data, dict):
        return None, [Finding("error", f"{path}: manifest root must be an object")]
    return data, []


def validate_manifest(path: Path) -> tuple[list[Finding], list[Finding]]:
    findings: list[Finding] = []
    errors: list[Finding] = []

    data, load_errors = _load_json(path)
    errors.extend(load_errors)
    if data is None:
        return findings, errors

    version = data.get("agent_safety_doctrine_version")
    if version != "agent_safety_doctrine.v1":
        errors.append(
            Finding(
                "error",
                f"{path}: agent_safety_doctrine_version must be 'agent_safety_doctrine.v1'",
            )
        )

    if not _is_non_empty_string(data.get("change_id")):
        errors.append(Finding("error", f"{path}: change_id is required"))

    claim_label = data.get("claim_label")
    if claim_label not in CLAIM_VALUES:
        errors.append(Finding("error", f"{path}: invalid claim_label '{claim_label}'"))

    if data.get("authority_chain") != AUTHORITY_CHAIN:
        errors.append(
            Finding(
                "error",
                f"{path}: authority_chain must preserve Law > Blueprint > Contract > Implementation > Pipeline > Tool",
            )
        )

    if not _is_non_empty_string_list(data.get("blueprint_refs")):
        errors.append(Finding("error", f"{path}: blueprint_refs must include at least one blueprint authority"))

    _validate_change_boundary(path, data.get("change_boundary"), errors)
    _validate_prohibited_actions(path, data.get("prohibited_actions"), errors)
    _validate_uncertainty(path, data.get("uncertainty"), errors)

    if not errors:
        findings.append(Finding("info", f"{path}: Agent Safety Doctrine manifest passed"))
    return findings, errors


def _validate_change_boundary(path: Path, value: object, errors: list[Finding]) -> None:
    if not isinstance(value, dict):
        errors.append(Finding("error", f"{path}: change_boundary must be an object"))
        return

    for field in REQUIRED_CHANGE_BOUNDARY_FIELDS:
        if field not in value:
            errors.append(Finding("error", f"{path}: change_boundary.{field} is required"))

    for field in ("what_changed", "why_changed", "reversal"):
        if field in value and not _is_non_empty_string(value.get(field)):
            errors.append(Finding("error", f"{path}: change_boundary.{field} must be non-empty"))

    for field in ("evidence_refs", "assumptions"):
        if field in value and not _is_non_empty_string_list(value.get(field)):
            errors.append(
                Finding("error", f"{path}: change_boundary.{field} must include at least one non-empty entry")
            )


def _validate_prohibited_actions(path: Path, value: object, errors: list[Finding]) -> None:
    if not isinstance(value, dict):
        errors.append(Finding("error", f"{path}: prohibited_actions must be an object"))
        return

    for action in PROHIBITED_ACTIONS:
        if action not in value:
            errors.append(Finding("error", f"{path}: prohibited_actions.{action} is required"))
            continue
        if value[action] is not False:
            errors.append(
                Finding(
                    "error",
                    f"{path}: prohibited_actions.{action} must be false; agent drift is not admissible",
                )
            )


def _validate_uncertainty(path: Path, value: object, errors: list[Finding]) -> None:
    if not isinstance(value, dict):
        errors.append(Finding("error", f"{path}: uncertainty must be an object"))
        return

    level = value.get("level")
    authority_delta = value.get("authority_delta")
    if level not in UNCERTAINTY_LEVELS:
        errors.append(Finding("error", f"{path}: uncertainty.level must be one of {sorted(UNCERTAINTY_LEVELS)}"))
    if authority_delta not in AUTHORITY_DELTAS:
        errors.append(
            Finding("error", f"{path}: uncertainty.authority_delta must be one of {sorted(AUTHORITY_DELTAS)}")
        )
    if not _is_non_empty_string(value.get("resolution_path")):
        errors.append(Finding("error", f"{path}: uncertainty.resolution_path is required"))
    if level in {"medium", "high"} and authority_delta == "increased":
        errors.append(
            Finding(
                "error",
                f"{path}: authority may not increase under high uncertainty; hold, degrade, or escalate",
            )
        )


def _iter_manifest_paths(root: Path, paths: list[str]) -> list[Path]:
    selected = paths or ["governance/agent_change_manifests"]
    manifests: list[Path] = []
    for raw_path in selected:
        path = (root / raw_path).resolve()
        if not path.exists():
            continue
        if path.is_file():
            manifests.append(path)
            continue
        manifests.extend(sorted(child for child in path.rglob("*.json") if child.is_file()))
    return manifests


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Agent Safety Doctrine manifests.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Manifest file or directory to validate. Defaults to governance/agent_change_manifests.",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    manifests = _iter_manifest_paths(repo_root, args.path)
    findings: list[Finding] = []
    errors: list[Finding] = []

    if not manifests:
        errors.append(Finding("error", "No Agent Safety Doctrine manifests found."))

    for manifest_path in manifests:
        manifest_findings, manifest_errors = validate_manifest(manifest_path)
        findings.extend(manifest_findings)
        errors.extend(manifest_errors)

    for finding in [*findings, *errors]:
        print(finding.render())
    print(f"Agent safety doctrine check: manifests={len(manifests)}, errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
