"""Meaning Ledger — encoded rationale, boundaries, and non-binding metadata."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class MeaningEntryKind(str, Enum):
    RATIONALE = "rationale"
    BOUNDARY = "boundary"
    DRIFT_CONTAINMENT = "drift_containment"
    CONTINUITY_FREEZE = "continuity_freeze"
    EMOTIONAL_METADATA = "emotional_metadata"
    POLICY = "policy"
    BACKFILL = "backfill"


@dataclass
class MeaningLedgerEntry:
    entry_id: str
    kind: MeaningEntryKind
    title: str
    body: str
    lineage: list[str] = field(default_factory=list)
    law_surfaces: list[str] = field(default_factory=list)
    binding: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "kind": self.kind.value,
            "title": self.title,
            "body": self.body,
            "lineage": list(self.lineage),
            "law_surfaces": list(self.law_surfaces),
            "binding": self.binding,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> MeaningLedgerEntry:
        return cls(
            entry_id=str(row["entry_id"]),
            kind=MeaningEntryKind(str(row["kind"])),
            title=str(row["title"]),
            body=str(row["body"]),
            lineage=[str(item) for item in row.get("lineage") or []],
            law_surfaces=[str(item) for item in row.get("law_surfaces") or []],
            binding=bool(row.get("binding", True)),
            metadata=dict(row.get("metadata") or {}),
            created_at=str(row.get("created_at") or ""),
        )


def default_meaning_ledger_path() -> Path:
    override = os.environ.get("MEANING_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "meaning-ledger.jsonl"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "meaning-ledger.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class MeaningLedger:
    """Append-only meaning ledger with idempotent upsert by entry_id."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_meaning_ledger_path()
        self._entries: dict[str, MeaningLedgerEntry] = {}
        if self.path.is_file():
            self._load()

    def append(self, entry: MeaningLedgerEntry) -> MeaningLedgerEntry:
        if not entry.created_at:
            entry.created_at = _now_iso()
        self._entries[entry.entry_id] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), sort_keys=True) + "\n")
        return entry

    def get(self, entry_id: str) -> MeaningLedgerEntry | None:
        return self._entries.get(entry_id)

    def all(self) -> list[MeaningLedgerEntry]:
        return list(self._entries.values())

    def _load(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            entry = MeaningLedgerEntry.from_dict(json.loads(cleaned))
            self._entries[entry.entry_id] = entry
