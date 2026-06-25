"""Append-only domain receipt store (ObservationReceiptV2 and other non-transition receipts)."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from constitutional.runtime.receipts_v2 import BaseReceiptV2

ROOT = Path(".runtime/receipts")
DOMAIN_ALL = ROOT / "domain_receipts.jsonl"
DOMAIN_BY_STATE = ROOT / "by_state"

_lock = threading.Lock()
_index: dict[str, list[BaseReceiptV2]] = {}


def _ensure_dirs() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    DOMAIN_BY_STATE.mkdir(parents=True, exist_ok=True)


def _state_file(state_object_id: str) -> Path:
    safe = state_object_id.replace("/", "_").replace(":", "_")
    return DOMAIN_BY_STATE / f"domain__{safe}.jsonl"


def append_domain_receipt(receipt: BaseReceiptV2) -> None:
    """Append one domain receipt to global + per-state JSONL and memory index."""
    _ensure_dirs()
    line = receipt.model_dump_json()

    with _lock:
        with DOMAIN_ALL.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

        state_id = receipt.inputs.request_id
        with _state_file(state_id).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

        _index.setdefault(state_id, []).append(receipt)


def load_domain_receipts_for_state(state_object_id: str) -> list[BaseReceiptV2]:
    with _lock:
        if state_object_id in _index:
            return list(_index[state_object_id])

    path = _state_file(state_object_id)
    if not path.is_file():
        return []

    raw: list[BaseReceiptV2] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                raw.append(BaseReceiptV2.model_validate(json.loads(line)))

    with _lock:
        _index[state_object_id] = list(raw)
    return raw


def clear_domain_memory_index() -> None:
    with _lock:
        _index.clear()
