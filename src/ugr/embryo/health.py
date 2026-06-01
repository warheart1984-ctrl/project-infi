"""Embryo v0 component health probes."""

from __future__ import annotations

from typing import Any

from src.ugr.embryo.model_pool import ModelPoolRouter


def probe_embryo_health(*, runtime: Any | None = None) -> dict[str, Any]:
    """Return health snapshot for embryo v0 components."""
    router = ModelPoolRouter()
    ingestion_enabled = 0
    try:
        from src.ugr.ingestion.config import IngestionConfig

        ingestion_enabled = len(IngestionConfig().enabled_sources())
    except Exception:
        ingestion_enabled = 0

    graph_stats = None
    region_health = None
    causal_enabled = False
    if runtime is not None and hasattr(runtime, "ledger"):
        graph_stats = runtime.ledger.graph_index_stats()
        region_health = runtime.ledger.region_health()
        try:
            from src.ugr.causal_graph.store import causal_graph_enabled

            causal_enabled = causal_graph_enabled()
        except Exception:
            causal_enabled = False

    return {
        "status": "ok",
        "components": {
            "orchestrator": {"status": "ok", "runtime_id": getattr(runtime, "runtime_dir", None) is not None},
            "pattern_ledger": {
                "status": "ok",
                "graph_index": graph_stats,
                "causal_graph_enabled": causal_enabled,
                "region_health": region_health,
            },
            "ingestion": {
                "status": "ok" if ingestion_enabled else "degraded",
                "enabled_sources": ingestion_enabled,
            },
            "invariants": {"status": "ok", "engine": "aais.invariant_engine.bridge_guard"},
            "immune": {"status": "ok", "surface": "immune_system"},
            "model_pool": {
                "status": "ok",
                "slots": len(router.list_slots()),
                "pool_version": router.config.get("pool_version"),
            },
        },
    }
