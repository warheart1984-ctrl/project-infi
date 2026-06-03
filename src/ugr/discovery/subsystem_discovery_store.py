"""Durable subsystem discovery receipts and shadow catalog."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.mission.tenant_manifold import tenant_path_slug
from src.ugr.platform.tenant_registry import normalize_tenant_id


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


class SubsystemDiscoveryStore:
    """Tenant-partitioned discoveries.jsonl + catalog.jsonl."""

    def __init__(self, runtime_dir: str | Path | None = None, *, tenant_id: str | None = None):
        root = Path(runtime_dir or _default_runtime_dir())
        self.runtime_root = root
        self.tenant_id = normalize_tenant_id(tenant_id or "global")
        slug = tenant_path_slug(self.tenant_id)
        base = root / "urg" / "discovery" / slug
        self.discoveries_path = base / "discoveries.jsonl"
        self.catalog_path = base / "catalog.jsonl"
        base.mkdir(parents=True, exist_ok=True)

    def _read_lines(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def has_discovery(self, subsystem_id: str) -> bool:
        sid = str(subsystem_id or "").strip()
        for row in self._read_lines(self.discoveries_path):
            if str(row.get("subsystem_id") or "") == sid:
                return True
        return False

    def persist_discovery(
        self,
        receipt: dict[str, Any],
        *,
        tenant_id: str | None = None,
    ) -> bool:
        sid = str(receipt.get("subsystem_id") or "").strip()
        if not sid:
            return False
        if self.has_discovery(sid):
            return False
        record = {
            "subsystem_id": sid,
            "receipt_id": receipt.get("receipt_id"),
            "tenant_id": normalize_tenant_id(tenant_id or receipt.get("tenant_id")),
            "receipt": receipt,
        }
        with self.discoveries_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
        return True

    def append_catalog(
        self,
        receipt: dict[str, Any],
        *,
        tenant_id: str | None = None,
    ) -> bool:
        sid = str(receipt.get("subsystem_id") or "").strip()
        if not sid:
            return False
        for row in self._read_lines(self.catalog_path):
            if str(row.get("subsystem_id") or "") == sid:
                return False
        spec = dict(receipt.get("spec") or {})
        entry = {
            "subsystem_id": sid,
            "role": spec.get("role"),
            "rail_class": spec.get("rail_class"),
            "first_discovered_at": receipt.get("discovered_at"),
            "receipt_id": receipt.get("receipt_id"),
            "operator_id": receipt.get("operator_id"),
            "status": str(receipt.get("catalog_status") or "shadow"),
            "tenant_id": normalize_tenant_id(tenant_id or receipt.get("tenant_id")),
        }
        with self.catalog_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
        return True

    def get_by_subsystem_id(self, subsystem_id: str) -> dict[str, Any] | None:
        sid = str(subsystem_id or "").strip()
        for row in reversed(self._read_lines(self.discoveries_path)):
            if str(row.get("subsystem_id") or "") == sid:
                return dict(row.get("receipt") or row)
        return None

    def list_catalog(
        self,
        *,
        since: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self._read_lines(self.catalog_path)
        if since is not None:
            rows = [r for r in rows if float(r.get("first_discovered_at") or 0) >= since]
        return rows[-limit:]
