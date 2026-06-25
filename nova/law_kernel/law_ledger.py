"""KLAW-3 — append-only LawLedger with optional SQLite write-through cache."""

from __future__ import annotations

from dataclasses import replace

from nova.law_kernel.models import LawRecord, LawStatus


class LawLedgerImmutableError(RuntimeError):
    """Raised when a mutation would alter committed law history."""


class LawLedger:
    """Append-only store for law records; SQLite-backed when persist=True."""

    def __init__(self, *, seed: list[LawRecord] | None = None, persist: bool = False) -> None:
        self._persist = persist
        self._rows: list[LawRecord] = list(seed or [])
        self._by_code: dict[str, LawRecord] = {row.code: row for row in self._rows}
        if persist:
            self._hydrate_from_cache()

    def _hydrate_from_cache(self) -> None:
        from nova.bridges import law_ledger_bridge

        cached = law_ledger_bridge.list_cached_laws()
        if not cached:
            return
        self._rows = list(cached)
        self._by_code = {row.code: row for row in self._rows}

    def _persist_record(self, record: LawRecord, *, entry_type: str) -> None:
        if not self._persist:
            return
        from nova.bridges import law_ledger_bridge

        law_ledger_bridge.persist_nova_law(record, entry_type=entry_type)

    def list(self) -> list[LawRecord]:
        return list(self._rows)

    def all(self) -> list[LawRecord]:
        return self.list()

    def get(self, code: str) -> LawRecord | None:
        return self._by_code.get(code)

    def admitted(self) -> list[LawRecord]:
        return [row for row in self._by_code.values() if row.status == LawStatus.ADMITTED]

    def append(self, record: LawRecord) -> LawRecord:
        if record.code in self._by_code:
            raise LawLedgerImmutableError(
                f"KLAW-3: law code {record.code} already exists; append status change instead"
            )
        self._rows.append(record)
        self._by_code[record.code] = record
        self._persist_record(record, entry_type="LAW_EVAL")
        return record

    def append_status_change(self, code: str, *, status: LawStatus, epoch: str) -> LawRecord:
        current = self._by_code.get(code)
        if current is None:
            raise KeyError(code)
        if current.status == status:
            return current
        successor = replace(current, status=status, epoch=epoch)
        self._rows.append(successor)
        self._by_code[code] = successor
        self._persist_record(successor, entry_type="LAW_STATUS_CHANGE")
        return successor

    def add_law(
        self,
        *,
        code: str,
        text: str,
        status: LawStatus,
        fitness: float,
        epoch: str,
        domains: tuple[str, ...] | list[str] = (),
        proof_ref: str = "",
    ) -> LawRecord:
        from nova.law_kernel.models import new_law_record

        return self.append(
            new_law_record(
                code=code,
                text=text,
                status=status,
                fitness=fitness,
                epoch=epoch,
                domains=domains,
                proof_ref=proof_ref,
            )
        )
