"""Append-only ledger for IdentityObject snapshots (CRK-T5 replay)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.continuity.identity_object import IdentityObject


@dataclass(slots=True)
class IdentityHistoryRecord:
    id: str
    timestamp: str
    epoch: int
    kernel_version: int
    reason: str
    identity: dict[str, object]


class IdentityHistoryLedger:
    """Process-local identity snapshot store."""

    def __init__(self) -> None:
        self._rows: list[IdentityHistoryRecord] = []
        self._counter = 0

    def append(
        self,
        *,
        identity: IdentityObject,
        epoch: int,
        kernel_version: int = 1,
        reason: str = "epoch-snapshot",
    ) -> IdentityHistoryRecord:
        self._counter += 1
        rec = IdentityHistoryRecord(
            id=f"IDH-{self._counter:05d}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            epoch=epoch,
            kernel_version=kernel_version,
            reason=reason,
            identity=identity.to_dict(),
        )
        self._rows.append(rec)
        return rec

    def list(self) -> list[IdentityHistoryRecord]:
        return list(self._rows)

    def clear(self) -> None:
        self._rows.clear()
        self._counter = 0


_SHARED_IDENTITY_LEDGER = IdentityHistoryLedger()


def reset_identity_ledger() -> None:
    _SHARED_IDENTITY_LEDGER.clear()


def shared_identity_ledger() -> IdentityHistoryLedger:
    return _SHARED_IDENTITY_LEDGER
