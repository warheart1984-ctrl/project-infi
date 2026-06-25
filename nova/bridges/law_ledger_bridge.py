"""Law events, laws, proofs → SQLite (src.continuity.law_ledger)."""

from __future__ import annotations

import re
from typing import Iterable, Optional

from src.continuity.law_ledger import LawLedgerEntryType, LawLedgerStore
from src.continuity.law_ledger import LawRecord as SrcLawRecord
from src.continuity.law_ledger import LawStatus as SrcLawStatus

from nova.law_kernel.models import LawRecord as NovaLawRecord
from nova.law_kernel.models import LawStatus as NovaLawStatus
from nova.law_kernel.types import LawEvent, LawId, LawRecord, law_record_from_src

_STORE: LawLedgerStore | None = None
_NOVA_INTRODUCER = "nova"


def _store() -> LawLedgerStore:
    global _STORE
    if _STORE is None:
        _STORE = LawLedgerStore()
    return _STORE


def reset_law_ledger_store(store: LawLedgerStore | None = None) -> None:
    """Test hook — replace the shared SQLite store."""
    global _STORE
    _STORE = store


def _epoch_to_int(epoch: str) -> int:
    match = re.search(r"EPOCH:(\d+)", epoch)
    if match:
        return int(match.group(1))
    if epoch.isdigit():
        return int(epoch)
    return 0


def _epoch_from_int(value: int) -> str:
    return f"EPOCH:{value}:T0"


def _nova_status_to_src(status: NovaLawStatus) -> SrcLawStatus:
    mapping = {
        NovaLawStatus.ADMITTED: SrcLawStatus.ADMITTED,
        NovaLawStatus.EXPERIMENTAL: SrcLawStatus.EXPERIMENTAL,
        NovaLawStatus.REVOKED: SrcLawStatus.REVOKED,
    }
    return mapping.get(status, SrcLawStatus.EXPERIMENTAL)


def nova_to_src_law(record: NovaLawRecord) -> SrcLawRecord:
    return SrcLawRecord(
        law_id=record.code,
        version="1.0.0",
        law_hash=record.proof_ref or f"hash_{record.code}",
        spec_ref=record.text,
        status=_nova_status_to_src(record.status),
        created_at_epoch=_epoch_to_int(record.epoch),
        introduced_by=_NOVA_INTRODUCER,
        current_fitness=record.fitness,
        domains=list(record.domains),
    )


def persist_nova_law(record: NovaLawRecord, *, entry_type: str = "LAW_EVAL") -> None:
    """Write-through cache: upsert law record and append ledger entry."""
    src_record = nova_to_src_law(record)
    _store().upsert_law_record(src_record)
    record_law_event(
        LawEvent(
            entry_type=entry_type,
            law_id=record.code,
            law_hash=src_record.law_hash,
            epoch=_epoch_to_int(record.epoch),
            payload=record.to_dict(),
            signed_by=_NOVA_INTRODUCER,
        )
    )


def list_cached_laws() -> list[LawRecord]:
    """Hydrate Nova law records introduced by the Nova kernel."""
    rows: list[LawRecord] = []
    for src_row in _store().all_laws():
        if src_row.introduced_by != _NOVA_INTRODUCER:
            continue
        payload = src_row.to_dict()
        payload["created_at_epoch"] = _epoch_from_int(src_row.created_at_epoch)
        rows.append(law_record_from_src(payload))
    return rows


def record_law_event(event: LawEvent) -> None:
    """Persist a law event into the SQLite ledger (src)."""
    entry_type = LawLedgerEntryType(event.entry_type)
    _store().append_law_ledger_entry(
        entry_type=entry_type,
        law_id=event.law_id,
        law_hash=event.law_hash,
        epoch=event.epoch,
        payload=dict(event.payload),
        signed_by=event.signed_by,
        entry_id=event.entry_id,
    )


def get_law_history(law_id: LawId) -> Iterable[LawRecord]:
    """Fetch ledger entries for a given law from src."""
    for entry in _store().ledger_entries():
        if entry.law_id == str(law_id):
            yield law_record_from_src(
                {
                    "law_id": entry.law_id,
                    "law_hash": entry.law_hash,
                    "epoch": _epoch_from_int(entry.epoch),
                    "entry_type": entry.entry_type.value,
                    "payload": entry.payload,
                    "timestamp": entry.timestamp,
                }
            )


def get_latest_law_snapshot(law_id: LawId) -> Optional[LawRecord]:
    """Return the latest law record for a law, if any."""
    row = _store().get_law_record(str(law_id))
    if row is None:
        return None
    payload = row.to_dict()
    payload["created_at_epoch"] = _epoch_from_int(row.created_at_epoch)
    return law_record_from_src(payload)
