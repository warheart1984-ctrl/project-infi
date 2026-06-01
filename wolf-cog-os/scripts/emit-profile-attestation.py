#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit Forge profile attestation skeleton.")
    parser.add_argument("--profile", default="forge-selfhosted")
    parser.add_argument(
        "--profiles-root",
        default="wolf-cog-os/profiles/forge",
        help="Root directory for Forge profiles.",
    )
    parser.add_argument(
        "--validation",
        default="ci-artifacts/profile-validation.json",
        help="Path to validation output JSON.",
    )
    parser.add_argument("--output", default="ci-artifacts/profile-attestation.json")
    parser.add_argument("--source", default="ci-dry-run")
    parser.add_argument(
        "--resolution",
        default="ci-artifacts/profile-resolution.json",
        help="Path to profile resolution JSON output.",
    )
    parser.add_argument("--iso-path", default="", help="Built ISO path for digest binding.")
    parser.add_argument("--manifest-path", default="", help="Artifact manifest path for digest binding.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _profile_path(repo_root: Path, profiles_root: str, profile_id: str) -> Path:
    if profile_id.endswith(".yaml"):
        return repo_root / profiles_root / profile_id
    return repo_root / profiles_root / f"{profile_id}.yaml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    profile_path = _profile_path(repo_root, args.profiles_root, args.profile)
    validation_path = repo_root / args.validation
    resolution_path = repo_root / args.resolution
    output_path = repo_root / args.output
    iso_path = Path(args.iso_path) if args.iso_path else None
    manifest_path = Path(args.manifest_path) if args.manifest_path else None

    validation = {}
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
    resolution = {}
    if resolution_path.exists():
        resolution = json.loads(resolution_path.read_text(encoding="utf-8"))

    if iso_path and not iso_path.is_absolute():
        iso_path = repo_root / iso_path
    if manifest_path and not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path

    iso_sha256 = _sha256(iso_path) if iso_path and iso_path.exists() else ""
    manifest_sha256 = _sha256(manifest_path) if manifest_path and manifest_path.exists() else ""
    if args.dry_run:
        binding_status = "not-applicable-dry-run"
    elif iso_sha256 and manifest_sha256:
        binding_status = "bound"
    elif iso_sha256:
        binding_status = "iso-bound"
    else:
        binding_status = "pending"

    profile_exists = profile_path.exists()
    attestation = {
        "version": "forge-attestation.v0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": args.source,
        "dry_run": args.dry_run,
        "profile": {
            "id": args.profile,
            "path": str(profile_path.relative_to(repo_root)) if profile_exists else str(profile_path),
            "exists": profile_exists,
            "sha256": _sha256(profile_path) if profile_exists else "",
        },
        "validation": {
            "path": str(validation_path.relative_to(repo_root)) if validation_path.exists() else str(validation_path),
            "status": validation.get("status", "unknown"),
            "mode": validation.get("mode", "unknown"),
        },
        "resolution": {
            "path": str(resolution_path.relative_to(repo_root)) if resolution_path.exists() else str(resolution_path),
            "profile_id": resolution.get("profile_id", args.profile),
            "source": resolution.get("source", "unknown"),
            "profile_path": resolution.get("profile_path", str(profile_path)),
        },
        "artifact_binding": {
            "iso_path": str(iso_path) if iso_path else "",
            "iso_sha256": iso_sha256,
            "manifest_path": str(manifest_path) if manifest_path else "",
            "manifest_sha256": manifest_sha256,
            "binding_status": binding_status,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(attestation, indent=2) + "\n", encoding="utf-8")
    print(
        "Forge profile attestation:"
        f" profile={args.profile}, dry_run={args.dry_run}, output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
