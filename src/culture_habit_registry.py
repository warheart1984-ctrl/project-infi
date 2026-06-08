"""Operator habit registry loader (Stage 5 / Release 36)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HABIT_VERSION = "operator_habit.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_habit_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_habit_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_habits(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_habit_registry(repo_root=repo_root)
    return list(doc.get("habits") or [])


def save_adopted_habit(habit: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_habit_registry.v1.json"
    doc = load_habit_registry(repo_root=root)
    habits = list(doc.get("habits") or [])
    habit_id = str(habit.get("habit_id") or "")
    habits = [h for h in habits if str(h.get("habit_id") or "") != habit_id]
    habits.append(habit)
    doc["habits"] = habits
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return habit


def validate_habit_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_habit_registry(repo_root=repo_root)
    if doc.get("operator_habit_registry_version") != "operator_habit_registry.v1":
        errors.append("invalid operator_habit_registry_version")
    for habit in list(doc.get("habits") or []):
        habit_id = str(habit.get("habit_id") or "")
        if not habit_id:
            errors.append("habit missing habit_id")
        if habit.get("habit_version") != HABIT_VERSION:
            errors.append(f"invalid habit_version on {habit_id}")
        if not habit.get("operator_promoted"):
            errors.append(f"registry habit must be operator_promoted: {habit_id}")
        kind = str(habit.get("pattern_kind") or "")
        if kind not in {"chain", "mesh_path", "routine"}:
            errors.append(f"invalid pattern_kind on {habit_id}")
    return errors
