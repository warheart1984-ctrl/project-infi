"""UGR embryo v0 gateway — single ingress for deliberation, ingestion, and graph."""

# Mythic: Gateway
# Engineering: GatewayEngine
from __future__ import annotations

from typing import Any

from src.ugr.embryo.health import probe_embryo_health
from src.ugr.embryo.model_pool import ModelPoolRouter, attach_model_pool_to_response


UGR_EMBRYO_ID = "aais.ugr.embryo"
UGR_EMBRYO_VERSION = "0.1"
UGR_GATEWAY_SURFACE = "v0"


def wrap_embryo_envelope(
    operation: str,
    payload: dict[str, Any],
    *,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Attach embryo metadata to any gateway operation result."""
    health = probe_embryo_health(runtime=runtime)
    wrapped = dict(payload)
    wrapped["embryo"] = {
        "embryo_id": UGR_EMBRYO_ID,
        "embryo_version": UGR_EMBRYO_VERSION,
        "gateway_surface": UGR_GATEWAY_SURFACE,
        "operation": operation,
        "trace_id": payload.get("trace_id"),
        "rail_decision": payload.get("rail_decision"),
        "model_pool": payload.get("model_pool"),
        "component_health": health.get("components"),
        "claim_status": "asserted",
    }
    return wrapped


class UGREmbryoGateway:
    """Cloud super-LLM embryo v0 — orchestrates governed runtime surfaces."""

    def __init__(self, *, runtime: Any | None = None, model_pool: ModelPoolRouter | None = None):
        if runtime is None:
            from src.ugr.unified_runtime import build_ugr_runtime

            runtime = build_ugr_runtime()
        self.runtime = runtime
        self.model_pool = model_pool or ModelPoolRouter()

    def deliberate(self, request: dict[str, Any] | None) -> dict[str, Any]:
        payload = dict(request or {})
        question = str(payload.get("question") or "").strip()
        if not question:
            return wrap_embryo_envelope(
                "deliberate",
                {"status": "rejected", "summary": "question is required", "trace_id": None},
                runtime=self.runtime,
            )
        result = self.runtime.handle_request(payload)
        if not result.get("model_pool"):
            result = attach_model_pool_to_response(result, payload, router=self.model_pool)
        return wrap_embryo_envelope("deliberate", result, runtime=self.runtime)

    def ingest(self, *, source_id: str, dry_run: bool = False) -> dict[str, Any]:
        from src.ugr.ingestion.pipeline import GovernedIngestionPipeline

        pipeline = GovernedIngestionPipeline()
        result = pipeline.run_source(source_id, dry_run=dry_run).to_dict()
        return wrap_embryo_envelope("ingest", result, runtime=self.runtime)

    def ingest_sources(self) -> dict[str, Any]:
        from src.ugr.ingestion.config import IngestionConfig

        config = IngestionConfig()
        payload = {
            "status": "ok",
            "sources": [source.to_dict() for source in config.sources.values()],
            "enabled": [source.source_id for source in config.enabled_sources()],
        }
        return wrap_embryo_envelope("ingest_sources", payload, runtime=self.runtime)

    def graph_query(
        self,
        *,
        terms: list[str] | None = None,
        subject: str | None = None,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        ledger = getattr(self.runtime, "ledger", None)
        if ledger is None:
            return wrap_embryo_envelope(
                "graph_query",
                {"status": "error", "summary": "ledger unavailable"},
                runtime=self.runtime,
            )
        if subject:
            matches = ledger.query_by_subject(str(subject), tenant_scope=tenant_scope, limit=limit)
        else:
            matches = ledger.query_related(list(terms or []), tenant_scope=tenant_scope, limit=limit)
        payload = {
            "status": "ok",
            "matches": matches,
            "stats": ledger.graph_index_stats(),
        }
        return wrap_embryo_envelope("graph_query", payload, runtime=self.runtime)

    def rebuild_graph_index(self) -> dict[str, Any]:
        ledger = getattr(self.runtime, "ledger", None)
        if ledger is None:
            return wrap_embryo_envelope(
                "graph_rebuild",
                {"status": "error", "summary": "ledger unavailable"},
                runtime=self.runtime,
            )
        result = ledger.rebuild_graph_index()
        if result is None:
            payload = {"status": "rejected", "summary": "UGR_GRAPH_ENABLED is not active"}
        else:
            payload = {"status": "ok", **dict(result or {})}
        return wrap_embryo_envelope("graph_rebuild", payload, runtime=self.runtime)

    def health(self) -> dict[str, Any]:
        payload = probe_embryo_health(runtime=self.runtime)
        return wrap_embryo_envelope("health", payload, runtime=self.runtime)

    def shadow_eval(self, request: dict[str, Any] | None) -> dict[str, Any]:
        from src.ugr.platform.shadow_runtime import ShadowRuntimeEvaluator

        payload = dict(request or {})
        question = str(payload.get("question") or "").strip()
        if not question:
            return wrap_embryo_envelope(
                "shadow_eval",
                {"status": "rejected", "summary": "question is required"},
                runtime=self.runtime,
            )
        evaluator = ShadowRuntimeEvaluator()
        result = evaluator.evaluate(payload)
        return wrap_embryo_envelope("shadow_eval", result, runtime=self.runtime)
