"""Rank workflow families and chains for brain proposals."""

from __future__ import annotations

import re
from typing import Any

from src.workflow_family_registry import list_workflow_families
from src.workflow_plugin_catalog import list_workflow_bundles


def _signals(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z]{3,}", text.lower())}


def score_families(text: str, *, repo_root=None) -> list[dict[str, Any]]:
    tokens = _signals(text)
    rankings: list[dict[str, Any]] = []
    for family in list_workflow_families(repo_root=repo_root):
        identity = dict(family.get("identity") or {})
        routing = dict(family.get("routing") or {})
        signals = [str(s).lower() for s in list(routing.get("intent_signals") or [])]
        matched = [s for s in signals if s in tokens]
        score = len(matched) / max(len(signals), 1)
        rankings.append(
            {
                "family_id": identity.get("family_id"),
                "display_name": identity.get("display_name"),
                "fitness_score": round(score, 2),
                "matched_signals": matched,
            }
        )
    rankings.sort(key=lambda r: (-float(r.get("fitness_score") or 0), str(r.get("family_id"))))
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank
    return rankings


def score_chains(text: str, *, repo_root=None) -> list[dict[str, Any]]:
    tokens = _signals(text)
    rankings: list[dict[str, Any]] = []
    for bundle in list_workflow_bundles(repo_root=repo_root):
        wid = str(bundle.get("workflow_id") or "")
        display = str(bundle.get("display_name") or wid)
        category = str(bundle.get("category") or "")
        hay = f"{wid} {display} {category}".lower()
        matched = [t for t in tokens if t in hay]
        score = min(1.0, len(matched) * 0.25 + (0.5 if "research" in hay and "research" in tokens else 0))
        rankings.append(
            {
                "workflow_id": wid,
                "display_name": display,
                "family_id": category,
                "fitness_score": round(score, 2),
                "matched_signals": matched,
            }
        )
    rankings.sort(key=lambda r: (-float(r.get("fitness_score") or 0), str(r.get("workflow_id"))))
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank
    return rankings
