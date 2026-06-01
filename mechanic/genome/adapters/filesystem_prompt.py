"""Scan prompt-like assets under a repo."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from mechanic.genome.adapters._gitignore import load_gitignore_patterns, path_is_ignored
from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.schema import add_edge, add_node

_PROMPT_SUFFIXES = {".md", ".mdc", ".txt", ".yaml", ".yml"}
_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".runtime",
    "venv",
    ".venv",
}
_MAX_FILE_BYTES = 512_000


class FilesystemPromptAdapter(GenomeAdapter):
    adapter_id = "filesystem_prompt"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "repo_path": str(repo_path),
            "suffixes": sorted(_PROMPT_SUFFIXES),
            "max_file_bytes": _MAX_FILE_BYTES,
        }

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        patterns = load_gitignore_patterns(repo_path)
        found = 0
        for path in sorted(repo_path.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_path).as_posix()
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if ".cursor" in path.parts:
                continue
            if path_is_ignored(rel, patterns):
                continue
            if path.suffix.lower() not in _PROMPT_SUFFIXES:
                continue
            if path.stat().st_size > _MAX_FILE_BYTES:
                continue
            lower = rel.lower()
            if "prompt" not in lower and path.suffix.lower() not in {".mdc"}:
                if path.name.lower() not in {
                    "agents.md",
                    "readme.md",
                    "skill.md",
                } and not lower.endswith("/skill.md"):
                    if "system_prompt" not in lower and "/prompts/" not in lower:
                        continue
            node_id = f"prompt:{_hash_rel(rel)}"
            add_node(
                genome,
                node_id=node_id,
                node_type="prompt_asset",
                label=path.name,
                source_path=rel,
                attrs={"bytes": path.stat().st_size},
            )
            found += 1
        return {"adapter_id": self.adapter_id, "nodes_added": found}


def _hash_rel(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
