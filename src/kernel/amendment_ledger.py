"""Append-only ledger for CRK-2 kernel amendment proposals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(slots=True)
class KernelAmendmentRecord:
    id: str
    timestamp: str
    kernel_version: int
    insufficiency: float
    signals: list[float]
    reason: str
    ratified: bool


class AmendmentStore(Protocol):
    def next_id(self) -> str: ...

    def append(self, row: dict[str, Any]) -> None: ...

    def read_all(self) -> list[dict[str, Any]]: ...


class InMemoryAmendmentStore:
    """Process-local amendment ledger backend."""

    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []
        self._counter = 0

    def next_id(self) -> str:
        self._counter += 1
        return f"KAM-{self._counter:05d}"

    def append(self, row: dict[str, Any]) -> None:
        self._rows.append(dict(row))

    def read_all(self) -> list[dict[str, Any]]:
        return list(self._rows)


class KernelAmendmentLedger:
    """Simple append-only ledger for CRK-2 proposals."""

    def __init__(self, store: AmendmentStore) -> None:
        self.store = store

    def append(
        self,
        kernel_version: int,
        insufficiency: float,
        signals: list[float],
        reason: str,
        ratified: bool,
    ) -> KernelAmendmentRecord:
        rec = KernelAmendmentRecord(
            id=self.store.next_id(),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            kernel_version=kernel_version,
            insufficiency=insufficiency,
            signals=list(signals),
            reason=reason,
            ratified=ratified,
        )
        self.store.append(asdict(rec))
        return rec

    def list(self) -> list[KernelAmendmentRecord]:
        return [KernelAmendmentRecord(**row) for row in self.store.read_all()]
