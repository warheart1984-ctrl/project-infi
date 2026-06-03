#!/usr/bin/env python3
"""Lint AAIS Codex/Cursor naming protocol for src/**/*.py."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ALIASES_PATH = ROOT / "governance" / "legacy_engineering_aliases.v1.json"

LEGACY_SUFFIXES = ("_organ.py", "_fabric.py")
ENGINEERING_HEADER = re.compile(r"^#\s*Engineering:\s*.+", re.MULTILINE)


def load_grandfather_paths() -> set[str]:
    if not ALIASES_PATH.is_file():
        print(f"ERROR: missing grandfather registry {ALIASES_PATH}", file=sys.stderr)
        return set()
    data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    paths: set[str] = set()
    for entry in data.get("aliases", []):
        legacy = entry.get("legacy_path")
        if legacy:
            paths.add(legacy.replace("\\", "/"))
    return paths


def looks_like_subsystem_shell(text: str) -> bool:
    return (
        "MODULE_ID" in text
        or "cisiv_stage" in text
        or ("build_" in text and "_status" in text)
    )


def is_legacy_stem(path: Path) -> bool:
    return path.name.endswith(LEGACY_SUFFIXES)


def main() -> int:
    grandfather = load_grandfather_paths()
    errors: list[str] = []
    warnings: list[str] = []

    if not SRC.is_dir():
        print("naming-gate: src/ missing — skip")
        return 0

    for py in sorted(SRC.rglob("*.py")):
        rel = py.relative_to(ROOT).as_posix()
        if is_legacy_stem(py):
            if rel not in grandfather:
                errors.append(
                    f"{rel}: *_organ/*_fabric path not grandfathered — "
                    "use engineering stem or register via MP-X"
                )
            continue

        text = py.read_text(encoding="utf-8", errors="replace")
        if looks_like_subsystem_shell(text) and not ENGINEERING_HEADER.search(text):
            warnings.append(f"{rel}: subsystem shell missing '# Engineering:' file header line")

    for msg in warnings:
        print(f"WARNING: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"ERROR: {msg}", file=sys.stderr)

    if errors:
        print(f"naming-gate: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1

    print(
        f"naming-gate: PASS ({len(grandfather)} grandfathered legacy paths, "
        f"{len(warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
