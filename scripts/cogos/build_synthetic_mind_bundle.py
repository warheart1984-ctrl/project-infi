#!/usr/bin/env python3
"""Build portable Synthetic Mind bundle from canonical src/cog_runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE_DIR = REPO_ROOT / "artifacts" / "synthetic-mind-bundle"

BRIDGE_MODULES = (
    "cogos_runtime_bridge.py",
    "aais_composed_runtime.py",
    "aais_ul.py",
    "aais_ul_substrate.py",
    "direct_challenge_module.py",
    "jarvis_reasoning_protocol.py",
    "jarvis_types.py",
    "reasoning_types.py",
)

SKIP_DIR_NAMES = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def _repo_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _should_skip(path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    return path.suffix in SKIP_SUFFIXES


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.rglob("*")):
        if _should_skip(item):
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _collect_bundle_files(bundle_dir: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "synthetic_mind_manifest.json":
            continue
        rel = path.relative_to(bundle_dir).as_posix()
        entries.append({"relative_path": rel, "sha256": _sha256_file(path)})
    return entries


def _bundle_sha256(files: list[dict[str, str]]) -> str:
    payload = "\n".join(f"{item['relative_path']}:{item['sha256']}" for item in files)
    return _sha256_bytes(payload.encode("utf-8"))


def build_bundle(bundle_dir: Path) -> Path:
    _repo_on_path()
    from src.cog_runtime import export_family_json, nova_cortex_spec
    from src.cog_runtime.spark_pipeline import SPARK_PIPELINE_ID

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    runtime_src = bundle_dir / "opt" / "cogos" / "runtime" / "src"
    runtime_src.mkdir(parents=True, exist_ok=True)

    _copy_tree(REPO_ROOT / "src" / "cog_runtime", runtime_src / "cog_runtime")

    for module in BRIDGE_MODULES:
        src = REPO_ROOT / "src" / module
        if src.is_file():
            shutil.copy2(src, runtime_src / module)

    speaking_src = REPO_ROOT / "src" / "speaking_runtime"
    if speaking_src.is_dir():
        _copy_tree(speaking_src, runtime_src / "speaking_runtime")

    (runtime_src / "__init__.py").touch(exist_ok=True)

    family_path = bundle_dir / "opt" / "cogos" / "config" / "cognitive_runtime_family.json"
    export_family_json(family_path)

    spec = nova_cortex_spec()
    files = _collect_bundle_files(bundle_dir)
    bundle_hash = _bundle_sha256(files)
    build_id = os.environ.get("COGOS_AI_FACTORY_BUILD_ID", "").strip()

    manifest: dict[str, object] = {
        "bundle_version": "synthetic_mind_bundle.v1",
        "family_id": spec["family_id"],
        "family_version": str(spec.get("version") or ""),
        "spark_pipeline_id": SPARK_PIPELINE_ID,
        "claim_posture": "asserted",
        "built_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "bundle_root": bundle_dir.as_posix(),
        "bundle_sha256": bundle_hash,
        "files": files,
        "required_modules": [
            "cog_runtime/coherence_projection.py",
            "cog_runtime/spark_pipeline.py",
            "cog_runtime/formal/spine_pipeline.py",
        ],
    }
    if build_id:
        manifest["ai_factory_build_id"] = build_id

    manifest_path = bundle_dir / "synthetic_mind_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Synthetic Mind bundle from src/cog_runtime.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=str(DEFAULT_BUNDLE_DIR),
        help=f"Bundle output directory (default: {DEFAULT_BUNDLE_DIR})",
    )
    args = parser.parse_args()

    bundle_dir = Path(args.output_dir).expanduser().resolve()
    manifest_path = build_bundle(bundle_dir)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
