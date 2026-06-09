"""Runtime directory for mesh state under AAIS .runtime/mesh."""

from __future__ import annotations

import os
from pathlib import Path

_mesh_dir_override: Path | None = None


def mesh_data_dir() -> Path:
    if _mesh_dir_override is not None:
        return _mesh_dir_override
    try:
        from src.temporal_replay.paths import default_runtime_dir

        base = default_runtime_dir()
    except Exception:
        base = Path(
            os.environ.get("AAIS_RUNTIME_DIR")
            or os.environ.get("PROJECT_INFI_RUNTIME", ".runtime")
        )
    path = Path(base) / "mesh"
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_mesh_dir(path: Path | str | None) -> None:
    global _mesh_dir_override
    if path is None:
        _mesh_dir_override = None
        return
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    _mesh_dir_override = p


def mesh_base() -> str:
    return str(mesh_data_dir())
