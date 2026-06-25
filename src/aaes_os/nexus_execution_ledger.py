"""Nexus execution observatory — records governed AAES receipts."""

from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ledger_path() -> Path:
    override = os.environ.get("NEXUS_EXECUTION_LEDGER_PATH", "").strip()
    if override:
        return Path(override)
    runtime = os.environ.get("AAIS_RUNTIME_DIR", "").strip()
    if runtime:
        return Path(runtime) / "nexus_executions.jsonl"
    return Path(__file__).resolve().parents[2] / ".runtime" / "nexus_executions.jsonl"


class NexusExecutionLedger:
    """Append-only ledger of governed AAES execution receipts for Nexus ops-console."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: list[dict[str, Any]] = []
        self._read_pos = 0
        self._hydrate()

    def _hydrate(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                cleaned = line.strip()
                if not cleaned:
                    continue
                try:
                    self._cache.append(json.loads(cleaned))
                except json.JSONDecodeError:
                    continue
            self._read_pos = handle.tell()

    def _sync_from_disk(self) -> None:
        """Append new ledger lines written by other processes (e.g. AAIS container)."""
        if not self.path.exists():
            return
        with self._lock:
            with self.path.open("r", encoding="utf-8") as handle:
                handle.seek(self._read_pos)
                for line in handle:
                    cleaned = line.strip()
                    if not cleaned:
                        continue
                    try:
                        self._cache.append(json.loads(cleaned))
                    except json.JSONDecodeError:
                        continue
                self._read_pos = handle.tell()

    def record_execution(self, receipt: dict[str, Any]) -> dict[str, Any]:
        """Persist one Nexus execution event derived from an AAES receipt."""
        event = {
            "recorded_at": _now(),
            "event_id": str(
                receipt.get("event_id")
                or receipt.get("aaes_trace_id")
                or receipt.get("trace_id")
                or receipt.get("execution_id")
                or ""
            ),
            "mission_id": str(receipt.get("mission_id") or ""),
            "law_eval_id": str(receipt.get("law_eval_id") or ""),
            "aaes_trace_id": str(receipt.get("aaes_trace_id") or receipt.get("trace_id") or ""),
            "aaes_status": str(receipt.get("aaes_status") or receipt.get("status") or ""),
            "steward_id": str(receipt.get("steward_id") or receipt.get("steward_identity") or ""),
            "darz_bridge_hash": str(receipt.get("darz_bridge_hash") or ""),
            "blocked": bool(receipt.get("blocked")),
            "receipt": dict(receipt),
        }
        with self._lock:
            self._cache.append(event)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def list_executions(self, *, limit: int = 50) -> list[dict[str, Any]]:
        self._sync_from_disk()
        with self._lock:
            return list(reversed(self._cache[-limit:]))

    def latest(self) -> dict[str, Any] | None:
        items = self.list_executions(limit=1)
        return items[0] if items else None


_LEDGER: NexusExecutionLedger | None = None


def get_nexus_execution_ledger() -> NexusExecutionLedger:
    global _LEDGER
    if _LEDGER is None:
        _LEDGER = NexusExecutionLedger()
    return _LEDGER


def reset_nexus_execution_ledger(ledger: NexusExecutionLedger | None = None) -> None:
    global _LEDGER
    _LEDGER = ledger
