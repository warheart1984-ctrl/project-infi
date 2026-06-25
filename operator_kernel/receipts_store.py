"""Append-only Receipt v2 store — global JSONL + per-state JSONL + in-memory index."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import TypeAlias

from constitutional.runtime import TransitionReceiptV2

ROOT = Path(".runtime/receipts")
ALL = ROOT / "all_receipts.jsonl"
BY_STATE = ROOT / "by_state"

StateKey: TypeAlias = tuple[str, str]

_lock = threading.Lock()
_index: dict[StateKey, list[TransitionReceiptV2]] = {}


def _ensure_dirs() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    BY_STATE.mkdir(parents=True, exist_ok=True)


def _state_key(receipt: TransitionReceiptV2) -> StateKey:
    transition = receipt.transition
    state_type = transition.state_type or "operator_task"
    state_id = transition.state_id or receipt.inputs.request_id
    return state_type, state_id


def _state_file(state_type: str, state_object_id: str) -> Path:
    return BY_STATE / f"{state_type}__{state_object_id}.jsonl"


def append_receipt(receipt: TransitionReceiptV2) -> None:
    """Append one transition receipt to global log, per-state log, and memory index."""
    _ensure_dirs()
    line = receipt.model_dump_json()

    with _lock:
        with ALL.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

        state_type, state_id = _state_key(receipt)
        with _state_file(state_type, state_id).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

        _index.setdefault((state_type, state_id), []).append(receipt)


def load_receipts_for_state(state_type: str, state_object_id: str) -> list[TransitionReceiptV2]:
    """Load receipts for a state object from memory index or per-state JSONL."""
    key = (state_type, state_object_id)
    with _lock:
        if key in _index:
            return list(_index[key])

    path = _state_file(state_type, state_object_id)
    if not path.is_file():
        return []

    receipts: list[TransitionReceiptV2] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            receipts.append(TransitionReceiptV2.model_validate(json.loads(line)))

    with _lock:
        _index[key] = list(receipts)
    return receipts


def clear_memory_index() -> None:
    """Test helper — drop in-memory cache (disk logs unchanged)."""
    with _lock:
        _index.clear()
