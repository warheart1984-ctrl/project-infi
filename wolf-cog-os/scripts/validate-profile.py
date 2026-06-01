#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge profile contract skeleton.")
    parser.add_argument("--profile", default="forge-selfhosted", help="Profile id to validate.")
    parser.add_argument(
        "--profiles-root",
        default="wolf-cog-os/profiles/forge",
        help="Root directory for Forge profiles.",
    )
    parser.add_argument(
        "--schema",
        default="wolf-cog-os/profiles/forge/forge-profile.schema.json",
        help="Schema stub JSON path.",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="warn")
    parser.add_argument("--output", default="ci-artifacts/profile-validation.json")
    return parser.parse_args()


def _resolve_profile_path(profile_id: str, profiles_root: Path) -> Path:
    if profile_id.endswith(".yaml"):
        return profiles_root / profile_id
    return profiles_root / f"{profile_id}.yaml"


def _parse_top_level_keys(profile_text: str) -> set[str]:
    keys: set[str] = set()
    for line in profile_text.splitlines():
        if not line or line.startswith(" ") or line.startswith("\t"):
            continue
        match = re.match(r"^([a-zA-Z0-9_]+):", line)
        if match:
            keys.add(match.group(1))
    return keys


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    profiles_root = repo_root / args.profiles_root
    schema_path = repo_root / args.schema
    profile_path = _resolve_profile_path(args.profile, profiles_root)

    findings: list[dict[str, str]] = []
    status = "pass"

    if not schema_path.exists():
        findings.append({"level": "error", "message": f"Schema file not found: {schema_path}"})
        status = "fail"
        required_top_level: list[str] = []
    else:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required_top_level = list(schema.get("required_top_level", []))

    if not profile_path.exists():
        level = "error" if args.mode == "fail" else "warning"
        findings.append({"level": level, "message": f"Profile file not found: {profile_path}"})
        if level == "error":
            status = "fail"
        present_keys: set[str] = set()
    else:
        profile_text = profile_path.read_text(encoding="utf-8")
        present_keys = _parse_top_level_keys(profile_text)

    missing = [key for key in required_top_level if key not in present_keys]
    for key in missing:
        level = "error" if args.mode == "fail" else "warning"
        if level == "error":
            status = "fail"
        findings.append({"level": level, "message": f"Missing top-level key: {key}"})

    result = {
        "validator": "forge-profile-contract",
        "mode": args.mode,
        "status": status,
        "profile_id": args.profile,
        "profile_path": str(profile_path.relative_to(repo_root)) if profile_path.exists() else str(profile_path),
        "required_top_level": required_top_level,
        "present_top_level": sorted(present_keys),
        "findings": findings,
    }

    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(
        "Forge profile validation:"
        f" profile={args.profile}, mode={args.mode}, status={status}, findings={len(findings)}"
    )
    return 1 if status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
