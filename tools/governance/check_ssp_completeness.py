#!/usr/bin/env python3
"""SSP completeness gate — verify concept specs have full governance bundle."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


IDEAS_PENDING = Path("docs/_future/ideas_pending")
SCHEMAS_ROOT = Path("schemas")
IDEAS_SCHEMAS = IDEAS_PENDING / "schemas"

SCHEMA_LINK_RE = re.compile(r"schemas/([a-z0-9_]+\.v1\.json)", re.IGNORECASE)


def concept_specs(root: Path) -> list[Path]:
    pending = root / IDEAS_PENDING
    specs: list[Path] = []
    for path in sorted(pending.glob("*.md")):
        name = path.name
        if name == "README.md":
            continue
        if name.endswith("_MVP_PLAN.md"):
            continue
        specs.append(path)
    return specs


def mvp_plan_path(spec: Path) -> Path:
    return spec.with_name(f"{spec.stem}_MVP_PLAN.md")


def find_schema_name(spec: Path) -> str | None:
    text = spec.read_text(encoding="utf-8")
    match = SCHEMA_LINK_RE.search(text)
    return match.group(1) if match else None


def schema_exists(schema_name: str, root: Path) -> bool:
    candidates = [
        root / IDEAS_SCHEMAS / schema_name,
        root / SCHEMAS_ROOT / schema_name,
        root / "triangulation" / "schemas" / schema_name,
    ]
    return any(p.is_file() for p in candidates)


def validate_schema_json(schema_name: str, root: Path) -> tuple[bool, str]:
    for base in (root / IDEAS_SCHEMAS, root / SCHEMAS_ROOT, root / "triangulation" / "schemas"):
        path = base / schema_name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON in {path}: {exc}"
        if "$schema" not in data:
            return False, f"missing $schema in {path}"
        if "$id" not in data:
            return False, f"missing $id in {path}"
        return True, str(path)
    return False, f"schema not found: {schema_name}"


def check_spec(spec: Path, root: Path) -> list[str]:
    errors: list[str] = []
    rel = spec.relative_to(root)
    text = spec.read_text(encoding="utf-8")

    if not re.search(r"## \d+\. Proof Posture", text):
        errors.append(f"{rel}: missing Proof Posture section")
    if not re.search(r"## \d+\. CISIV Path", text):
        errors.append(f"{rel}: missing CISIV Path section")

    plan = mvp_plan_path(spec)
    if not plan.is_file():
        errors.append(f"{rel}: missing MVP plan {plan.name}")

    schema_name = find_schema_name(spec)
    if not schema_name:
        errors.append(f"{rel}: no schema link matching schemas/*.v1.json")
    elif not schema_exists(schema_name, root):
        errors.append(f"{rel}: schema {schema_name} not found")
    else:
        ok, detail = validate_schema_json(schema_name, root)
        if not ok:
            errors.append(f"{rel}: {detail}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    specs = concept_specs(root)

    if not specs:
        print("[ssp-gate] no concept specs found — OK")
        return 0

    print(f"[ssp-gate] checking {len(specs)} concept spec(s)")
    all_errors: list[str] = []
    for spec in specs:
        all_errors.extend(check_spec(spec, root))

    if all_errors:
        for err in all_errors:
            print(f"[ssp-gate] FAIL: {err}")
        return 1

    print("[ssp-gate] PASS: all concept specs have full SSP bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
