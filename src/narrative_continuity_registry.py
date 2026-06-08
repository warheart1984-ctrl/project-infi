"""Operator narrative beat registry loader (Stage 7 / Release 38)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BEAT_VERSION = "operator_narrative_beat.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_narrative_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_narrative_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_beats(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_narrative_registry(repo_root=repo_root)
    return list(doc.get("beats") or [])


def save_adopted_beat(beat: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_narrative_registry.v1.json"
    doc = load_narrative_registry(repo_root=root)
    beats = list(doc.get("beats") or [])
    beat_id = str(beat.get("beat_id") or "")
    beats = [b for b in beats if str(b.get("beat_id") or "") != beat_id]
    beats.append(beat)
    doc["beats"] = beats
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return beat


def validate_narrative_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_narrative_registry(repo_root=repo_root)
    if doc.get("operator_narrative_registry_version") != "operator_narrative_registry.v1":
        errors.append("invalid operator_narrative_registry_version")
    for beat in list(doc.get("beats") or []):
        beat_id = str(beat.get("beat_id") or "")
        if not beat_id:
            errors.append("beat missing beat_id")
        if beat.get("beat_version") != BEAT_VERSION:
            errors.append(f"invalid beat_version on {beat_id}")
        if not beat.get("operator_promoted"):
            errors.append(f"registry beat must be operator_promoted: {beat_id}")
        kind = str(beat.get("beat_kind") or "")
        if kind not in {"chapter", "thread", "promise_closure", "arc"}:
            errors.append(f"invalid beat_kind on {beat_id}")
    return errors
