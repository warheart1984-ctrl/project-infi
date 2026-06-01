#!/usr/bin/env python3
"""Emit forge-lineage.json reproducible lineage artifact."""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SCRIPT_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from forge_lineage import LINEAGE_SCHEMA, build_lineage_record, git_commit_short  # noqa: E402
from forge_pipeline import nested_get, parse_simple_yaml  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit Forge lineage artifact.")
    parser.add_argument("--pipeline", default="wolf-cog-os/forge/pipelines/daily-driver.yaml")
    parser.add_argument("--profile", default=os.environ.get("COGOS_FORGE_PROFILE", "forge-selfhosted"))
    parser.add_argument("--substrate-id", default=os.environ.get("COGOS_SUBSTRATE_ID", "auto"))
    parser.add_argument("--rootfs-backend", default=os.environ.get("COGOS_ROOTFS_BACKEND", "debootstrap"))
    parser.add_argument("--replay-adapter", default=os.environ.get("COGOS_REPLAY_ADAPTER", ""))
    parser.add_argument("--target-arch", default=os.environ.get("COGOS_TARGET_ARCH", os.environ.get("COGOS_ARCH", "amd64")))
    parser.add_argument("--cogos-tag", default=os.environ.get("COGOS_TAG", ""))
    parser.add_argument("--git-commit", default="", help="Override git commit (default: auto-detect).")
    parser.add_argument("--build-host", default="", help="Override build host fingerprint.")
    parser.add_argument("--output", default="ci-artifacts/forge-lineage.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    pipeline_path = repo_root / args.pipeline
    spec = parse_simple_yaml(pipeline_path) if pipeline_path.is_file() else {}
    pipeline_name = nested_get(spec, "name") or pipeline_path.stem
    variant_id = nested_get(spec, "variant", "id") or pipeline_name
    seed = nested_get(spec, "reproducibility", "seed")
    parent_lineage_id = nested_get(spec, "lineage", "parent_lineage_id")
    rootfs_backend = nested_get(spec, "rootfs", "backend") or args.rootfs_backend
    packages_raw: list[str] = []
    packages = spec.get("packages", {})
    if isinstance(packages, dict):
        include = packages.get("include", [])
        if isinstance(include, list):
            packages_raw = [str(item) for item in include]

    git_commit = args.git_commit.strip() or git_commit_short(repo_root)
    build_host = args.build_host.strip() or platform.node()

    record = build_lineage_record(
        pipeline_name=pipeline_name,
        variant_id=variant_id,
        profile_id=args.profile,
        substrate_id=args.substrate_id,
        rootfs_backend=rootfs_backend,
        replay_adapter=args.replay_adapter.strip(),
        package_sets=packages_raw or ["base"],
        target_arch=args.target_arch,
        reproducibility_seed=seed,
        parent_lineage_id=parent_lineage_id,
        cogos_tag=args.cogos_tag,
        pipeline_path=str(pipeline_path.relative_to(repo_root)) if pipeline_path.is_file() else args.pipeline,
        git_commit=git_commit,
        build_host=build_host,
    )
    record["generated_at"] = datetime.now(timezone.utc).isoformat()

    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"forge lineage written: {output_path} id={record['lineage_id'][:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
