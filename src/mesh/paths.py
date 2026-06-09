"""Path helpers for mesh store files (flat under mesh_data_dir)."""

from __future__ import annotations

from pathlib import Path

from src.mesh.runtime import mesh_data_dir


def mesh_dir(base_dir: str | Path | None = None) -> Path:
    if base_dir is not None:
        p = Path(base_dir)
        if p.name == "mesh" or (p / "node_identity.json").exists():
            return p
    return mesh_data_dir()
