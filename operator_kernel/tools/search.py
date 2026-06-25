"""Code search (ripgrep with Python fallback)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from operator_kernel.tools.workspace import IGNORE_DIRS


def search_code(workspace_root: Path, query: str, max_results: int = 50) -> dict:
    max_results = max(1, min(int(max_results), 200))
    if shutil.which("rg"):
        return _search_rg(workspace_root, query, max_results)
    return _search_python(workspace_root, query, max_results)


def _search_rg(workspace_root: Path, query: str, max_results: int) -> dict:
    completed = subprocess.run(
        ["rg", "--line-number", "--no-heading", "--max-count", str(max_results), query, "."],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    hits = [line for line in completed.stdout.splitlines() if line.strip()]
    return {"engine": "rg", "query": query, "hits": hits[:max_results], "count": len(hits)}


def _search_python(workspace_root: Path, query: str, max_results: int) -> dict:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    hits: list[str] = []
    for path in workspace_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(workspace_root).as_posix()
        for idx, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{rel}:{idx}:{line.strip()}")
                if len(hits) >= max_results:
                    return {"engine": "python", "query": query, "hits": hits, "count": len(hits)}
    return {"engine": "python", "query": query, "hits": hits, "count": len(hits)}
