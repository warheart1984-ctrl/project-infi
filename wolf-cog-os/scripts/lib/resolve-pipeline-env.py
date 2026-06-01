#!/usr/bin/env python3
"""Resolve Forge pipeline YAML into shell-exportable environment."""
from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from forge_pipeline import nested_get, parse_simple_yaml  # noqa: E402


def resolve_pipeline_env(pipeline_path: Path) -> dict[str, object]:
    spec = parse_simple_yaml(pipeline_path) if pipeline_path.is_file() else {}
    output = spec.get("output", {})
    cloud_formats: list[str] = []
    if isinstance(output, dict):
        include = output.get("cloud_formats", [])
        if isinstance(include, list):
            cloud_formats = [str(item) for item in include]
    return {
        "pipeline_path": str(pipeline_path),
        "pipeline_name": nested_get(spec, "name") or pipeline_path.stem,
        "variant_id": nested_get(spec, "variant", "id"),
        "substrate_id": nested_get(spec, "substrate", "id") or "auto",
        "rootfs_backend": nested_get(spec, "rootfs", "backend") or "debootstrap",
        "iso_name": nested_get(spec, "output", "iso_name"),
        "cloud_formats": cloud_formats,
        "reproducibility_seed": nested_get(spec, "reproducibility", "seed"),
    }


def emit_shell_exports(payload: dict[str, object]) -> None:
    exports = {
        "COGOS_FORGE_PIPELINE": payload["pipeline_path"],
        "COGOS_PIPELINE_NAME": payload["pipeline_name"],
        "COGOS_PIPELINE_VARIANT_ID": payload["variant_id"],
        "COGOS_SUBSTRATE_ID": payload["substrate_id"],
        "COGOS_ROOTFS_BACKEND": payload["rootfs_backend"],
        "COGOS_PIPELINE_ISO_NAME": payload["iso_name"],
        "COGOS_PIPELINE_CLOUD_FORMATS": " ".join(payload["cloud_formats"]),
        "COGOS_PIPELINE_REPRO_SEED": payload["reproducibility_seed"],
    }
    for key, value in exports.items():
        print(f"export {key}={shlex.quote(str(value))}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: resolve-pipeline-env.py <pipeline.yaml> [--json]", file=sys.stderr)
        return 2
    pipeline = Path(sys.argv[1])
    payload = resolve_pipeline_env(pipeline.resolve())
    if len(sys.argv) > 2 and sys.argv[2] == "--json":
        print(json.dumps(payload, indent=2))
        return 0
    emit_shell_exports(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
