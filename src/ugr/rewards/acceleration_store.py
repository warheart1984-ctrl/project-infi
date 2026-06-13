"""Tenant-scoped acceleration entitlement persistence."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def _runtime_root(runtime_dir: str | None = None) -> Path:
    configured = runtime_dir or os.getenv("AAIS_RUNTIME_DIR")
    return Path(configured or ".runtime").expanduser().resolve()


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "unknown")).strip("_")
    return normalized or "unknown"


class AccelerationStore:
    """Small JSON-backed store for acceleration entitlements."""

    def __init__(self, *, runtime_dir: str | None = None, tenant_id: str = "default") -> None:
        self.runtime_root = _runtime_root(runtime_dir)
        self.tenant_id = tenant_id
        self.base_dir = self.runtime_root / "ugr" / "acceleration" / _slug(tenant_id)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def entitlements_path(self, operator_id: str) -> Path:
        return self.base_dir / f"{_slug(operator_id)}.json"

    def load(self, operator_id: str) -> dict[str, Any]:
        path = self.entitlements_path(operator_id)
        if not path.exists():
            return {"operator_id": operator_id, "tenant_id": self.tenant_id, "entitlements": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, operator_id: str, record: dict[str, Any]) -> None:
        path = self.entitlements_path(operator_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")

    def grant(self, operator_id: str, entitlement: str, *, contribution_id: str) -> dict[str, Any]:
        record = self.load(operator_id)
        entitlements = list(record.get("entitlements") or [])
        if entitlement in entitlements:
            self.save(operator_id, record)
            return {
                "status": "duplicate",
                "skipped": True,
                "operator_id": operator_id,
                "tenant_id": self.tenant_id,
                "entitlement": entitlement,
            }
        entitlements.append(entitlement)
        record.update(
            {
                "operator_id": operator_id,
                "tenant_id": self.tenant_id,
                "entitlements": entitlements,
                "last_contribution_id": contribution_id,
            }
        )
        self.save(operator_id, record)
        return {
            "status": "granted",
            "skipped": False,
            "operator_id": operator_id,
            "tenant_id": self.tenant_id,
            "entitlement": entitlement,
        }

    def has(self, operator_id: str, entitlement: str) -> bool:
        return entitlement in set(self.load(operator_id).get("entitlements") or [])
