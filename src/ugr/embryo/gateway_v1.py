"""UGR embryo v1 gateway — causal graph, provenance, and region health."""

from __future__ import annotations

from typing import Any

from src.ugr.causal_graph.store import causal_graph_enabled
from src.ugr.embryo.gateway import UGREmbryoGateway, wrap_embryo_envelope


UGR_EMBRYO_V1_VERSION = "1.0"
UGR_GATEWAY_V1_SURFACE = "v1"


def wrap_embryo_v1_envelope(operation: str, payload: dict[str, Any], *, runtime: Any | None = None) -> dict[str, Any]:
    wrapped = wrap_embryo_envelope(operation, payload, runtime=runtime)
    embryo = dict(wrapped.get("embryo") or {})
    embryo["embryo_version"] = UGR_EMBRYO_V1_VERSION
    embryo["gateway_surface"] = UGR_GATEWAY_V1_SURFACE
    embryo["causal_graph_enabled"] = causal_graph_enabled()
    wrapped["embryo"] = embryo
    return wrapped


class UGREmbryoGatewayV1(UGREmbryoGateway):
    """Embryo v1 — extends v0 with persistent causal graph queries."""

    def _require_causal_graph(self) -> dict[str, Any] | None:
        if not causal_graph_enabled():
            return {
                "status": "rejected",
                "summary": "UGR_CAUSAL_GRAPH_ENABLED is not active",
            }
        return None

    def causal_query(
        self,
        *,
        claim_id: str,
        depth: int | None = None,
        tenant_scope: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        rejected = self._require_causal_graph()
        if rejected:
            return wrap_embryo_v1_envelope("causal_query", rejected, runtime=self.runtime)
        needle = str(claim_id or "").strip()
        if not needle:
            return wrap_embryo_v1_envelope(
                "causal_query",
                {"status": "rejected", "summary": "claim_id is required"},
                runtime=self.runtime,
            )
        ledger = getattr(self.runtime, "ledger", None)
        if ledger is None:
            return wrap_embryo_v1_envelope(
                "causal_query",
                {"status": "error", "summary": "ledger unavailable"},
                runtime=self.runtime,
            )
        result = ledger.query_causal(
            needle,
            depth=depth,
            tenant_scope=tenant_scope,
            limit=limit,
        )
        payload = {"status": "ok", **result}
        return wrap_embryo_v1_envelope("causal_query", payload, runtime=self.runtime)

    def provenance_query(self, *, claim_id: str, limit: int = 50) -> dict[str, Any]:
        rejected = self._require_causal_graph()
        if rejected:
            return wrap_embryo_v1_envelope("provenance_query", rejected, runtime=self.runtime)
        needle = str(claim_id or "").strip()
        if not needle:
            return wrap_embryo_v1_envelope(
                "provenance_query",
                {"status": "rejected", "summary": "claim_id is required"},
                runtime=self.runtime,
            )
        ledger = getattr(self.runtime, "ledger", None)
        if ledger is None:
            return wrap_embryo_v1_envelope(
                "provenance_query",
                {"status": "error", "summary": "ledger unavailable"},
                runtime=self.runtime,
            )
        edges = ledger.query_provenance(needle, limit=limit)
        payload = {
            "status": "ok",
            "claim_id": needle,
            "edges": edges,
            "stats": ledger.graph_index_stats(),
        }
        return wrap_embryo_v1_envelope("provenance_query", payload, runtime=self.runtime)

    def regions_health(self) -> dict[str, Any]:
        rejected = self._require_causal_graph()
        if rejected:
            return wrap_embryo_v1_envelope("regions_health", rejected, runtime=self.runtime)
        ledger = getattr(self.runtime, "ledger", None)
        snapshot = ledger.region_health() if ledger is not None else None
        if snapshot is None:
            return wrap_embryo_v1_envelope(
                "regions_health",
                {"status": "error", "summary": "region health unavailable"},
                runtime=self.runtime,
            )
        return wrap_embryo_v1_envelope(
            "regions_health",
            {"status": "ok", **snapshot},
            runtime=self.runtime,
        )

    def rebuild_causal_graph(self) -> dict[str, Any]:
        rejected = self._require_causal_graph()
        if rejected:
            return wrap_embryo_v1_envelope("causal_rebuild", rejected, runtime=self.runtime)
        ledger = getattr(self.runtime, "ledger", None)
        if ledger is None:
            return wrap_embryo_v1_envelope(
                "causal_rebuild",
                {"status": "error", "summary": "ledger unavailable"},
                runtime=self.runtime,
            )
        result = ledger.rebuild_graph_index()
        payload = {"status": "ok", **dict(result or {})}
        return wrap_embryo_v1_envelope("causal_rebuild", payload, runtime=self.runtime)

    def health(self) -> dict[str, Any]:
        payload = super().health()
        embryo = dict(payload.get("embryo") or {})
        embryo["embryo_version"] = UGR_EMBRYO_V1_VERSION
        embryo["gateway_surface"] = UGR_GATEWAY_V1_SURFACE
        embryo["causal_graph_enabled"] = causal_graph_enabled()
        ledger = getattr(self.runtime, "ledger", None)
        if ledger is not None:
            embryo["region_health"] = ledger.region_health()
        payload["embryo"] = embryo
        return payload
