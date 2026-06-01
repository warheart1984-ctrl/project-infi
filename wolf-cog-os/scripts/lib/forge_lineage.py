"""Forge reproducible lineage computation (P7)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


LINEAGE_SCHEMA = "forge-lineage.v1"


def git_commit_short(repo_root: Path | None = None) -> str:
    import subprocess

    root = repo_root or Path.cwd()
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except Exception:
        return ""


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_lineage_id(components: dict[str, Any]) -> str:
    material = dict(components)
    for key in ("lineage_id", "generated_at", "lineage_hash_alg", "build_host"):
        material.pop(key, None)
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def build_lineage_record(
    *,
    pipeline_name: str,
    variant_id: str,
    profile_id: str,
    substrate_id: str = "auto",
    rootfs_backend: str = "debootstrap",
    replay_adapter: str = "",
    package_sets: list[str] | None = None,
    target_arch: str = "amd64",
    reproducibility_seed: str = "",
    parent_lineage_id: str = "",
    cogos_tag: str = "",
    pipeline_path: str = "",
    git_commit: str = "",
    build_host: str = "",
) -> dict[str, Any]:
    package_sets = sorted(package_sets or [])
    components = {
        "schema_version": LINEAGE_SCHEMA,
        "pipeline_name": pipeline_name,
        "variant_id": variant_id,
        "profile_id": profile_id,
        "substrate_id": substrate_id,
        "rootfs_backend": rootfs_backend,
        "replay_adapter": replay_adapter,
        "package_sets": package_sets,
        "target_arch": target_arch,
        "reproducibility_seed": reproducibility_seed,
        "parent_lineage_id": parent_lineage_id,
        "cogos_tag": cogos_tag,
        "pipeline_path": pipeline_path,
        "git_commit": git_commit,
        "build_host": build_host,
    }
    lineage_id = compute_lineage_id(components)
    return {
        **components,
        "lineage_id": lineage_id,
        "lineage_hash_alg": "sha256-canonical-json-v1",
    }
