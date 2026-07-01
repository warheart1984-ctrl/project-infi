from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from typing import Any

from skillzmcgee.governance.validator import MinimalValidator


class ContinuityLedger:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, entry: dict[str, Any]) -> str:
        self._entries.append(deepcopy(entry))
        return str(entry["id"])

    def all(self) -> list[dict[str, Any]]:
        return deepcopy(self._entries)

    def by_id(self, entry_id: str) -> dict[str, Any] | None:
        return next((entry for entry in self.all() if entry["id"] == entry_id), None)


class ValidatedLedger(ContinuityLedger):
    def __init__(self, validator: MinimalValidator) -> None:
        super().__init__()
        self.validator = validator

    def append(self, entry: dict[str, Any]) -> str:
        self.validator.validate_entry(entry)
        return super().append(entry)


class FileContinuityLedger(ValidatedLedger):
    def __init__(self, path: str | Path, validator: MinimalValidator) -> None:
        self.path = Path(path)
        super().__init__(validator)
        self._load()

    def append(self, entry: dict[str, Any]) -> str:
        self.validator.validate_entry(entry)
        stored_entry = deepcopy(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(stored_entry, sort_keys=True, separators=(",", ":")))
            stream.write("\n")
        self._entries.append(stored_entry)
        return str(entry["id"])

    def _load(self) -> None:
        if not self.path.exists():
            return
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            entry = json.loads(line)
            try:
                self.validator.validate_entry(entry)
            except ValueError as exc:
                raise ValueError(f"invalid receipt at {self.path}:{line_number}: {exc}") from exc
            self._entries.append(entry)


class SQLiteContinuityLedger(ValidatedLedger):
    def __init__(self, path: str | Path, validator: MinimalValidator) -> None:
        self.path = Path(path)
        super().__init__(validator)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._load()

    def append(self, entry: dict[str, Any]) -> str:
        self.validator.validate_entry(entry)
        stored_entry = deepcopy(entry)
        payload = json.dumps(stored_entry, sort_keys=True, separators=(",", ":"))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO receipts (id, timestamp, actor, slice, status, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(stored_entry["id"]),
                    str(stored_entry["timestamp"]),
                    str(stored_entry["actor"]),
                    str(stored_entry["slice"]),
                    str(stored_entry["status"]),
                    payload,
                ),
            )
        self._entries.append(stored_entry)
        return str(entry["id"])

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    slice TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_receipts_slice ON receipts(slice)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_receipts_timestamp ON receipts(timestamp)"
            )

    def _load(self) -> None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM receipts ORDER BY rowid ASC"
            ).fetchall()
        for row_number, (payload,) in enumerate(rows, start=1):
            entry = json.loads(payload)
            try:
                self.validator.validate_entry(entry)
            except ValueError as exc:
                raise ValueError(f"invalid receipt at {self.path}:row {row_number}: {exc}") from exc
            self._entries.append(entry)
