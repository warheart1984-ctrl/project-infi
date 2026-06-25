"""Workspace file operations."""

from __future__ import annotations

import fnmatch
from pathlib import Path

IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
    ".local-secrets",
}


def _path_matches(rel: str, pattern: str) -> bool:
    """Match workspace-relative paths; fnmatch does not treat ** as recursive."""
    pat = (pattern or "**/*").strip()
    if pat in ("**/*", "**", "*"):
        return True
    if fnmatch.fnmatchcase(rel, pat):
        return True
    name = Path(rel).name
    if fnmatch.fnmatchcase(name, pat):
        return True
    if pat.startswith("**/"):
        tail = pat[3:]
        if fnmatch.fnmatchcase(rel, tail) or fnmatch.fnmatchcase(name, tail):
            return True
    return False


class WorkspaceTools:
    def __init__(self, workspace_root: Path, gate):
        self.workspace_root = workspace_root.resolve()
        self.gate = gate

    def list_files(self, pattern: str = "**/*", max_results: int = 100) -> dict:
        max_results = max(1, min(int(max_results), 500))
        matches: list[str] = []
        for path in self.workspace_root.rglob("*"):
            try:
                if not path.is_file():
                    continue
                rel_parts = path.relative_to(self.workspace_root).parts
            except (ValueError, OSError):
                continue
            if any(part in IGNORE_DIRS for part in rel_parts):
                continue
            rel = path.relative_to(self.workspace_root).as_posix()
            if _path_matches(rel, pattern):
                matches.append(rel)
                if len(matches) >= max_results:
                    break
        matches.sort()
        nodes = [{"path": p} for p in matches]
        return {"files": matches, "nodes": nodes, "count": len(matches)}

    def read_file(self, path: str, start_line: int | None = None, end_line: int | None = None) -> dict:
        target = self.gate.resolve_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        text = target.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if start_line is not None or end_line is not None:
            start = max(1, int(start_line or 1)) - 1
            end = int(end_line) if end_line is not None else len(lines)
            lines = lines[start:end]
            text = "\n".join(lines)
        return {
            "path": path,
            "content": text,
            "line_count": len(lines),
        }
