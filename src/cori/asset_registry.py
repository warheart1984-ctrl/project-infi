"""CORI Alpha — lightweight asset registry backed by continuity SQLite."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from src.continuity.continuity_store import ContinuityStore, get_continuity_store


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AssetRegistry:
    """Register and query governed assets (missions, artifacts, entities)."""

    def __init__(self, store: ContinuityStore | None = None) -> None:
        self._store = store or get_continuity_store()

    def register(
        self,
        asset_id: str,
        metadata: dict[str, Any],
        *,
        asset_type: str | None = None,
        steward_identity: str | None = None,
    ) -> None:
        body = dict(metadata)
        resolved_type = asset_type or str(body.get("asset_type") or "governed_mission")
        with self._store._connect() as conn:
            conn.execute(
                """
                INSERT INTO assets (id, asset_type, metadata_json, steward_identity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    asset_type = excluded.asset_type,
                    metadata_json = excluded.metadata_json,
                    steward_identity = excluded.steward_identity,
                    updated_at = excluded.updated_at
                """,
                (
                    asset_id,
                    resolved_type,
                    json.dumps(body, sort_keys=True, default=str),
                    steward_identity,
                    _now(),
                    _now(),
                ),
            )

    def get(self, asset_id: str) -> dict[str, Any] | None:
        with self._store._connect() as conn:
            row = conn.execute(
                "SELECT id, asset_type, metadata_json, steward_identity, created_at, updated_at FROM assets WHERE id = ?",
                (asset_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "asset_type": row["asset_type"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "steward_identity": row["steward_identity"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_assets(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._store._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, asset_type, metadata_json, steward_identity, created_at, updated_at
                FROM assets
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "asset_type": row["asset_type"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
                "steward_identity": row["steward_identity"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


_REGISTRY: AssetRegistry | None = None


def get_asset_registry(*, store: ContinuityStore | None = None) -> AssetRegistry:
    global _REGISTRY
    if store is not None:
        return AssetRegistry(store=store)
    if _REGISTRY is None:
        _REGISTRY = AssetRegistry()
    return _REGISTRY


def reset_asset_registry(registry: AssetRegistry | None = None) -> None:
    global _REGISTRY
    _REGISTRY = registry
