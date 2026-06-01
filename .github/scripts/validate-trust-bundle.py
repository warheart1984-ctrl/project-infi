#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


CLAIM_VALUES = {"asserted", "proven", "rejected"}
ISO_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

SIGNIFICANT_PATH_PATTERNS = (
    re.compile(r"^META_ARCHITECT_LAWBOOK\.md$"),
    re.compile(r"^REPO_PROOF_LAW\.md$"),
    re.compile(r"^README\.md$"),
    re.compile(r"^HUMAN_AI_CO_COLLABORATION_CHARTER\.md$"),
    re.compile(r"^docs/"),
    re.compile(r"^templates/"),
    re.compile(r"^\.cursor/rules/"),
    re.compile(r"^\.github/workflows/"),
    re.compile(r"^\.github/scripts/"),
)

BUNDLE_PATH_PATTERN = re.compile(r"^docs/trust_bundles/.+\.md$")


@dataclass(frozen=True)
class Finding:
    level: str
    message: str

    def render(self) -> str:
        return f"[{self.level.upper()}] {self.message}"


def _normalize_changed_files(raw: str) -> list[str]:
    if not raw.strip():
        return []
    files: list[str] = []
    for part in raw.split(","):
        value = part.strip().replace("\\", "/")
        if value:
            files.append(value)
    return files


def _is_significant_change(changed_files: list[str]) -> bool:
    for path in changed_files:
        if BUNDLE_PATH_PATTERN.match(path):
            continue
        for pattern in SIGNIFICANT_PATH_PATTERNS:
            if pattern.search(path):
                return True
    return False


def _extract_block(lines: list[str], start_idx: int) -> tuple[list[str], int]:
    block: list[str] = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("  "):
            value = line[2:].rstrip()
            if value:
                block.append(value)
            idx += 1
            continue
        break
    return block, idx


def _parse_bundle(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value == "|":
            block, idx = _extract_block(lines, idx)
            data[key] = block
            continue
        if key == "proof_links":
            proof_links, idx = _extract_block(lines, idx)
            normalized = [entry[2:].strip() for entry in proof_links if entry.startswith("- ")]
            data[key] = [item for item in normalized if item]
            continue
        if value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
            continue
        data[key] = value
    return data


def _validate_bundle(path: Path) -> tuple[list[Finding], list[Finding]]:
    findings: list[Finding] = []
    errors: list[Finding] = []
    data = _parse_bundle(path)

    claim_label = str(data.get("claim_label", "")).strip()
    if claim_label not in CLAIM_VALUES:
        errors.append(Finding("error", f"{path}: invalid claim_label '{claim_label}'"))

    why_short = data.get("why_short")
    if not isinstance(why_short, list):
        errors.append(Finding("error", f"{path}: missing why_short block"))
    else:
        non_empty = [line for line in why_short if line.strip()]
        if not non_empty:
            errors.append(Finding("error", f"{path}: why_short must have at least one line"))
        if len(non_empty) > 5:
            errors.append(Finding("error", f"{path}: why_short exceeds 5 lines"))

    proof_links = data.get("proof_links")
    none_yet = data.get("none_yet")
    proof_links_list = proof_links if isinstance(proof_links, list) else []
    if none_yet is True:
        if proof_links_list:
            errors.append(Finding("error", f"{path}: none_yet=true cannot include proof_links"))
    elif none_yet is False:
        if not proof_links_list:
            errors.append(Finding("error", f"{path}: none_yet=false requires proof_links"))
    else:
        errors.append(Finding("error", f"{path}: none_yet must be true or false"))

    override_command = str(data.get("override_command", "")).strip()
    if not override_command:
        errors.append(Finding("error", f"{path}: override_command is required"))

    override_breaks_blueprint = data.get("override_breaks_blueprint")
    debt_ticket_ref = str(data.get("debt_ticket_ref", "")).strip()
    if override_breaks_blueprint is True and debt_ticket_ref in {"", "none"}:
        errors.append(
            Finding(
                "error",
                f"{path}: debt_ticket_ref is required when override_breaks_blueprint=true",
            )
        )

    for ts_key in ("created_at_utc", "updated_at_utc"):
        ts_val = str(data.get(ts_key, "")).strip()
        if not ISO_UTC_PATTERN.match(ts_val):
            errors.append(Finding("error", f"{path}: {ts_key} must be ISO-8601 UTC"))

    for text_key in ("author", "context"):
        text_val = str(data.get(text_key, "")).strip()
        if not text_val:
            errors.append(Finding("error", f"{path}: {text_key} is required"))

    if not errors:
        findings.append(Finding("info", f"{path}: Trust Bundle validation passed"))
    findings.extend(errors)
    return findings, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Doctrine XI Trust Bundle presence and schema for significant changes."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root.",
    )
    parser.add_argument(
        "--changed-files",
        default="",
        help="Comma-separated changed file list from CI.",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    changed_files = _normalize_changed_files(args.changed_files)

    findings: list[Finding] = []
    errors: list[Finding] = []

    significant = _is_significant_change(changed_files) if changed_files else False
    if significant:
        changed_bundles = [path for path in changed_files if BUNDLE_PATH_PATTERN.match(path)]
        if not changed_bundles:
            errors.append(
                Finding(
                    "error",
                    "Significant AI-driven governance change detected but no Trust Bundle was changed in docs/trust_bundles/.",
                )
            )
        for rel_path in changed_bundles:
            bundle_path = (repo_root / rel_path).resolve()
            if not bundle_path.exists():
                errors.append(Finding("error", f"Referenced Trust Bundle does not exist: {rel_path}"))
                continue
            bundle_findings, bundle_errors = _validate_bundle(bundle_path)
            findings.extend(bundle_findings)
            errors.extend(bundle_errors)
    else:
        findings.append(
            Finding(
                "info",
                "No significant AI-driven governance change detected; Trust Bundle requirement not triggered.",
            )
        )

    for finding in findings:
        print(finding.render())
    print(
        "Trust bundle check: "
        f"changed_files={len(changed_files)}, significant={significant}, errors={len(errors)}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
