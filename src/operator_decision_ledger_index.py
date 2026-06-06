"""Secondary index for Operator Decision Ledger graph queries."""

# Engineering: OperatorDecisionLedgerIndexEngine
from __future__ import annotations

import json
import threading
from collections import deque
from pathlib import Path
from typing import Any

from src.temporal_replay.paths import default_runtime_dir, operator_ledger_index_path, operator_ledger_path

INDEX_VERSION = "operator_decision_ledger_index.v1"
MAX_QUERY_LIMIT = 500
MAX_CHAIN_NODES = 64


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def index_entry_from_row(row: dict[str, Any]) -> dict[str, Any]:
    federation = dict(row.get("federation") or {})
    grant_id = str(
        federation.get("grant_id")
        or (federation.get("counterparty_receipt_ref") or {}).get("grant_id")
        or ""
    ).strip() or None
    return {
        "decision_id": str(row.get("decision_id") or ""),
        "decision_kind": str(row.get("decision_kind") or ""),
        "decision": str(row.get("decision") or ""),
        "recorded_at": str(row.get("recorded_at") or ""),
        "tenant_id": row.get("tenant_id"),
        "approval_id": row.get("approval_id"),
        "mission_id": row.get("mission_id"),
        "grant_id": grant_id,
        "reversibility": str(row.get("reversibility") or ""),
        "pipeline_id": row.get("pipeline_id"),
    }


class OperatorDecisionLedgerIndex:
    """JSON index sidecar for filtered queries and causal chain walks."""

    def __init__(self, *, runtime_dir: Path | None = None):
        self._runtime_dir_override = runtime_dir
        self._lock = threading.Lock()

    @property
    def runtime_dir(self) -> Path:
        return self._runtime_dir_override or default_runtime_dir()

    def _index_path(self, scope_id: str) -> Path:
        return operator_ledger_index_path(scope_id, runtime_dir=self.runtime_dir)

    def _events_path(self, scope_id: str) -> Path:
        return operator_ledger_path(scope_id, runtime_dir=self.runtime_dir)

    def _read_index(self, scope_id: str) -> dict[str, Any]:
        path = self._index_path(scope_id)
        if not path.is_file():
            return {"index_version": INDEX_VERSION, "scope_id": scope_id, "entries": []}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"index_version": INDEX_VERSION, "scope_id": scope_id, "entries": []}
        entries = list(payload.get("entries") or [])
        return {
            "index_version": INDEX_VERSION,
            "scope_id": scope_id,
            "entries": entries,
        }

    def _write_index(self, scope_id: str, entries: list[dict[str, Any]]) -> None:
        path = self._index_path(scope_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "index_version": INDEX_VERSION,
            "scope_id": scope_id,
            "entry_count": len(entries),
            "entries": entries,
        }
        path.write_text(_stable_json(payload) + "\n", encoding="utf-8")

    def append_index_entry(self, scope_id: str, row: dict[str, Any]) -> None:
        entry = index_entry_from_row(row)
        if not entry.get("decision_id"):
            return
        with self._lock:
            payload = self._read_index(scope_id)
            entries = list(payload.get("entries") or [])
            entries = [e for e in entries if e.get("decision_id") != entry["decision_id"]]
            entries.append(entry)
            self._write_index(scope_id, entries)

    def rebuild_index(self, scope_id: str) -> dict[str, Any]:
        path = self._events_path(scope_id)
        entries: list[dict[str, Any]] = []
        if path.is_file():
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    entry = index_entry_from_row(row)
                    if entry.get("decision_id"):
                        entries.append(entry)
        with self._lock:
            self._write_index(scope_id, entries)
        return {"scope_id": scope_id, "entry_count": len(entries), "rebuilt": True}

    def query_index(
        self,
        scope_id: str,
        *,
        kind: str | None = None,
        since: str | None = None,
        tenant_id: str | None = None,
        pending_only: bool = False,
        cursor: str | None = None,
        limit: int = MAX_QUERY_LIMIT,
    ) -> dict[str, Any]:
        payload = self._read_index(scope_id)
        entries = list(payload.get("entries") or [])
        if not entries and self._events_path(scope_id).is_file():
            self.rebuild_index(scope_id)
            payload = self._read_index(scope_id)
            entries = list(payload.get("entries") or [])

        filtered: list[dict[str, Any]] = []
        for entry in entries:
            if kind and str(entry.get("decision_kind") or "") != kind:
                continue
            if since and str(entry.get("recorded_at") or "") < since:
                continue
            if tenant_id and str(entry.get("tenant_id") or "") != tenant_id:
                continue
            if pending_only and str(entry.get("decision") or "") != "pending":
                continue
            filtered.append(entry)

        start_idx = 0
        if cursor:
            for idx, entry in enumerate(filtered):
                if str(entry.get("decision_id")) == cursor:
                    start_idx = idx + 1
                    break

        cap = max(1, min(int(limit or MAX_QUERY_LIMIT), MAX_QUERY_LIMIT))
        page = filtered[start_idx : start_idx + cap]
        next_cursor = str(page[-1].get("decision_id") or "") if len(page) == cap and page else None
        return {
            "scope_id": scope_id,
            "entries": page,
            "count": len(page),
            "total_matched": len(filtered),
            "next_cursor": next_cursor,
        }

    def shortest_causal_chain(
        self,
        scope_id: str,
        from_id: str,
        to_id: str,
        *,
        rows_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if rows_by_id is None:
            rows_by_id = {}
            path = self._events_path(scope_id)
            if path.is_file():
                with path.open(encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        did = str(row.get("decision_id") or "")
                        if did:
                            rows_by_id[did] = row

        if from_id not in rows_by_id or to_id not in rows_by_id:
            return {
                "scope_id": scope_id,
                "from_id": from_id,
                "to_id": to_id,
                "found": False,
                "path": [],
                "edges": [],
            }

        children: dict[str, list[str]] = {}
        for did, row in rows_by_id.items():
            for parent in list(row.get("causal_parents") or []):
                parent_id = str(parent)
                children.setdefault(parent_id, []).append(did)

        queue: deque[list[str]] = deque([[from_id]])
        visited: set[str] = {from_id}
        while queue:
            path = queue.popleft()
            current = path[-1]
            if current == to_id:
                edges = [
                    {"from": path[i], "to": path[i + 1]}
                    for i in range(len(path) - 1)
                ]
                return {
                    "scope_id": scope_id,
                    "from_id": from_id,
                    "to_id": to_id,
                    "found": True,
                    "path": path,
                    "edges": edges,
                    "node_count": len(path),
                }
            if len(path) >= MAX_CHAIN_NODES:
                continue
            for child in children.get(current, []):
                if child in visited:
                    continue
                visited.add(child)
                queue.append(path + [child])
            for parent in list(rows_by_id.get(current, {}).get("causal_parents") or []):
                parent_id = str(parent)
                if parent_id in visited:
                    continue
                visited.add(parent_id)
                queue.append(path + [parent_id])

        return {
            "scope_id": scope_id,
            "from_id": from_id,
            "to_id": to_id,
            "found": False,
            "path": [],
            "edges": [],
        }


operator_decision_ledger_index = OperatorDecisionLedgerIndex()
