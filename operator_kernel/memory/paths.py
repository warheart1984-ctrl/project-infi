"""Resolve memory storage paths under %USERPROFILE%\\.operator."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryPaths:
    root: Path
    semantic: Path
    lsg: Path
    tasks: Path | None = None


def _user_operator_root() -> Path:
    profile = os.environ.get("USERPROFILE") or os.environ.get("HOME") or "."
    return Path(profile).expanduser() / ".operator"


def memory_paths(tasks_dir: Path | None = None) -> MemoryPaths:
    root = Path(os.environ.get("OPERATOR_MEMORY_ROOT", str(_user_operator_root()))).expanduser()
    config_path = Path(os.environ.get("OPERATOR_MEMORY_CONFIG", "")).expanduser()
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            root = Path(str(data.get("root") or root)).expanduser()
        except (json.JSONDecodeError, OSError):
            pass
    semantic = Path(os.environ.get("OPERATOR_SEMANTIC_STORE", str(root / "memory" / "semantic.jsonl")))
    lsg = Path(os.environ.get("NOVA_LSG_STORE", str(root / "lsg")))
    return MemoryPaths(root=root, semantic=semantic, lsg=lsg, tasks=tasks_dir)
