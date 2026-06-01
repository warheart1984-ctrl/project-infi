"""Graph index store — query layer over canonical JSONL with in-memory index."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.graph_index.index import GraphClaimIndex
from src.ugr.graph_index.sync import discover_claim_paths, load_claims_from_paths


UGR_GRAPH_ENABLED_ENV = "UGR_GRAPH_ENABLED"


def graph_index_enabled() -> bool:
    raw = os.getenv(UGR_GRAPH_ENABLED_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _default_config_path() -> Path:
    env_path = os.getenv("UGR_GRAPH_INDEX_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "graph-index.json"


class GraphIndexStore:
    """Maintain graph index synced from canonical claim JSONL files."""

    def __init__(
        self,
        *,
        runtime_root: str | Path,
        ledger: Any | None = None,
        config_path: str | Path | None = None,
    ):
        self.runtime_root = Path(runtime_root)
        self.ledger = ledger
        self.config_path = Path(config_path) if config_path else _default_config_path()
        self._config = self._load_config()
        self.index = GraphClaimIndex()
        self._query_backend = None
        try:
            from src.ugr.graph_backends.factory import create_query_backend, load_graph_backend_config

            self._query_backend = create_query_backend(
                runtime_root=self.runtime_root,
                config=load_graph_backend_config(),
            )
        except Exception:
            self._query_backend = None
        self.rebuild()

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {"config_version": "0.1", "max_rows_per_path": 5000}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def rebuild(self) -> dict[str, Any]:
        paths = discover_claim_paths(self.runtime_root)
        max_rows = int(self._config.get("max_rows_per_path") or 5000)
        claims = load_claims_from_paths(paths, max_rows_per_path=max_rows)
        self.index.rebuild(claims)
        backend_stats = None
        if self._query_backend is not None:
            backend_stats = self._query_backend.rebuild_from_canonical(max_rows_per_path=max_rows)
        return {
            "paths": [str(path) for path in paths],
            "loaded_claims": len(claims),
            **self.index.stats(),
            "query_backend": backend_stats,
        }

    def on_append(self, record: dict[str, Any]) -> None:
        if str(record.get("record_type") or "claim") == "claim":
            self.index.upsert_claim(record)
            if self._query_backend is not None:
                self._query_backend.on_append(record)

    def scan_query_related(
        self,
        terms: list[str],
        *,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Fallback scan via underlying ledger — used for parity tests."""
        if self.ledger is None:
            return self.index.query_related(terms, tenant_scope=tenant_scope, limit=limit)
        if hasattr(self.ledger, "query_related"):
            return self.ledger.query_related(terms, tenant_scope=tenant_scope, limit=limit)
        return []

    def query_related(
        self,
        terms: list[str],
        *,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if self._query_backend is not None:
            return self._query_backend.query_related(terms, tenant_scope=tenant_scope, limit=limit)
        return self.index.query_related(terms, tenant_scope=tenant_scope, limit=limit)

    def query_by_subject(
        self,
        subject: str,
        *,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if self._query_backend is not None:
            return self._query_backend.query_by_subject(subject, tenant_scope=tenant_scope, limit=limit)
        return self.index.query_by_subject(subject, tenant_scope=tenant_scope, limit=limit)

    def read_claims(self, *, tenant_scope: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        if tenant_scope is None and self.ledger is not None and hasattr(self.ledger, "read_claims"):
            claims = self.ledger.read_claims(limit=limit)
            for row in claims:
                self.on_append(row)
            return claims
        return self.index.read_claims(tenant_scope=tenant_scope, limit=limit)

    def stats(self) -> dict[str, Any]:
        payload = self.index.stats()
        if self._query_backend is not None:
            payload["query_backend"] = self._query_backend.stats()
        return payload
