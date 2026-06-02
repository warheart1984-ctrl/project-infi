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
