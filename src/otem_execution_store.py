"""Durable persistence for OTEM execution substrate workflows (phase 2)."""

# Mythic: Otem Execution Store
# Engineering: OtemExecutionStoreEngine
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_STORE_DIR = Path(
    os.environ.get("AAIS_OTEM_EXECUTION_STORE_DIR")
    or os.environ.get("AAIS_DATA_DIR", ".runtime")
) / "otem-execution"


class OTEMExecutionStore:
    """Append-friendly JSON persistence for substrate workflow records."""

    def __init__(self, store_dir: Path | None = None) -> None:
        self.store_dir = Path(store_dir or DEFAULT_STORE_DIR)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, workflow_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in workflow_id)
        return self.store_dir / f"{safe}.json"

    def save_workflow_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow_id = str(payload.get("workflow_id") or "").strip()
        if not workflow_id:
            raise ValueError("workflow_id is required for OTEM execution persistence")
        path = self._path_for(workflow_id)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def load_workflow_record(self, workflow_id: str) -> dict[str, Any] | None:
        path = self._path_for(workflow_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def delete_workflow(self, workflow_id: str) -> None:
        path = self._path_for(workflow_id)
        if path.is_file():
            path.unlink()

    def clear_all(self) -> None:
        for path in self.store_dir.glob("*.json"):
            path.unlink()


_default_store: OTEMExecutionStore | None = None


def get_otem_execution_store() -> OTEMExecutionStore:
    global _default_store
    if _default_store is None:
        _default_store = OTEMExecutionStore()
    return _default_store


def reset_otem_execution_store(*, clear_persisted: bool = False) -> OTEMExecutionStore:
    global _default_store
    _default_store = OTEMExecutionStore()
    if clear_persisted:
        _default_store.clear_all()
    return _default_store
