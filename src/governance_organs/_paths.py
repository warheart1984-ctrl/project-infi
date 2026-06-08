"""Repository path resolution for Alt-4 governance organs."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    configured = os.getenv("AAIS_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def runtime_governance_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        base = Path(configured).expanduser() / "governance"
    else:
        base = repo_root() / ".runtime" / "governance"
    base.mkdir(parents=True, exist_ok=True)
    return base


def list_gene_backups(backup_dir: Path, gene: str, *, suffix: str = ".genome.v1.json") -> list[Path]:
    """Return sorted backups for ``gene``, excluding longer gene prefix collisions."""
    prefix = f"{gene}_"
    matches: list[Path] = []
    for path in backup_dir.glob(f"{gene}_*{suffix}"):
        remainder = path.name[len(prefix) :]
        if not remainder or not remainder[0].isdigit():
            continue
        matches.append(path)
    return sorted(matches)
