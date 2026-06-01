from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.evolving_workbench import EvolvingWorkspaceIntel
from src.jarvis_types import ChangeImpact


def _unique(values: list[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
        if limit is not None and len(ordered) >= limit:
            break
    return ordered


def _risk_level(affected_files: list[str], recommended_tests: list[str]) -> str:
    score = len(affected_files)
    if any(path.endswith("/src/api.py") or path.endswith("api.py") for path in affected_files):
        score += 2
    if any("/frontend/src/pages/" in path.replace("\\", "/") for path in affected_files):
        score += 1
    if not recommended_tests and affected_files:
        score += 1
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


class ChangeScope:
    """Translate repo-map awareness into impact judgment."""

    def __init__(self, workspace_intel: EvolvingWorkspaceIntel):
        self.workspace_intel = workspace_intel

    def analyze_file_impact(
        self,
        *,
        file_path: str | None = None,
        symbol: str | None = None,
        goal: str | None = None,
        path_prefix: str | None = None,
    ) -> dict[str, Any]:
        focus_path = str(file_path or "").strip() or None
        if not focus_path and symbol:
            try:
                symbol_payload = self.workspace_intel.read_symbol(symbol=symbol, path_prefix=path_prefix)
                focus_path = str((symbol_payload.get("symbol") or {}).get("path") or "").strip() or None
            except FileNotFoundError:
                focus_path = None

        repo_map = self.workspace_intel.inspect_repo_map(
            goal=goal,
            focus_path=focus_path,
            symbol=symbol,
            path_prefix=path_prefix,
        )
        affected_files = _unique(
            [*(repo_map.get("focus_paths") or []), *(repo_map.get("related_paths") or [])],
            limit=12,
        )
        symbol_query = symbol or (Path(focus_path).stem if focus_path else "")
        symbol_hits = []
        if symbol_query:
            symbol_hits = (self.workspace_intel.list_symbols(
                query=symbol_query,
                limit=12,
                path_prefix=path_prefix,
            ) or {}).get("symbols", [])
        recommended_tests = _unique(list(repo_map.get("likely_test_files") or []), limit=8)
        seams = []
        for path in (repo_map.get("related_paths") or [])[:6]:
            seams.append(
                {
                    "path": path,
                    "reason": "linked through the focused repo map",
                    "kind": "test" if "/tests/" in f"/{path}/" or Path(path).name.startswith("test_") else "integration",
                }
            )
        impact = ChangeImpact(
            impact_id=f"impact_{uuid4().hex}",
            focus_path=focus_path or ((repo_map.get("focus_paths") or [None])[0]),
            symbol=symbol,
            affected_files=affected_files,
            affected_symbols=symbol_hits[:8],
            recommended_tests=recommended_tests,
            risk_level=_risk_level(affected_files, recommended_tests),
            integration_seams=seams,
            repo_map=repo_map,
            summary=(
                f"ChangeScope found {len(affected_files)} affected files and "
                f"{len(recommended_tests)} likely tests."
            ),
        )
        return impact.to_dict()
