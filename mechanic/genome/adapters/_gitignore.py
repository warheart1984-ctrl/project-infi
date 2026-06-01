"""Minimal .gitignore parser for scan scope."""

from __future__ import annotations

from pathlib import Path


def load_gitignore_patterns(repo_path: Path) -> list[str]:
    patterns: list[str] = []
    gitignore = repo_path / ".gitignore"
    if not gitignore.is_file():
        return patterns
    for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def path_is_ignored(rel_path: str, patterns: list[str]) -> bool:
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")
    for pattern in patterns:
        pat = pattern.rstrip("/")
        if pat.startswith("!"):
            continue
        if pat.endswith("/"):
            if any(part == pat[:-1] for part in parts):
                return True
        elif "*" in pat:
            if pat.replace("*", "") in normalized:
                return True
        elif normalized == pat or normalized.startswith(pat + "/"):
            return True
        elif any(part == pat for part in parts):
            return True
    return False
