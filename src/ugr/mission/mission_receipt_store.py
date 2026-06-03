"""Durable MissionReceipt persistence — tenant-partitioned under AAIS runtime dir."""

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


def receipt_admin_enabled() -> bool:
    raw = os.getenv("URG_RECEIPT_ADMIN", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class MissionReceiptStore:
    """Append-only mission receipt log per tenant."""

    def __init__(self, runtime_dir: str | Path | None = None, *, tenant_id: str | None = None):
        root = Path(runtime_dir or _default_runtime_dir())
        self.tenant_id = normalize_tenant_id(tenant_id or "global")
        slug = tenant_path_slug(self.tenant_id)
        self.path = root / "urg" / "receipts" / slug / "receipts.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._legacy_global = root / "urg" / "receipts.jsonl"

    def persist_receipt(
        self,
        mission_id: str,
        *,
        legacy: dict[str, Any],
        schema: dict[str, Any],
        tenant_id: str | None = None,
    ) -> bool:
        """Append receipt record; skip if same mission_id + ledger_root already stored."""
        mid = str(mission_id or "").strip()
        if not mid:
            return False
        tenant_norm = normalize_tenant_id(tenant_id or self.tenant_id)
        ledger_root = str(schema.get("ledger_root") or "")
        if self._has_record(mid, ledger_root, tenant_norm=tenant_norm):
            return False
        record = {
            "mission_id": mid,
            "tenant_id": tenant_norm,
            "ledger_root": ledger_root,
            "legacy_receipt": legacy,
            "mission_receipt_schema": schema,
        }
        line = json.dumps(record, sort_keys=True, default=str)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return True

    def _has_record(self, mission_id: str, ledger_root: str, *, tenant_norm: str) -> bool:
        for row in self._iter_records(tenant_norm=tenant_norm):
            if row.get("mission_id") == mission_id and row.get("ledger_root") == ledger_root:
                return True
        return False

    def _iter_records(self, *, tenant_norm: str | None = None) -> list[dict[str, Any]]:
        paths: list[Path] = [self.path]
        if receipt_admin_enabled() and self._legacy_global.exists():
            paths.append(self._legacy_global)
        rows: list[dict[str, Any]] = []
        for path in paths:
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows

    def get_receipt(
        self,
        mission_id: str,
        *,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Return latest stored receipt for mission_id within tenant partition."""
        mid = str(mission_id or "").strip()
        if not mid:
            return None
        tenant_norm = normalize_tenant_id(tenant_id or self.tenant_id)
        latest: dict[str, Any] | None = None
        for row in self._iter_records(tenant_norm=tenant_norm):
            if row.get("mission_id") != mid:
                continue
            row_tenant = normalize_tenant_id(row.get("tenant_id") or tenant_norm)
            if row_tenant != tenant_norm and not receipt_admin_enabled():
                continue
            latest = row
        return latest
