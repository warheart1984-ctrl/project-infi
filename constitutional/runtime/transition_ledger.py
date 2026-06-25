"""Constitutional Transition Ledger — durable record of all state transitions."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from constitutional.runtime.constitutional_state import (
    StateObject,
    reconstruct_state,
    replay_state,
    validate_transition,
)
from constitutional.runtime.receipts_v2 import (
    BaseReceiptV2,
    TransitionReceiptV2,
    is_receipt_v2_complete,
    stable_json_hash,
)


class LedgerEntry(BaseModel):
    transition_id: str
    state_object_id: str
    from_state: str
    to_state: str
    receipt_id: str
    timestamp: str
    runtime: str
    legal_basis: str
    accountable_party: str
    lineage_hash: str = ""


class LedgerFailure(BaseModel):
    code: str
    message: str
    receipt_id: str | None = None
    transition_id: str | None = None


class LedgerReplayResult(BaseModel):
    entries_processed: int
    failures: list[LedgerFailure]
    state_replay_diverged: bool
    ledger_hash: str


class ConstitutionalTransitionLedger:
    """Append-only ledger of constitutional transitions (Article XVI ledger spec)."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._receipt_index: dict[str, LedgerEntry] = {}

    @property
    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def append_from_transition_receipt(
        self,
        receipt: TransitionReceiptV2,
        *,
        state_object_id: str,
        accountable_party: str,
    ) -> LedgerEntry:
        if not is_receipt_v2_complete(receipt):
            raise ValueError(f"incomplete transition receipt: {receipt.receipt_id}")
        validate_transition(receipt.transition.from_state, receipt.transition.to_state)
        if receipt.receipt_id in self._receipt_index:
            raise ValueError(f"duplicate receipt_id in ledger: {receipt.receipt_id}")

        entry = LedgerEntry(
            transition_id=receipt.receipt_id,
            state_object_id=state_object_id,
            from_state=receipt.transition.from_state,
            to_state=receipt.transition.to_state,
            receipt_id=receipt.receipt_id,
            timestamp=receipt.timestamp,
            runtime=receipt.runtime,
            legal_basis=receipt.transition.legal_basis,
            accountable_party=accountable_party,
            lineage_hash=receipt.continuity.lineage_hash,
        )
        self._entries.append(entry)
        self._receipt_index[receipt.receipt_id] = entry
        return entry

    def has_receipt(self, receipt_id: str) -> bool:
        return receipt_id in self._receipt_index

    def detect_failures(self) -> list[LedgerFailure]:
        failures: list[LedgerFailure] = []
        seen_receipts: set[str] = set()
        prior_by_state: dict[str, str] = {}

        for entry in self._entries:
            if entry.receipt_id in seen_receipts:
                failures.append(
                    LedgerFailure(
                        code="duplicate_receipt",
                        message="duplicate receipt_id in ledger",
                        receipt_id=entry.receipt_id,
                        transition_id=entry.transition_id,
                    )
                )
            seen_receipts.add(entry.receipt_id)

            if not entry.legal_basis:
                failures.append(
                    LedgerFailure(
                        code="missing_legal_basis",
                        message="ledger entry missing legal_basis",
                        receipt_id=entry.receipt_id,
                    )
                )

            if not entry.accountable_party:
                failures.append(
                    LedgerFailure(
                        code="unaccountable_action",
                        message="ledger entry missing accountable_party",
                        receipt_id=entry.receipt_id,
                    )
                )

            try:
                validate_transition(entry.from_state, entry.to_state)
            except ValueError as exc:
                failures.append(
                    LedgerFailure(
                        code="illegal_transition",
                        message=str(exc),
                        transition_id=entry.transition_id,
                    )
                )

            expected_from = prior_by_state.get(entry.state_object_id, "Proposed")
            if entry.from_state != expected_from:
                failures.append(
                    LedgerFailure(
                        code="broken_lineage",
                        message=(
                            f"state {entry.state_object_id}: expected from_state "
                            f"{expected_from}, got {entry.from_state}"
                        ),
                        transition_id=entry.transition_id,
                    )
                )
            prior_by_state[entry.state_object_id] = entry.to_state

        return failures

    def replay(
        self,
        receipts: list[TransitionReceiptV2],
        canonical_state: StateObject,
    ) -> LedgerReplayResult:
        failures = self.detect_failures()
        state_result = replay_state(receipts, canonical_state)
        if state_result.diverged:
            failures.append(
                LedgerFailure(
                    code="irreproducible_transition",
                    message="state replay diverged from canonical state",
                )
            )
        return LedgerReplayResult(
            entries_processed=len(self._entries),
            failures=failures,
            state_replay_diverged=state_result.diverged,
            ledger_hash=self.snapshot_hash(),
        )

    def snapshot_hash(self) -> str:
        return stable_json_hash([e.model_dump() for e in self._entries])

    def save_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for entry in self._entries:
                handle.write(json.dumps(entry.model_dump(), sort_keys=True) + "\n")

    @classmethod
    def load_jsonl(cls, path: Path) -> ConstitutionalTransitionLedger:
        ledger = cls()
        if not path.is_file():
            return ledger
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entry = LedgerEntry.model_validate(json.loads(line))
                ledger._entries.append(entry)
                ledger._receipt_index[entry.receipt_id] = entry
        return ledger

    def reconstruct_state_for(
        self,
        state_object_id: str,
        receipts: list[TransitionReceiptV2],
        seed: StateObject,
    ) -> StateObject:
        scoped = [
            r
            for r in receipts
            if not r.transition.state_id or r.transition.state_id == state_object_id
        ]
        return reconstruct_state(scoped, seed)

    def receipts_for_entries(self, receipts_by_id: dict[str, TransitionReceiptV2]) -> list[TransitionReceiptV2]:
        out: list[TransitionReceiptV2] = []
        for entry in self._entries:
            receipt = receipts_by_id.get(entry.receipt_id)
            if receipt is None:
                raise KeyError(f"missing transition receipt for ledger entry {entry.receipt_id}")
            out.append(receipt)
        return out
