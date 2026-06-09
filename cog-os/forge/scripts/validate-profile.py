#!/usr/bin/env python3
"""Validate Nova NorthStar CoG OS forge profile YAML files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_simple(text: str) -> dict:
    data: dict = {}
    current_key = None
    list_keys = {"packages", "services", "gates"}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_key = line[:-1].strip()
            if current_key in list_keys:
                data[current_key] = []
            else:
                data[current_key] = ""
            continue
        if line.strip().startswith("- ") and current_key in list_keys:
            data[current_key].append(line.strip()[2:].strip())
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def load_profile(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ImportError:
        return parse_simple(text)


def validate_profile(path: Path) -> list[str]:
    errors: list[str] = []
    data = load_profile(path)
    for key in ("name", "init_mode", "packages", "services"):
        if key not in data:
            errors.append(f"{path.name}: missing {key}")
    if data.get("name") and data["name"] != path.stem:
        errors.append(f"{path.name}: name mismatch ({data.get('name')})")
    init_mode = data.get("init_mode")
    if init_mode not in ("custom", "hybrid"):
        errors.append(f"{path.name}: init_mode must be custom or hybrid (got {init_mode!r})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles-dir", default="cog-os/forge/profiles")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    args = parser.parse_args()
    profiles_dir = Path(args.profiles_dir)
    if not profiles_dir.is_dir():
        print(f"profiles dir missing: {profiles_dir}", file=sys.stderr)
        return 1 if args.mode == "fail" else 0

    errors: list[str] = []
    for path in sorted(profiles_dir.glob("*.yaml")):
        errors.extend(validate_profile(path))

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1 if args.mode == "fail" else 0
    print(f"validated {len(list(profiles_dir.glob('*.yaml')))} profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
