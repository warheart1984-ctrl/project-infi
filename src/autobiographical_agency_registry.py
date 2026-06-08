"""Operator autobiographical episode registry loader (Stage 8 / Release 39)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EPISODE_VERSION = "operator_autobiographical_episode.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_autobiographical_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_autobiographical_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_episodes(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_autobiographical_registry(repo_root=repo_root)
    return list(doc.get("episodes") or [])


def save_adopted_episode(episode: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_autobiographical_registry.v1.json"
    doc = load_autobiographical_registry(repo_root=root)
    episodes = list(doc.get("episodes") or [])
    episode_id = str(episode.get("episode_id") or "")
    episodes = [e for e in episodes if str(e.get("episode_id") or "") != episode_id]
    episodes.append(episode)
    doc["episodes"] = episodes
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return episode


def validate_autobiographical_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_autobiographical_registry(repo_root=repo_root)
    if doc.get("operator_autobiographical_registry_version") != "operator_autobiographical_registry.v1":
        errors.append("invalid operator_autobiographical_registry_version")
    for episode in list(doc.get("episodes") or []):
        episode_id = str(episode.get("episode_id") or "")
        if not episode_id:
            errors.append("episode missing episode_id")
        if episode.get("episode_version") != EPISODE_VERSION:
            errors.append(f"invalid episode_version on {episode_id}")
        if not episode.get("operator_promoted"):
            errors.append(f"registry episode must be operator_promoted: {episode_id}")
        kind = str(episode.get("episode_kind") or "")
        if kind not in {"ongoing_work", "commitment_arc", "operator_partnership", "closure"}:
            errors.append(f"invalid episode_kind on {episode_id}")
    return errors
