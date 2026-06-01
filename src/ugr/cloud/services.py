"""UGR cloud microservice apps."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify

from src.cognitive_bridge import CognitiveBridgeService, summarize_bridge_result
from src.invariant_engine import InvariantEngine
from src.ugr.cloud.service_base import create_ugr_service_app, read_json_body
from src.ugr.convergence_engine import converge_lane_results
from src.ugr.lane_manager import LaneSpec, design_lane_set, run_lanes
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.unified_pattern_ledger import UnifiedPatternLedger


def _coerce_lane_spec(spec: dict[str, Any]) -> LaneSpec:
    payload = dict(spec or {})
    return LaneSpec(
        lane_id=str(payload.get("lane_id") or ""),
        lane_type=str(payload.get("lane_type") or ""),
        priority=str(payload.get("priority") or "normal"),
        resource_budget=dict(payload.get("resource_budget") or {}),
        invariant_profile=tuple(payload.get("invariant_profile") or ()),
    )


def _runtime_root() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


def create_policy_app(bridge: CognitiveBridgeService | None = None) -> Flask:
    service = bridge or CognitiveBridgeService()

    def register(app: Flask) -> None:
        @app.route("/v1/bridge/route", methods=["POST"])
        def route_bridge():
            body = read_json_body()
            packet = dict(body.get("packet") or {})
            runtime_context = str(body.get("runtime_context") or "live_runtime")
            result = service.route_to_bridge(packet, runtime_context=runtime_context)
            return _wrap_ul_payload({
                "bridge_result": result,
                "summary": summarize_bridge_result(result),
            })

        @app.route("/v1/invariants/bridge", methods=["POST"])
        def validate_bridge_invariants():
            body = read_json_body()
            normalized = dict(body.get("normalized") or {})
            governance = dict(body.get("governance") or {})
            return InvariantEngine.validate_bridge_packet(normalized, governance)

    return create_ugr_service_app(service_id="ugr.policy", register_routes=register)


def create_ledger_app(store: PatternLedgerStore | None = None) -> Flask:
    ledger = store or PatternLedgerStore(runtime_dir=_runtime_root())
    unified = UnifiedPatternLedger(runtime_root=_runtime_root())

    def register(app: Flask) -> None:
        @app.route("/v1/ledger/claims", methods=["POST"])
        def append_claim():
            body = read_json_body()
            claim = dict(body.get("claim") or {})
            return _wrap_ul_payload({"record": ledger.append_claim(claim)})

        @app.route("/v1/ledger/query", methods=["POST"])
        def query_related():
            body = read_json_body()
            terms = list(body.get("terms") or [])
            limit = int(body.get("limit") or 20)
            tenant_scope = body.get("tenant_scope")
            if tenant_scope:
                matches = unified.read_claims(tenant_scope=str(tenant_scope), limit=limit)
            else:
                matches = ledger.query_related(terms, limit=limit)
            return _wrap_ul_payload({"matches": matches})

        @app.route("/v1/ledger/claim-id", methods=["POST"])
        def make_claim_id():
            body = read_json_body()
            claim_id = ledger.make_claim_id(
                str(body.get("subject") or ""),
                str(body.get("predicate") or ""),
                str(body.get("object") or ""),
                str(body.get("source_lane") or "convergence"),
            )
            return _wrap_ul_payload({"claim_id": claim_id})

        @app.route("/v1/ledger/pattern-events", methods=["POST"])
        def append_pattern_event():
            body = read_json_body()
            event = dict(body.get("event") or body)
            return _wrap_ul_payload({"record": ledger.append_pattern_event(event, mirror_legacy=bool(body.get("mirror_legacy", False)))})

        @app.route("/v1/ledger/cogos/sync", methods=["POST"])
        def sync_cogos_patterns():
            body = read_json_body()
            rows = list(body.get("rows") or [])
            if rows:
                return ledger.sync_cogos_patterns(rows=rows)
            return ledger.sync_cogos_patterns(source_path=body.get("source_path"))

    return create_ugr_service_app(service_id="ugr.ledger", register_routes=register)


def create_lane_worker_app(store: PatternLedgerStore | None = None) -> Flask:
    ledger = store or PatternLedgerStore(runtime_dir=_runtime_root())

    def register(app: Flask) -> None:
        @app.route("/v1/lanes/run", methods=["POST"])
        def run_lane_batch():
            body = read_json_body()
            trace_id = str(body.get("trace_id") or "")
            specs = [_coerce_lane_spec(spec) for spec in list(body.get("lane_specs") or [])]
            shared_context = dict(body.get("shared_context") or {})
            results = run_lanes(trace_id, specs, shared_context, ledger=ledger)
            return _wrap_ul_payload({"lane_results": [item.to_dict() for item in results]})

        @app.route("/v1/lanes/design", methods=["POST"])
        def design_lanes():
            body = read_json_body()
            intent = str(body.get("intent") or "general_qa")
            lane_types = list(body.get("lane_types") or [])
            specs = design_lane_set(intent, lane_types or None)
            return _wrap_ul_payload({"lane_specs": [spec.to_dict() for spec in specs]})

    return create_ugr_service_app(service_id="ugr.lane_worker", register_routes=register)


def create_convergence_app() -> Flask:
    def register(app: Flask) -> None:
        @app.route("/v1/convergence/merge", methods=["POST"])
        def merge():
            body = read_json_body()
            trace_id = str(body.get("trace_id") or "")
            lane_results = list(body.get("lane_results") or [])
            request_payload = dict(body.get("request") or {})
            policy_context = dict(body.get("policy_context") or {})
            return converge_lane_results(
                trace_id,
                lane_results,
                request=request_payload,
                policy_context=policy_context,
            )

    return create_ugr_service_app(service_id="ugr.convergence", register_routes=register)


def create_orchestrator_app(runtime: Any | None = None) -> Flask:
    from src.ugr.cloud.distributed_runtime import DistributedUnifiedGovernedRuntime

    orchestrator = runtime or DistributedUnifiedGovernedRuntime()

    def register(app: Flask) -> None:
        @app.route("/v1/deliberate", methods=["POST"])
        def deliberate():
            body = read_json_body()
            return orchestrator.handle_request(body)

    return create_ugr_service_app(service_id="ugr.orchestrator", service_version="0.2", register_routes=register)


def create_ingestion_app(pipeline: Any | None = None) -> Flask:
    from src.ugr.ingestion.pipeline import GovernedIngestionPipeline

    worker = pipeline or GovernedIngestionPipeline(runtime_root=_runtime_root())

    def register(app: Flask) -> None:
        @app.route("/v1/ingestion/run", methods=["POST"])
        def run_ingestion():
            body = read_json_body()
            source_id = str(body.get("source_id") or "").strip()
            if not source_id:
                return jsonify({"error": "source_id is required"}), 400
            dry_run = bool(body.get("dry_run"))
            records = body.get("records")
            result = worker.run_source(
                source_id,
                dry_run=dry_run,
                records=list(records) if isinstance(records, list) else None,
            )
            return result.to_dict()

        @app.route("/v1/ingestion/sources", methods=["GET"])
        def list_sources():
            return _wrap_ul_payload({
                "sources": [source.to_dict() for source in worker.config.sources.values()],
                "enabled": [source.source_id for source in worker.config.enabled_sources()],
            })

        @app.route("/v1/ingestion/run-enabled", methods=["POST"])
        def run_enabled():
            body = read_json_body()
            dry_run = bool(body.get("dry_run"))
            return _wrap_ul_payload({"runs": worker.run_enabled_sources(dry_run=dry_run)})

    return create_ugr_service_app(service_id="ugr.ingestion", service_version="0.1", register_routes=register)


def create_platform_app(
    *,
    tenants: Any | None = None,
    ledger: Any | None = None,
    cicd: Any | None = None,
) -> Flask:
    from src.ugr.platform.cognition_cicd import CognitionCICDPipeline
    from src.ugr.platform.graph_shard import GraphShardRouter
    from src.ugr.platform.sharded_ledger import ShardedPatternLedger
    from src.ugr.platform.tenant_registry import TenantRegistry

    registry = tenants or TenantRegistry()
    sharded = ledger or ShardedPatternLedger(runtime_root=_runtime_root())
    router = GraphShardRouter(runtime_root=_runtime_root())
    pipeline = cicd or CognitionCICDPipeline()

    def register(app: Flask) -> None:
        @app.route("/v1/platform/tenants", methods=["GET"])
        def list_tenants():
            return _wrap_ul_payload({"tenants": [tenant.to_dict() for tenant in registry.list_tenants()]})

        @app.route("/v1/platform/shards", methods=["GET"])
        def list_shards():
            return _wrap_ul_payload({"shards": [shard.to_dict() for shard in router.list_shards()]})

        @app.route("/v1/platform/ledger/query", methods=["POST"])
        def query_overlay():
            body = read_json_body()
            terms = list(body.get("terms") or [])
            tenant_scope = body.get("tenant_scope")
            limit = int(body.get("limit") or 20)
            matches = sharded.query_related(terms, tenant_scope=tenant_scope, limit=limit)
            return _wrap_ul_payload({"matches": matches})

        @app.route("/v1/platform/shadow-eval", methods=["POST"])
        def shadow_eval():
            body = read_json_body()
            return pipeline.evaluator.evaluate(body)

        @app.route("/v1/platform/cicd/evaluate", methods=["POST"])
        def cicd_evaluate():
            body = read_json_body()
            if body.get("comparison"):
                return pipeline.evaluate_comparison(dict(body.get("comparison") or {}))
            return pipeline.evaluate(body)

    return create_ugr_service_app(service_id="ugr.platform", service_version="0.1", register_routes=register)


def create_graph_index_app(store: PatternLedgerStore | None = None) -> Flask:
    from src.ugr.graph_index.store import GraphIndexStore, graph_index_enabled

    ledger = store or PatternLedgerStore(runtime_dir=_runtime_root())
    graph = (
        ledger._graph
        if getattr(ledger, "_graph", None) is not None
        else GraphIndexStore(runtime_root=_runtime_root(), ledger=ledger._ledger)
    )

    def register(app: Flask) -> None:
        @app.route("/v1/graph/stats", methods=["GET"])
        def stats():
            return _wrap_ul_payload({
                "enabled": graph_index_enabled(),
                "stats": graph.stats(),
            })

        @app.route("/v1/graph/rebuild", methods=["POST"])
        def rebuild():
            return graph.rebuild()

        @app.route("/v1/graph/query", methods=["POST"])
        def query():
            body = read_json_body()
            terms = list(body.get("terms") or [])
            tenant_scope = body.get("tenant_scope")
            limit = int(body.get("limit") or 20)
            subject = body.get("subject")
            if subject:
                matches = graph.query_by_subject(str(subject), tenant_scope=tenant_scope, limit=limit)
            else:
                matches = graph.query_related(terms, tenant_scope=tenant_scope, limit=limit)
            return _wrap_ul_payload({"matches": matches, "stats": graph.stats()})

        @app.route("/v1/graph/related", methods=["POST"])
        def related_sp():
            body = read_json_body()
            matches = graph.index.related_by_subject_predicate(
                str(body.get("subject") or ""),
                str(body.get("predicate") or ""),
                tenant_scope=body.get("tenant_scope"),
                limit=int(body.get("limit") or 20),
            )
            return _wrap_ul_payload({"matches": matches})

    return create_ugr_service_app(service_id="ugr.graph_index", service_version="0.1", register_routes=register)


def create_causal_graph_app(store: PatternLedgerStore | None = None) -> Flask:
    from src.ugr.causal_graph.store import CausalGraphStore, causal_graph_enabled

    ledger = store or PatternLedgerStore(runtime_dir=_runtime_root())
    graph = (
        ledger._graph
        if getattr(ledger, "_graph", None) is not None and isinstance(ledger._graph, CausalGraphStore)
        else CausalGraphStore(runtime_root=_runtime_root(), ledger=ledger._ledger)
    )

    def register(app: Flask) -> None:
        @app.route("/v1/causal/stats", methods=["GET"])
        def stats():
            return _wrap_ul_payload({
                "enabled": causal_graph_enabled(),
                "stats": graph.stats(),
            })

        @app.route("/v1/causal/rebuild", methods=["POST"])
        def rebuild():
            return graph.rebuild()

        @app.route("/v1/causal/query", methods=["POST"])
        def causal_query():
            body = read_json_body()
            claim_id = str(body.get("claim_id") or "").strip()
            if not claim_id:
                return jsonify({"error": "claim_id is required"}), 400
            return graph.query_causal(
                claim_id,
                depth=body.get("depth"),
                tenant_scope=body.get("tenant_scope"),
                limit=int(body.get("limit") or 50),
            )

        @app.route("/v1/causal/provenance", methods=["POST"])
        def provenance_query():
            body = read_json_body()
            claim_id = str(body.get("claim_id") or "").strip()
            if not claim_id:
                return jsonify({"error": "claim_id is required"}), 400
            edges = graph.query_provenance(claim_id, limit=int(body.get("limit") or 50))
            return _wrap_ul_payload({"claim_id": claim_id, "edges": edges, "stats": graph.stats()})

        @app.route("/v1/causal/regions/health", methods=["GET"])
        def regions_health():
            return graph.region_health()

    return create_ugr_service_app(service_id="ugr.causal_graph", service_version="1.0", register_routes=register)


def create_embryo_v1_gateway_app(gateway: Any | None = None) -> Flask:
    from src.ugr.embryo.gateway_v1 import UGREmbryoGatewayV1

    embryo = gateway or UGREmbryoGatewayV1()

    def register(app: Flask) -> None:
        @app.route("/v1/embryo/health", methods=["GET"])
        def health():
            return embryo.health()

        @app.route("/v1/embryo/causal/query", methods=["POST"])
        def causal_query():
            body = read_json_body()
            claim_id = str(body.get("claim_id") or "").strip()
            if not claim_id:
                return jsonify({"error": "claim_id is required"}), 400
            return embryo.causal_query(
                claim_id=claim_id,
                depth=body.get("depth"),
                tenant_scope=body.get("tenant_scope"),
                limit=int(body.get("limit") or 50),
            )

        @app.route("/v1/embryo/provenance", methods=["POST"])
        def provenance_query():
            body = read_json_body()
            claim_id = str(body.get("claim_id") or "").strip()
            if not claim_id:
                return jsonify({"error": "claim_id is required"}), 400
            return embryo.provenance_query(claim_id=claim_id, limit=int(body.get("limit") or 50))

        @app.route("/v1/embryo/regions/health", methods=["GET"])
        def regions_health():
            return embryo.regions_health()

        @app.route("/v1/embryo/causal/rebuild", methods=["POST"])
        def causal_rebuild():
            return embryo.rebuild_causal_graph()

    return create_ugr_service_app(service_id="ugr.embryo_gateway_v1", service_version="1.0", register_routes=register)


def create_model_pool_app(router: Any | None = None) -> Flask:
    from src.ugr.embryo.model_pool import ModelPoolRouter

    pool = router or ModelPoolRouter()

    def register(app: Flask) -> None:
        @app.route("/v1/model-pool/slots", methods=["GET"])
        def list_slots():
            return _wrap_ul_payload({"slots": pool.list_slots(), "config_version": pool.config.get("pool_version")})

        @app.route("/v1/model-pool/resolve", methods=["POST"])
        def resolve():
            body = read_json_body()
            request_payload = dict(body.get("request") or {})
            trace_id = str(body.get("trace_id") or request_payload.get("trace_id") or "pool-resolve")
            slot = pool.resolve(
                request=request_payload,
                trace_id=trace_id,
                cloud_forge=dict(body.get("cloud_forge") or {}),
                lane_results=list(body.get("lane_results") or []),
                bridge_result=dict(body.get("bridge") or {}),
            )
            return _wrap_ul_payload({"model_pool": slot})

    return create_ugr_service_app(service_id="ugr.model_pool", service_version="0.1", register_routes=register)


def create_embryo_gateway_app(gateway: Any | None = None) -> Flask:
    from src.ugr.embryo.gateway import UGREmbryoGateway

    embryo = gateway or UGREmbryoGateway()

    def register(app: Flask) -> None:
        @app.route("/v1/embryo/health", methods=["GET"])
        def health():
            return embryo.health()

        @app.route("/v1/embryo/deliberate", methods=["POST"])
        def deliberate():
            body = read_json_body()
            return embryo.deliberate(body)

        @app.route("/v1/embryo/ingest", methods=["POST"])
        def ingest():
            body = read_json_body()
            source_id = str(body.get("source_id") or "").strip()
            if not source_id:
                return jsonify({"error": "source_id is required"}), 400
            return embryo.ingest(source_id=source_id, dry_run=bool(body.get("dry_run")))

        @app.route("/v1/embryo/ingest/sources", methods=["GET"])
        def ingest_sources():
            return embryo.ingest_sources()

        @app.route("/v1/embryo/graph/query", methods=["POST"])
        def graph_query():
            body = read_json_body()
            terms = list(body.get("terms") or [])
            subject = body.get("subject")
            if not subject and not terms:
                return jsonify({"error": "terms or subject is required"}), 400
            return embryo.graph_query(
                terms=terms,
                subject=str(subject) if subject else None,
                tenant_scope=body.get("tenant_scope"),
                limit=int(body.get("limit") or 20),
            )

        @app.route("/v1/embryo/graph/rebuild", methods=["POST"])
        def graph_rebuild():
            return embryo.rebuild_graph_index()

        @app.route("/v1/embryo/shadow-eval", methods=["POST"])
        def shadow_eval():
            body = read_json_body()
            return embryo.shadow_eval(body)

    return create_ugr_service_app(service_id="ugr.embryo_gateway", service_version="0.1", register_routes=register)
