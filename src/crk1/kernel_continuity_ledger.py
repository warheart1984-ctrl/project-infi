"""Kernel Continuity Ledger — KΩ.5 append-only record of kernel exposure events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

LedgerEntryKind = Literal[
    "cf_event",
    "kernel_challenge",
    "deliberation",
    "invariant_added",
    "invariant_retired",
    "kernel_epoch_transition",
]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class KernelContinuityLedgerEntry:
    """Single append-only ledger row."""

    entry_id: str
    kind: LedgerEntryKind
    epoch: int
    ref_id: str
    summary: str
    created_at: str = field(default_factory=_now_iso)
    links: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "kind": self.kind,
            "epoch": self.epoch,
            "ref_id": self.ref_id,
            "summary": self.summary,
            "created_at": self.created_at,
            "links": dict(self.links),
        }


@dataclass
class KernelContinuityLedger:
    """
    KΩ.5 — links CF-events, challenges, deliberations, and invariant lifecycle.

    All kernel mutations must be logged here before they take effect.
    """

    entries: list[KernelContinuityLedgerEntry] = field(default_factory=list)
    _counter: int = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter:04d}"

    def append(
        self,
        *,
        kind: LedgerEntryKind,
        epoch: int,
        ref_id: str,
        summary: str,
        links: dict[str, Any] | None = None,
    ) -> KernelContinuityLedgerEntry:
        entry = KernelContinuityLedgerEntry(
            entry_id=self._next_id("KCL"),
            kind=kind,
            epoch=epoch,
            ref_id=ref_id,
            summary=summary,
            links=links or {},
        )
        self.entries.append(entry)
        return entry

    def record_cf_event(
        self,
        *,
        cf_event_id: str,
        epoch: int,
        description: str,
        receipt_ids: list[str] | None = None,
    ) -> KernelContinuityLedgerEntry:
        return self.append(
            kind="cf_event",
            epoch=epoch,
            ref_id=cf_event_id,
            summary=description,
            links={"receipt_ids": list(receipt_ids or [])},
        )

    def record_challenge(self, *, kcr_id: str, epoch: int, challenge_id: str) -> KernelContinuityLedgerEntry:
        return self.append(
            kind="kernel_challenge",
            epoch=epoch,
            ref_id=kcr_id,
            summary=f"Kernel challenge {challenge_id} recorded",
            links={"challenge_id": challenge_id},
        )

    def record_epoch_transition(
        self,
        *,
        old_kernel_id: str,
        new_kernel_id: str,
        epoch: int,
        kcr_id: str,
    ) -> KernelContinuityLedgerEntry:
        return self.append(
            kind="kernel_epoch_transition",
            epoch=epoch,
            ref_id=new_kernel_id,
            summary=f"Kernel epoch transition {old_kernel_id} → {new_kernel_id}",
            links={"old_kernel_id": old_kernel_id, "kcr_id": kcr_id},
        )

    def to_dict(self) -> dict[str, Any]:
        return {"entries": [entry.to_dict() for entry in self.entries]}
