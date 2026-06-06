"""Infinity 1 operator API routes — ledger, replay, plugins, brain, workflows."""

# Mythic: Operator Api Routes
# Engineering: OperatorApiRoutesEngine
from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


def _session_scope() -> str:
    body = request.get_json(silent=True) or {}
    scope = str(request.args.get("session_id") or body.get("session_id") or "").strip()
    return scope or "global"


def register_operator_api_routes(app: Flask) -> None:
    """Register operator product seam routes on the Flask app."""

    @app.route("/api/operator/ledger", methods=["GET"])
    def operator_ledger_list():
        from src.operator_decision_ledger import operator_decision_ledger_store

        scope = _session_scope()
        since = str(request.args.get("since") or "").strip() or None
        decision = str(request.args.get("decision") or "").strip() or None
        limit = int(request.args.get("limit") or 200)
        events = operator_decision_ledger_store.list_events(
            scope, since=since, limit=limit, decision_filter=decision
        )
        return jsonify({"scope_id": scope, "events": events, "count": len(events)}), 200

    @app.route("/api/operator/ledger/digest", methods=["GET"])
    def operator_ledger_digest():
        from src.operator_decision_ledger import operator_decision_ledger_store

        scope = _session_scope()
        digest = operator_decision_ledger_store.build_digest_summary(scope)
        return jsonify({"scope_id": scope, "digest": digest}), 200

    @app.route("/api/operator/ledger/query", methods=["GET"])
    def operator_ledger_query():
        from src.operator_decision_ledger_index import operator_decision_ledger_index

        scope = _session_scope()
        result = operator_decision_ledger_index.query_index(
            scope,
            kind=str(request.args.get("kind") or "").strip() or None,
            since=str(request.args.get("since") or "").strip() or None,
            tenant_id=str(request.args.get("tenant_id") or "").strip() or None,
            pending_only=str(request.args.get("pending_only") or "").strip().lower() in {"1", "true", "yes"},
            cursor=str(request.args.get("cursor") or "").strip() or None,
            limit=int(request.args.get("limit") or 200),
        )
        return jsonify(result), 200

    @app.route("/api/operator/ledger/diff", methods=["GET"])
    def operator_ledger_diff():
        from src.operator_decision_ledger import build_decision_diff

        scope = _session_scope()
        from_id = str(request.args.get("from_id") or "").strip()
        to_id = str(request.args.get("to_id") or "").strip()
        if not from_id or not to_id:
            return jsonify({"error": "from_id and to_id required"}), 400
        diff = build_decision_diff(scope, from_id, to_id)
        return jsonify({"scope_id": scope, "diff": diff}), 200

    @app.route("/api/operator/ledger/federation/<grant_id>/graph", methods=["GET"])
    def operator_ledger_federation_graph(grant_id: str):
        from src.operator_decision_ledger import build_federation_graph

        scope = _session_scope()
        graph = build_federation_graph(
            grant_id,
            home_scope=scope,
            home_tenant_id=str(request.args.get("tenant_id") or "").strip() or None,
        )
        return jsonify(graph), 200

    @app.route("/api/operator/replay/<subject_type>/<subject_id>/timeline", methods=["GET"])
    def operator_replay_timeline(subject_type: str, subject_id: str):
        from src.temporal_replay.service import build_timeline

        tenant_id = str(request.args.get("tenant_id") or "").strip() or None
        timeline = build_timeline(subject_type, subject_id, tenant_id=tenant_id)
        if str(request.args.get("rebuild") or "").strip().lower() in {"1", "true", "yes"}:
            return jsonify({"replay": timeline, **timeline}), 200
        return jsonify(timeline), 200

    @app.route("/api/operator/plugins", methods=["GET"])
    def operator_plugins_registry():
        from src.plug_adapter_runtime import plug_adapter_runtime

        snapshot = plug_adapter_runtime.registry_snapshot()
        return jsonify({"plugins": snapshot, **snapshot}), 200

    @app.route("/api/operator/plugins/libraries", methods=["GET"])
    def operator_plugins_libraries():
        from src.plug_adapter_runtime import plug_adapter_runtime

        libraries = plug_adapter_runtime.list_libraries()
        return jsonify({"libraries": libraries, "count": len(libraries)}), 200

    @app.route("/api/operator/plugins/workflows", methods=["GET"])
    def operator_plugins_workflows():
        from src.plug_adapter_runtime import plug_adapter_runtime

        workflows = plug_adapter_runtime.list_workflows()
        return jsonify({"workflows": workflows, "count": len(workflows)}), 200

    @app.route("/api/operator/plugins/rescan", methods=["POST"])
    def operator_plugins_rescan():
        from src.plug_adapter_runtime import plug_adapter_runtime

        return jsonify(plug_adapter_runtime.rescan()), 200

    @app.route("/api/operator/plugins/<plug_id>/enabled", methods=["POST"])
    def operator_plugins_set_enabled(plug_id: str):
        from src.plug_adapter_runtime import plug_adapter_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        enabled = body.get("enabled")
        if enabled is None:
            enabled = str(body.get("value", "true")).strip().lower() in {"1", "true", "yes", "on"}
        row = plug_adapter_runtime.set_plug_enabled(plug_id, bool(enabled))
        if not row:
            return jsonify({"error": "plug not found", "plug_id": plug_id}), 404
        return jsonify({"plug": row}), 200

    @app.route("/api/operator/organs", methods=["GET"])
    def operator_organs_list():
        from src.workflow_family_registry import list_workflow_families

        organs = list_workflow_families()
        return jsonify({"organs": organs, "count": len(organs)}), 200

    @app.route("/api/operator/training/adapters", methods=["GET"])
    def operator_training_adapters_list():
        from src.jarvis_lora_promotion_store import list_adapters

        adapters = list_adapters()
        return jsonify({"adapters": adapters, "count": len(adapters)}), 200

    @app.route("/api/operator/training/adapters/<run_id>", methods=["GET"])
    def operator_training_adapters_detail(run_id: str):
        from src.jarvis_lora_promotion_store import get_adapter

        adapter = get_adapter(run_id)
        if not adapter:
            return jsonify({"error": "adapter not found", "run_id": run_id}), 404
        return jsonify(adapter), 200

    @app.route("/api/operator/training/adapters/<run_id>/promote", methods=["POST"])
    def operator_training_adapters_promote(run_id: str):
        from src.jarvis_lora_promotion_store import promote_adapter

        body: dict[str, Any] = request.get_json(silent=True) or {}
        promoted_by = str(body.get("promoted_by") or "operator").strip() or "operator"
        try:
            promotion = promote_adapter(run_id, promoted_by=promoted_by)
        except ValueError as exc:
            return jsonify({"error": str(exc), "run_id": run_id}), 400
        return jsonify(promotion), 200

    @app.route("/api/operator/workflows/<workflow_id>/execute", methods=["POST"])
    def operator_workflow_execute(workflow_id: str):
        from src.workflow_chain_executor import workflow_chain_executor

        body: dict[str, Any] = request.get_json(silent=True) or {}
        run = workflow_chain_executor.execute(
            workflow_id,
            args=dict(body.get("args") or {}),
            operator_approved=bool(body.get("operator_approved")),
            dry_run=bool(body.get("dry_run", True)),
        )
        status = 200 if run.get("outcome") not in {"not_found", "blocked"} else 400
        return jsonify({"run": run, **run}), status

    @app.route("/api/operator/brain", methods=["GET"])
    def operator_brain_status():
        from src.brain_layer_runtime import build_brain_status

        status = build_brain_status()
        return jsonify({"brain": status, **status}), 200

    @app.route("/api/operator/brain/propose", methods=["POST"])
    def operator_brain_propose():
        from src.brain_layer_runtime import propose

        body: dict[str, Any] = request.get_json(silent=True) or {}
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text required"}), 400
        result = propose(text)
        return jsonify(result), 200 if result.get("ok") else 400

    @app.route("/api/operator/brain/deliberate", methods=["POST"])
    def operator_brain_deliberate():
        from src.brain_layer_runtime import deliberate_text

        body: dict[str, Any] = request.get_json(silent=True) or {}
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text required"}), 400
        session_id = str(body.get("session_id") or "").strip() or None
        return jsonify(deliberate_text(text, session_id=session_id)), 200

    @app.route("/api/operator/brain/sessions", methods=["GET"])
    def operator_brain_sessions_list():
        from src.brain_session_store import brain_session_store

        sessions = brain_session_store.list_sessions()
        return jsonify({"sessions": sessions, "count": len(sessions)}), 200

    @app.route("/api/operator/brain/sessions", methods=["POST"])
    def operator_brain_sessions_create():
        from src.brain_session_store import brain_session_store

        body: dict[str, Any] = request.get_json(silent=True) or {}
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text required"}), 400
        session = brain_session_store.create_session(
            text, include_deliberation=bool(body.get("include_deliberation"))
        )
        return jsonify({"session": session}), 201

    @app.route("/api/operator/brain/sessions/<session_id>", methods=["GET"])
    def operator_brain_sessions_detail(session_id: str):
        from src.brain_session_store import brain_session_store

        session = brain_session_store.get_session(session_id)
        if not session:
            return jsonify({"error": "session not found", "session_id": session_id}), 404
        return jsonify({"session": session, **session}), 200

    @app.route("/api/operator/brain/sessions/<session_id>/propose", methods=["POST"])
    def operator_brain_sessions_propose(session_id: str):
        from src.brain_session_store import brain_session_store

        body: dict[str, Any] = request.get_json(silent=True) or {}
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text required"}), 400
        session = brain_session_store.append_proposal(session_id, text)
        if not session:
            return jsonify({"error": "session not found", "session_id": session_id}), 404
        return jsonify({"session": session}), 200

    @app.route("/api/operator/brain/sessions/<session_id>/deliberate", methods=["POST"])
    def operator_brain_sessions_deliberate(session_id: str):
        from src.brain_session_store import brain_session_store

        body: dict[str, Any] = request.get_json(silent=True) or {}
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text required"}), 400
        session = brain_session_store.append_deliberation(session_id, text)
        if not session:
            return jsonify({"error": "session not found", "session_id": session_id}), 404
        return jsonify({"session": session}), 200

    @app.route("/api/operator/brain/sessions/<session_id>/decide", methods=["POST"])
    def operator_brain_sessions_decide(session_id: str):
        from src.brain_session_store import brain_session_store
        from src.operator_decision_ledger import append_brain_decision_event

        body: dict[str, Any] = request.get_json(silent=True) or {}
        decision = str(body.get("decision") or "").strip().lower()
        session = brain_session_store.decide(session_id, decision)
        if not session:
            return jsonify({"error": "invalid session or decision"}), 400
        scope = str(body.get("session_scope") or session_id).strip() or session_id
        try:
            append_brain_decision_event(
                scope,
                session_id=session_id,
                decision=decision,
                summary=f"brain session {decision}",
            )
        except Exception as exc:
            logger.warning("brain decision ledger emit failed: %s", exc)
        return jsonify({"session": session}), 200

    @app.route("/api/jarvis/operator-decision-ledger/status", methods=["GET"])
    def jarvis_operator_decision_ledger_status():
        from src.operator_decision_ledger import build_operator_decision_ledger_status

        scope = str(request.args.get("session_id") or "").strip() or None
        return jsonify(build_operator_decision_ledger_status(scope)), 200

    @app.route("/api/operator/dashboard/seam-health", methods=["GET"])
    def operator_dashboard_seam_health():
        from src.operator_infinity1_dashboard import build_seam_health_poll

        return jsonify(build_seam_health_poll()), 200

    @app.route("/api/operator/dashboard/monitoring", methods=["GET"])
    def operator_dashboard_monitoring():
        from src.operator_infinity1_dashboard import build_monitoring_poll

        return jsonify(build_monitoring_poll()), 200
