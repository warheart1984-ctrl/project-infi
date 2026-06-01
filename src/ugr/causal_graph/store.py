"""Persistent causal graph store — JSONL canonical logs + in-memory index."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import json
import os
from collections import defaultdict
from datetime import datetime
from src.datetime_compat import UTC
from pathlib import Path
from typing import Any

from src.ugr.causal_graph.provenance import (
    discover_provenance_paths,
    load_provenance_links,
    materialize_causal_edges,
)
from src.ugr.causal_graph.region_health import RegionHealthRegistry
from src.ugr.graph_index.store import GraphIndexStore
from src.ugr.graph_index.sync import discover_claim_paths, load_claims_from_paths
from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.unified_pattern_ledger import _stable_json


UGR_CAUSAL_GRAPH_ENABLED_ENV = "UGR_CAUSAL_GRAPH_ENABLED"


def causal_graph_enabled() -> bool:
    raw = os.getenv(UGR_CAUSAL_GRAPH_ENABLED_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _default_config_path() -> Path:
    env_path = os.getenv("UGR_CAUSAL_GRAPH_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "causal-graph.json"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CausalGraphStore:
    """Causal graph v1 — persistent edge log + graph index + region overlays."""

    GRAPH_VERSION = "1.0"

    def __init__(
        self,
        *,
        runtime_root: str | Path,
        ledger: Any | None = None,
        config_path: str | Path | None = None,
        regions: RegionHealthRegistry | None = None,
    ):
        self.runtime_root = Path(runtime_root)
        self.ledger = ledger
        self.config_path = Path(config_path) if config_path else _default_config_path()
        self._config = self._load_config()
        self.regions = regions or RegionHealthRegistry()
        self.index = GraphIndexStore(
            runtime_root=self.runtime_root,
            ledger=self.ledger,
            config_path=os.getenv("UGR_GRAPH_INDEX_CONFIG") or None,
        )
        self.graph_dir = self.runtime_root / "collective-pattern-ledger" / "causal-graph-v1"
        self.edges_path = self.graph_dir / str(self._config.get("persistent_edge_log") or "edges.jsonl")
        self.nodes_path = self.graph_dir / str(self._config.get("persistent_node_log") or "nodes.jsonl")
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self._edges: dict[str, dict[str, Any]] = {}
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self.rebuild()

    def configure_runtime_root(self, runtime_root: str | Path) -> None:
        self.runtime_root = Path(runtime_root)
        self.graph_dir = self.runtime_root / "collective-pattern-ledger" / "causal-graph-v1"
        self.edges_path = self.graph_dir / str(self._config.get("persistent_edge_log") or "edges.jsonl")
        self.nodes_path = self.graph_dir / str(self._config.get("persistent_node_log") or "nodes.jsonl")
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self.index.runtime_root = self.runtime_root
        self.index.ledger = self.ledger

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return _wrap_ul_payload({"config_version": "0.1", "max_rows_per_path": 5000, "default_traversal_depth": 2})
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_stable_json(record) + "\n")

    def _load_persistent_edges(self) -> None:
        self._edges.clear()
        self._adjacency.clear()
        if not self.edges_path.exists():
            return
        with self.edges_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                edge = json.loads(line)
                edge_id = str(edge.get("edge_id") or "")
                if not edge_id:
                    continue
                self._edges[edge_id] = edge
                self._adjacency[str(edge.get("from_id") or "")].append(edge_id)

    def _persist_edges(self, edges: list[dict[str, Any]], *, replace: bool = False) -> None:
        if replace and self.edges_path.exists():
            self.edges_path.unlink()
        for edge in edges:
            payload = {
                **edge,
                "graph_version": self.GRAPH_VERSION,
                "timestamp": edge.get("timestamp") or _utc_now_iso(),
            }
            edge_id = str(payload.get("edge_id") or "")
            if edge_id in self._edges and not replace:
                continue
            self._edges[edge_id] = payload
            self._adjacency[str(payload.get("from_id") or "")].append(edge_id)
            self._append_jsonl(self.edges_path, payload)

    def _persist_nodes(self, claims: list[dict[str, Any]], *, replace: bool = False) -> None:
        if replace and self.nodes_path.exists():
            self.nodes_path.unlink()
        for claim in claims:
            node = {
                "node_id": claim.get("claim_id"),
                "node_type": "claim",
                "subject": claim.get("subject"),
                "predicate": claim.get("predicate"),
                "object": claim.get("object"),
                "tenant_scope": claim.get("tenant_scope"),
                "shard_id": claim.get("shard_id"),
                "graph_version": self.GRAPH_VERSION,
                "timestamp": _utc_now_iso(),
            }
            self._append_jsonl(self.nodes_path, node)

    def rebuild(self) -> dict[str, Any]:
        index_stats = self.index.rebuild()
        max_rows = int(self._config.get("max_rows_per_path") or 5000)
        claim_paths = discover_claim_paths(self.runtime_root)
        provenance_paths = discover_provenance_paths(self.runtime_root)
        claims = load_claims_from_paths(claim_paths, max_rows_per_path=max_rows)
        links = load_provenance_links(provenance_paths, max_rows_per_path=max_rows)
        edges = materialize_causal_edges(claims=claims, provenance_links=links)
        self._load_persistent_edges()
        if not self._edges:
            self._persist_edges(edges, replace=True)
            self._persist_nodes(claims, replace=True)
        else:
            existing_ids = set(self._edges.keys())
            new_edges = [edge for edge in edges if str(edge.get("edge_id") or "") not in existing_ids]
            self._persist_edges(new_edges, replace=False)
        return _wrap_ul_payload({
            **index_stats,
            "graph_version": self.GRAPH_VERSION,
            "edge_count": len(self._edges),
            "provenance_links_loaded": len(links),
            "region_health": self.regions.health_snapshot(),
        })

    def on_append(self, record: dict[str, Any]) -> None:
        self.index.on_append(record)
        if str(record.get("record_type") or "claim") != "claim":
            return
        claim_id = str(record.get("claim_id") or "")
        edges = materialize_causal_edges(claims=[record], provenance_links=[])
        self._persist_edges(edges, replace=False)
        self._append_jsonl(
            self.nodes_path,
            {
                "node_id": claim_id,
                "node_type": "claim",
                "subject": record.get("subject"),
                "predicate": record.get("predicate"),
                "object": record.get("object"),
                "tenant_scope": record.get("tenant_scope"),
                "shard_id": record.get("shard_id"),
                "graph_version": self.GRAPH_VERSION,
                "timestamp": _utc_now_iso(),
            },
        )

    def stats(self) -> dict[str, Any]:
        base = self.index.stats()
        base.update(
            {
                "graph_version": self.GRAPH_VERSION,
                "edge_count": len(self._edges),
                "persistent_edges_path": str(self.edges_path),
                "persistent_nodes_path": str(self.nodes_path),
                "region_health": self.regions.health_snapshot(),
            }
        )
        return base

    def query_related(
        self,
        terms: list[str],
        *,
        tenant_scope: str | None = None,
        region_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        overlay = self.regions.overlay_for_query(tenant_scope=tenant_scope, region_id=region_id)
        if str(overlay.get("status") or "") not in {"healthy", "degraded", "unknown"}:
            return []
        return self.index.query_related(terms, tenant_scope=tenant_scope, limit=limit)

    def query_by_subject(
        self,
        subject: str,
        *,
        tenant_scope: str | None = None,
        region_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        _ = self.regions.overlay_for_query(tenant_scope=tenant_scope, region_id=region_id)
        return self.index.query_by_subject(subject, tenant_scope=tenant_scope, limit=limit)

    def query_provenance(self, claim_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        needle = str(claim_id or "").strip()
        if not needle:
            return []
        matches = [
            edge
            for edge in self._edges.values()
            if str(edge.get("from_id") or "") == needle or str(edge.get("to_id") or "") == needle
        ]
        return matches[-limit:]

    def query_causal(
        self,
        claim_id: str,
        *,
        depth: int | None = None,
        tenant_scope: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        start = str(claim_id or "").strip()
        if not start:
            return _wrap_ul_payload({"claim_id": claim_id, "edges": [], "nodes": []})
        max_depth = int(depth or self._config.get("default_traversal_depth") or 2)
        normalized_tenant = normalize_tenant_id(tenant_scope or "global")
        visited: set[str] = set()
        collected_edges: list[dict[str, Any]] = []

        frontier = [(start, 0)]
        while frontier:
            node_id, current_depth = frontier.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            for edge_id in self._adjacency.get(node_id, []):
                edge = dict(self._edges.get(edge_id) or {})
                if not edge:
                    continue
                edge_tenant = normalize_tenant_id(edge.get("tenant_scope") or "global")
                if normalized_tenant != "global" and edge_tenant not in {normalized_tenant, "global"}:
                    continue
                collected_edges.append(edge)
                if current_depth + 1 <= max_depth:
                    next_id = str(edge.get("to_id") or "")
                    if next_id and next_id not in visited:
                        frontier.append((next_id, current_depth + 1))

        node_ids = {start}
        for edge in collected_edges:
            node_ids.add(str(edge.get("from_id") or ""))
            node_ids.add(str(edge.get("to_id") or ""))
        claim_index = self.index.index._claims
        nodes = [
            {
                "node_id": node_id,
                "claim": claim_index.get(node_id),
            }
            for node_id in sorted(node for node in node_ids if node)
        ]
        return _wrap_ul_payload({
            "claim_id": start,
            "depth": max_depth,
            "tenant_scope": normalized_tenant,
            "region_overlay": self.regions.overlay_for_query(tenant_scope=tenant_scope),
            "edges": collected_edges[-limit:],
            "nodes": nodes[:limit],
        })

    def region_health(self) -> dict[str, Any]:
        return self.regions.health_snapshot()

    def scan_query_related(
        self,
        terms: list[str],
        *,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return self.index.scan_query_related(terms, tenant_scope=tenant_scope, limit=limit)
