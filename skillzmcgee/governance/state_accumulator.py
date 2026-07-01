from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol


class LedgerView(Protocol):
    def all(self) -> list[dict[str, Any]]:
        ...


class StateAccumulator:
    def __init__(self) -> None:
        self.state: dict[str, dict[str, Any]] = {}

    def apply_entry(self, entry: dict[str, Any]) -> None:
        slice_id = str(entry["slice"])
        self.state[slice_id] = {
            "last_status": entry["status"],
            "last_output": deepcopy(entry["output"]),
            "last_run_id": entry["id"],
        }

    def rebuild_from_ledger(self, ledger: LedgerView) -> None:
        self.state = {}
        for entry in ledger.all():
            self.apply_entry(entry)

    def get_slice_state(self, slice_id: str) -> dict[str, Any] | None:
        value = self.state.get(slice_id)
        return deepcopy(value) if value is not None else None
