#!/usr/bin/env python3
"""Emit forge-build-state.json evidence for CI and local runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit Forge build state evidence JSON.")
    parser.add_argument("--profile", default=os.environ.get("COGOS_FORGE_PROFILE", "forge-selfhosted"))
    parser.add_argument("--rootfs", default="")
    parser.add_argument("--iso", default="")
    parser.add_argument("--resolution", default="ci-artifacts/profile-resolution.json")
    parser.add_argument("--validation", default="ci-artifacts/profile-validation.json")
    parser.add_argument("--attestation", default="ci-artifacts/profile-attestation.json")
    parser.add_argument("--pipeline", default=os.environ.get("COGOS_FORGE_PIPELINE", "wolf-cog-os/forge/pipelines/daily-driver.yaml"))
    parser.add_argument("--rootfs-backend", default=os.environ.get("COGOS_ROOTFS_BACKEND", "debootstrap"))
    parser.add_argument("--replay-adapter", default=os.environ.get("COGOS_REPLAY_ADAPTER", ""))
    parser.add_argument("--substrate-validation", default="ci-artifacts/substrate-validation.json")
    parser.add_argument("--lineage", default="ci-artifacts/forge-lineage.json")
    parser.add_argument("--emit-lineage", action="store_true", help="Emit forge-lineage.json before build state.")
    parser.add_argument("--output", default="ci-artifacts/forge-build-state.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rootfs_path = Path(args.rootfs) if args.rootfs else None
    iso_path = Path(args.iso) if args.iso else None
    lineage_path = repo_root / args.lineage

    tag = os.environ.get("COGOS_TAG", "")
    replay_adapter = args.replay_adapter.strip()
    substrate_validation = repo_root / args.substrate_validation
    if not replay_adapter and substrate_validation.is_file():
        try:
            replay_adapter = str(
                json.loads(substrate_validation.read_text(encoding="utf-8")).get("replay_adapter", "")
            ).strip()
        except json.JSONDecodeError:
            replay_adapter = ""

    if args.emit_lineage or not lineage_path.is_file():
        emit_cmd = [
            sys.executable,
            str(repo_root / "wolf-cog-os/scripts/emit-forge-lineage.py"),
            "--pipeline",
            args.pipeline,
            "--profile",
            args.profile,
            "--rootfs-backend",
            args.rootfs_backend,
            "--output",
            str(lineage_path.relative_to(repo_root)),
        ]
        if replay_adapter:
            emit_cmd.extend(["--replay-adapter", replay_adapter])
        if tag:
            emit_cmd.extend(["--cogos-tag", tag])
        subprocess.run(emit_cmd, cwd=str(repo_root), check=False)

    lineage_id = ""
    if lineage_path.is_file():
        try:
            lineage_payload = json.loads(lineage_path.read_text(encoding="utf-8"))
            lineage_id = str(lineage_payload.get("lineage_id", ""))
        except json.JSONDecodeError:
            lineage_id = ""

    forge_layout_ok = False
    if rootfs_path and rootfs_path.is_dir():
        required = [
            rootfs_path / "forge/pipelines/minimal.yaml",
            rootfs_path / "usr/local/bin/forge-menu",
        ]
        forge_layout_ok = all(p.exists() for p in required)

    state = {
        "schema_version": "forge-build-state.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_id": args.profile,
        "lineage_id": lineage_id,
        "pipeline": args.pipeline,
        "forge_layout_ok": forge_layout_ok,
        "host": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "inputs": {
            "rootfs": str(rootfs_path) if rootfs_path else "",
            "iso": str(iso_path) if iso_path else "",
        },
        "artifacts": {},
        "tool_versions": {},
    }

    for label, cmd in (
        ("make", ["make", "--version"]),
        ("xorriso", ["xorriso", "-version"]),
        ("mksquashfs", ["mksquashfs", "-version"]),
    ):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
            state["tool_versions"][label] = (proc.stdout or proc.stderr or "").splitlines()[0][:200]
        except Exception as exc:  # noqa: BLE001 - evidence capture only
            state["tool_versions"][label] = f"unavailable: {exc}"

    for key, rel in (
        ("profile_resolution", args.resolution),
        ("profile_validation", args.validation),
        ("profile_attestation", args.attestation),
        ("forge_lineage", args.lineage),
    ):
        path = repo_root / rel
        if path.is_file():
            state["artifacts"][key] = {
                "path": str(path),
                "sha256": sha256_file(path),
            }

    if iso_path and iso_path.is_file():
        state["artifacts"]["iso"] = {
            "path": str(iso_path),
            "sha256": sha256_file(iso_path),
            "size_bytes": iso_path.stat().st_size,
        }

    if rootfs_path and rootfs_path.is_dir():
        state["artifacts"]["rootfs"] = {
            "path": str(rootfs_path),
            "forge_layout_ok": forge_layout_ok,
        }

    output_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"forge build state written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
