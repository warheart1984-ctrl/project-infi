"""Infinity 1 operator API routes — ledger, replay, plugins, brain, workflows."""

# Mythic: Operator Api Routes
# Engineering: OperatorApiRoutesEngine
from __future__ import annotations

import logging
import os
from typing import Any

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


def require_workos_operator_permission(route_key: str):
    """Apply WorkOS RBAC to operator routes when AAIS_WORKOS_BRIDGE is enabled."""
    from src.workos_governance_bridge import OPERATOR_ROUTE_PERMISSIONS, require_workos_permission

    permission = OPERATOR_ROUTE_PERMISSIONS.get(route_key)
    if not permission:
        def passthrough(view):
            return view

        return passthrough
    return require_workos_permission(permission)


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
    @require_workos_operator_permission("POST /api/operator/plugins/rescan")
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
        from src.workflow_family_readiness import list_families_with_readiness

        organs = list_families_with_readiness()
        return jsonify({"organs": organs, "count": len(organs)}), 200

    @app.route("/api/operator/organs/<family_id>", methods=["GET"])
    def operator_organs_detail(family_id: str):
        from src.workflow_family_readiness import family_detail_with_readiness

        detail = family_detail_with_readiness(family_id)
        if not detail:
            return jsonify({"error": "organ not found", "family_id": family_id}), 404
        return jsonify({"organ": detail, **detail}), 200

    @app.route("/api/operator/organs/mesh", methods=["GET"])
    def operator_organs_mesh():
        from src.organ_coordination_runtime import organ_coordination_runtime

        return jsonify(organ_coordination_runtime.mesh_snapshot()), 200

    @app.route("/api/operator/organs/mesh/plan", methods=["POST"])
    def operator_organs_mesh_plan():
        from src.organ_coordination_runtime import organ_coordination_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        plan = organ_coordination_runtime.plan_mesh_run(
            intent_text=str(body.get("intent_text") or body.get("text") or ""),
            source_family_id=str(body.get("source_family_id") or "") or None,
            handoff_edge_index=int(body.get("handoff_edge_index") or 0),
        )
        status = 200 if plan.get("outcome") != "blocked" else 400
        return jsonify({"plan": plan, **plan}), status

    @app.route("/api/operator/organs/mesh/runs", methods=["POST"])
    def operator_organs_mesh_runs():
        from src.jarvis_organ_mesh_authority import authorize_mesh_run
        from src.organ_coordination_runtime import organ_coordination_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        session_id = str(body.get("session_id") or "global")
        operator_approved = bool(body.get("operator_approved"))
        dry_run = bool(body.get("dry_run", True))
        operator_ack = bool(body.get("operator_ack"))
        plan = dict(body.get("plan") or {})
        if not plan:
            plan = organ_coordination_runtime.plan_mesh_run(
                intent_text=str(body.get("intent_text") or body.get("text") or ""),
            )
        auth = authorize_mesh_run(plan, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False}), 403
        run = organ_coordination_runtime.execute_mesh_run(
            plan,
            session_id=session_id,
            operator_approved=operator_approved,
            dry_run=dry_run,
            operator_ack=operator_ack,
            jarvis_authorization=auth,
        )
        if run.get("reason") == "occ2_requires_operator_ack":
            return jsonify({"error": run.get("reason"), "run": run}), 403
        status = 200 if run.get("outcome") == "completed" else 400
        return jsonify({"run": run, **run}), status

    @app.route("/api/operator/organs/mesh/runs/<run_id>", methods=["GET"])
    def operator_organs_mesh_run_detail(run_id: str):
        from src.organ_coordination_runtime import organ_coordination_runtime

        run = organ_coordination_runtime.get_run(run_id)
        if not run:
            return jsonify({"error": "run not found", "run_id": run_id}), 404
        return jsonify({"run": run, **run}), 200

    @app.route("/api/operator/culture", methods=["GET"])
    def operator_culture_snapshot():
        from src.culture_habit_runtime import culture_habit_runtime

        return jsonify(culture_habit_runtime.culture_snapshot()), 200

    @app.route("/api/operator/culture/observe", methods=["POST"])
    def operator_culture_observe():
        from src.culture_habit_runtime import culture_habit_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = culture_habit_runtime.mine_habit_patterns(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/culture/habits", methods=["GET"])
    def operator_culture_habits_list():
        from src.culture_habit_registry import adopted_habits
        from src.culture_habit_runtime import culture_habit_runtime

        return jsonify(
            {
                "adopted_habits": adopted_habits(),
                "recent_candidates": culture_habit_runtime.list_candidates(limit=50),
                "posture": culture_habit_runtime.culture_posture(),
            }
        ), 200

    @app.route("/api/operator/culture/habits/adopt", methods=["POST"])
    def operator_culture_habits_adopt():
        from src.culture_habit_runtime import culture_habit_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("habit_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in culture_habit_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        result = culture_habit_runtime.adopt_habit(
            candidate,
            operator_approved=bool(body.get("operator_approved")),
            session_id=str(body.get("session_id") or "global"),
        )
        if result.get("reason") == "operator_approved required":
            return jsonify({"error": result.get("reason"), **result}), 403
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/identity", methods=["GET"])
    def operator_identity_snapshot():
        from src.identity_self_model_runtime import identity_self_model_runtime

        return jsonify(identity_self_model_runtime.identity_snapshot()), 200

    @app.route("/api/operator/identity/observe", methods=["POST"])
    def operator_identity_observe():
        from src.identity_self_model_runtime import identity_self_model_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = identity_self_model_runtime.observe_identity_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/identity/claims", methods=["GET"])
    def operator_identity_claims_list():
        from src.identity_self_model_registry import adopted_claims
        from src.identity_self_model_runtime import identity_self_model_runtime

        return jsonify(
            {
                "adopted_claims": adopted_claims(),
                "recent_candidates": identity_self_model_runtime.list_candidates(limit=50),
                "posture": identity_self_model_runtime.identity_posture(),
            }
        ), 200

    @app.route("/api/operator/identity/claims/adopt", methods=["POST"])
    def operator_identity_claims_adopt():
        from src.jarvis_identity_authority import authorize_foundation_admission
        from src.identity_self_model_runtime import identity_self_model_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("identity_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in identity_self_model_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_foundation_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = identity_self_model_runtime.adopt_identity_claim(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/narrative", methods=["GET"])
    def operator_narrative_snapshot():
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        return jsonify(narrative_continuity_runtime.narrative_snapshot()), 200

    @app.route("/api/operator/narrative/observe", methods=["POST"])
    def operator_narrative_observe():
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = narrative_continuity_runtime.observe_narrative_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/narrative/beats", methods=["GET"])
    def operator_narrative_beats_list():
        from src.narrative_continuity_registry import adopted_beats
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        return jsonify(
            {
                "adopted_beats": adopted_beats(),
                "recent_candidates": narrative_continuity_runtime.list_candidates(limit=50),
                "posture": narrative_continuity_runtime.narrative_posture(),
            }
        ), 200

    @app.route("/api/operator/narrative/beats/adopt", methods=["POST"])
    def operator_narrative_beats_adopt():
        from src.jarvis_narrative_authority import authorize_session_admission
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("narrative_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in narrative_continuity_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_session_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = narrative_continuity_runtime.adopt_narrative_beat(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/autobiographical", methods=["GET"])
    def operator_autobiographical_snapshot():
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        return jsonify(autobiographical_agency_runtime.autobiographical_snapshot()), 200

    @app.route("/api/operator/autobiographical/observe", methods=["POST"])
    def operator_autobiographical_observe():
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = autobiographical_agency_runtime.observe_autobiographical_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/autobiographical/episodes", methods=["GET"])
    def operator_autobiographical_episodes_list():
        from src.autobiographical_agency_registry import adopted_episodes
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        return jsonify(
            {
                "adopted_episodes": adopted_episodes(),
                "recent_candidates": autobiographical_agency_runtime.list_candidates(limit=50),
                "posture": autobiographical_agency_runtime.autobiographical_posture(),
            }
        ), 200

    @app.route("/api/operator/autobiographical/episodes/adopt", methods=["POST"])
    def operator_autobiographical_episodes_adopt():
        from src.jarvis_autobiographical_authority import authorize_operational_admission
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("autobiographical_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in autobiographical_agency_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_operational_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = autobiographical_agency_runtime.adopt_autobiographical_episode(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/social", methods=["GET"])
    def operator_social_snapshot():
        from src.social_continuity_runtime import social_continuity_runtime

        return jsonify(social_continuity_runtime.social_snapshot()), 200

    @app.route("/api/operator/social/observe", methods=["POST"])
    def operator_social_observe():
        from src.social_continuity_runtime import social_continuity_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = social_continuity_runtime.observe_social_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/social/bonds", methods=["GET"])
    def operator_social_bonds_list():
        from src.social_continuity_registry import adopted_bonds
        from src.social_continuity_runtime import social_continuity_runtime

        return jsonify(
            {
                "adopted_bonds": adopted_bonds(),
                "recent_candidates": social_continuity_runtime.list_candidates(limit=50),
                "posture": social_continuity_runtime.social_posture(),
            }
        ), 200

    @app.route("/api/operator/social/bonds/adopt", methods=["POST"])
    def operator_social_bonds_adopt():
        from src.jarvis_social_authority import authorize_archive_admission
        from src.social_continuity_runtime import social_continuity_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("social_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in social_continuity_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_archive_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = social_continuity_runtime.adopt_social_bond(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/multi-being", methods=["GET"])
    def operator_multi_being_snapshot():
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        return jsonify(multi_being_continuity_runtime.multi_being_snapshot()), 200

    @app.route("/api/operator/multi-being/observe", methods=["POST"])
    def operator_multi_being_observe():
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = multi_being_continuity_runtime.observe_multi_being_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/multi-being/pacts", methods=["GET"])
    def operator_multi_being_pacts_list():
        from src.multi_being_continuity_registry import adopted_pacts
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        return jsonify(
            {
                "adopted_pacts": adopted_pacts(),
                "recent_candidates": multi_being_continuity_runtime.list_candidates(limit=50),
                "posture": multi_being_continuity_runtime.multi_being_posture(),
            }
        ), 200

    @app.route("/api/operator/multi-being/pacts/adopt", methods=["POST"])
    def operator_multi_being_pacts_adopt():
        from src.jarvis_multi_being_authority import authorize_federation_slot_admission
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("multi_being_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in multi_being_continuity_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_federation_slot_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = multi_being_continuity_runtime.adopt_multi_being_pact(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/culture-of-beings", methods=["GET"])
    def operator_culture_of_beings_snapshot():
        from src.culture_of_beings_runtime import culture_of_beings_runtime

        return jsonify(culture_of_beings_runtime.culture_of_beings_snapshot()), 200

    @app.route("/api/operator/culture-of-beings/observe", methods=["POST"])
    def operator_culture_of_beings_observe():
        from src.culture_of_beings_runtime import culture_of_beings_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = culture_of_beings_runtime.observe_culture_of_beings_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/culture-of-beings/norms", methods=["GET"])
    def operator_culture_of_beings_norms_list():
        from src.culture_of_beings_registry import adopted_norms
        from src.culture_of_beings_runtime import culture_of_beings_runtime

        return jsonify(
            {
                "adopted_norms": adopted_norms(),
                "recent_candidates": culture_of_beings_runtime.list_candidates(limit=50),
                "posture": culture_of_beings_runtime.culture_of_beings_posture(),
            }
        ), 200

    @app.route("/api/operator/culture-of-beings/norms/adopt", methods=["POST"])
    def operator_culture_of_beings_norms_adopt():
        from src.culture_of_beings_runtime import culture_of_beings_runtime
        from src.jarvis_culture_of_beings_authority import authorize_culture_of_beings_slot_admission

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("shared_norm_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in culture_of_beings_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_culture_of_beings_slot_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = culture_of_beings_runtime.adopt_shared_norm(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/ecosystems", methods=["GET"])
    def operator_ecosystems_snapshot():
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

        return jsonify(constitutional_ecosystem_runtime.ecosystem_snapshot()), 200

    @app.route("/api/operator/ecosystems/observe", methods=["POST"])
    def operator_ecosystems_observe():
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = constitutional_ecosystem_runtime.observe_ecosystem_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/ecosystems/charters", methods=["GET"])
    def operator_ecosystems_charters_list():
        from src.constitutional_ecosystem_registry import adopted_charters
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

        return jsonify(
            {
                "adopted_charters": adopted_charters(),
                "recent_candidates": constitutional_ecosystem_runtime.list_candidates(limit=50),
                "posture": constitutional_ecosystem_runtime.ecosystem_posture(),
            }
        ), 200

    @app.route("/api/operator/ecosystems/charters/adopt", methods=["POST"])
    def operator_ecosystems_charters_adopt():
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime
        from src.jarvis_ecosystem_authority import authorize_ecosystem_slot_admission

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("charter_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in constitutional_ecosystem_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_ecosystem_slot_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = constitutional_ecosystem_runtime.adopt_ecosystem_charter(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/diplomacy", methods=["GET"])
    def operator_diplomacy_snapshot():
        from src.inter_substrate_diplomacy_runtime import inter_substrate_diplomacy_runtime

        return jsonify(inter_substrate_diplomacy_runtime.diplomacy_snapshot()), 200

    @app.route("/api/operator/diplomacy/observe", methods=["POST"])
    def operator_diplomacy_observe():
        from src.inter_substrate_diplomacy_runtime import inter_substrate_diplomacy_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = inter_substrate_diplomacy_runtime.observe_substrate_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/diplomacy/accords", methods=["GET"])
    def operator_diplomacy_accords_list():
        from src.inter_substrate_diplomacy_registry import adopted_accords
        from src.inter_substrate_diplomacy_runtime import inter_substrate_diplomacy_runtime

        return jsonify(
            {
                "adopted_accords": adopted_accords(),
                "recent_candidates": inter_substrate_diplomacy_runtime.list_candidates(limit=50),
                "posture": inter_substrate_diplomacy_runtime.diplomacy_posture(),
            }
        ), 200

    @app.route("/api/operator/diplomacy/accords/adopt", methods=["POST"])
    def operator_diplomacy_accords_adopt():
        from src.jarvis_diplomacy_authority import authorize_diplomacy_overlay_admission
        from src.inter_substrate_diplomacy_runtime import inter_substrate_diplomacy_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("accord_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in inter_substrate_diplomacy_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_diplomacy_overlay_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = inter_substrate_diplomacy_runtime.adopt_diplomatic_accord(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/norm-federations", methods=["GET"])
    def operator_norm_federations_snapshot():
        from src.norm_federation_runtime import norm_federation_runtime

        return jsonify(norm_federation_runtime.federation_snapshot()), 200

    @app.route("/api/operator/norm-federations/observe", methods=["POST"])
    def operator_norm_federations_observe():
        from src.norm_federation_runtime import norm_federation_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = norm_federation_runtime.observe_federation_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/norm-federations/treaties", methods=["GET"])
    def operator_norm_federations_treaties_list():
        from src.norm_federation_registry import adopted_treaties
        from src.norm_federation_runtime import norm_federation_runtime

        return jsonify(
            {
                "adopted_treaties": adopted_treaties(),
                "recent_candidates": norm_federation_runtime.list_candidates(limit=50),
                "posture": norm_federation_runtime.federation_posture(),
            }
        ), 200

    @app.route("/api/operator/norm-federations/treaties/adopt", methods=["POST"])
    def operator_norm_federations_treaties_adopt():
        from src.jarvis_norm_federation_authority import authorize_norm_federation_overlay_admission
        from src.norm_federation_runtime import norm_federation_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("treaty_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in norm_federation_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_norm_federation_overlay_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = norm_federation_runtime.adopt_federation_treaty(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/constitutional-evolution", methods=["GET"])
    def operator_constitutional_evolution_snapshot():
        from src.constitutional_evolution_runtime import constitutional_evolution_runtime

        return jsonify(constitutional_evolution_runtime.evolution_snapshot()), 200

    @app.route("/api/operator/constitutional-evolution/observe", methods=["POST"])
    def operator_constitutional_evolution_observe():
        from src.constitutional_evolution_runtime import constitutional_evolution_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = constitutional_evolution_runtime.observe_evolution_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/constitutional-evolution/amendments", methods=["GET"])
    def operator_constitutional_evolution_amendments_list():
        from src.constitutional_evolution_registry import adopted_amendments
        from src.constitutional_evolution_runtime import constitutional_evolution_runtime

        return jsonify(
            {
                "adopted_amendments": adopted_amendments(),
                "recent_candidates": constitutional_evolution_runtime.list_candidates(limit=50),
                "posture": constitutional_evolution_runtime.evolution_posture(),
            }
        ), 200

    @app.route("/api/operator/constitutional-evolution/amendments/adopt", methods=["POST"])
    def operator_constitutional_evolution_amendments_adopt():
        from src.jarvis_constitutional_evolution_authority import authorize_amendment_overlay_admission
        from src.constitutional_evolution_runtime import constitutional_evolution_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("amendment_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in constitutional_evolution_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_amendment_overlay_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = constitutional_evolution_runtime.adopt_charter_amendment(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/civilizations", methods=["GET"])
    def operator_civilizations_snapshot():
        from src.governed_civilization_runtime import governed_civilization_runtime

        return jsonify(governed_civilization_runtime.civilization_snapshot()), 200

    @app.route("/api/operator/civilizations/observe", methods=["POST"])
    def operator_civilizations_observe():
        from src.governed_civilization_runtime import governed_civilization_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = governed_civilization_runtime.observe_civilization_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/civilizations/charters", methods=["GET"])
    def operator_civilizations_charters_list():
        from src.governed_civilization_registry import adopted_civilizations
        from src.governed_civilization_runtime import governed_civilization_runtime

        return jsonify(
            {
                "adopted_civilizations": adopted_civilizations(),
                "recent_candidates": governed_civilization_runtime.list_candidates(limit=50),
                "posture": governed_civilization_runtime.civilization_posture(),
            }
        ), 200

    @app.route("/api/operator/civilizations/charters/adopt", methods=["POST"])
    def operator_civilizations_charters_adopt():
        from src.governed_civilization_runtime import governed_civilization_runtime
        from src.jarvis_civilization_authority import authorize_civilization_overlay_admission

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("civilization_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in governed_civilization_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_civilization_overlay_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = governed_civilization_runtime.adopt_civilization_charter(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/federated-epochs", methods=["GET"])
    def operator_federated_epochs_snapshot():
        from src.federated_civilizational_epoch_runtime import federated_civilizational_epoch_runtime

        return jsonify(federated_civilizational_epoch_runtime.epoch_snapshot()), 200

    @app.route("/api/operator/federated-epochs/observe", methods=["POST"])
    def operator_federated_epochs_observe():
        from src.federated_civilizational_epoch_runtime import federated_civilizational_epoch_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = federated_civilizational_epoch_runtime.observe_epoch_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/federated-epochs/charters", methods=["GET"])
    def operator_federated_epochs_charters_list():
        from src.federated_civilizational_epoch_registry import load_adopted_charters
        from src.federated_civilizational_epoch_runtime import (
            _default_runtime_dir,
            federated_civilizational_epoch_runtime,
        )

        runtime_dir = _default_runtime_dir()
        return jsonify(
            {
                "adopted_charters": load_adopted_charters(runtime_dir=runtime_dir),
                "recent_candidates": federated_civilizational_epoch_runtime.list_candidates(limit=50),
                "posture": federated_civilizational_epoch_runtime.epoch_posture(),
            }
        ), 200

    @app.route("/api/operator/federated-epochs/charters/adopt", methods=["POST"])
    def operator_federated_epochs_charters_adopt():
        from src.federated_civilizational_epoch_runtime import federated_civilizational_epoch_runtime
        from src.jarvis_federated_epoch_authority import authorize_federated_epoch_overlay_admission

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("epoch_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in federated_civilizational_epoch_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        auth = authorize_federated_epoch_overlay_admission(
            candidate, session_id=session_id, repo_root=repo_root
        )
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        witnesses = list(body.get("external_witnesses") or candidate.get("external_witnesses") or [])
        result = federated_civilizational_epoch_runtime.adopt_federated_epoch_charter(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            external_witnesses=witnesses,
            operator_org_domain=str(body.get("operator_org_domain") or "") or None,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/federated-epochs/epochs", methods=["GET"])
    def operator_federated_epochs_epochs_list():
        from src.federated_civilizational_epoch_runtime import federated_civilizational_epoch_runtime

        return jsonify({"epochs": federated_civilizational_epoch_runtime.list_epochs()}), 200

    @app.route("/api/operator/federated-epochs/witnesses", methods=["GET"])
    def operator_federated_epochs_witnesses_list():
        from src.federated_civilizational_epoch_runtime import federated_civilizational_epoch_runtime

        return jsonify({"witnesses": federated_civilizational_epoch_runtime.list_witnesses()}), 200

    @app.route("/api/operator/governance-membrane", methods=["GET"])
    def operator_governance_membrane_snapshot():
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        return jsonify(multi_organism_governance_membrane_runtime.membrane_snapshot()), 200

    @app.route("/api/operator/governance-membrane/observe", methods=["POST"])
    def operator_governance_membrane_observe():
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = multi_organism_governance_membrane_runtime.observe_membrane_drift(
            session_id=str(body.get("session_id") or "") or None,
            window_days=int(body.get("window_days") or 30),
        )
        return jsonify({"observation": result, **result}), 200

    @app.route("/api/operator/governance-membrane/policies", methods=["GET"])
    def operator_governance_membrane_policies_list():
        from src.multi_organism_governance_membrane_registry import adopted_policies
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        return jsonify(
            {
                "adopted_policies": adopted_policies(),
                "recent_candidates": multi_organism_governance_membrane_runtime.list_candidates(limit=50),
                "posture": multi_organism_governance_membrane_runtime.membrane_posture(),
            }
        ), 200

    @app.route("/api/operator/governance-membrane/policies/adopt", methods=["POST"])
    def operator_governance_membrane_policies_adopt():
        from src.jarvis_membrane_authority import authorize_membrane_slot_admission
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        body: dict[str, Any] = request.get_json(silent=True) or {}
        candidate = dict(body.get("candidate") or body.get("policy_candidate") or {})
        if not candidate and body.get("candidate_id"):
            for row in multi_organism_governance_membrane_runtime.list_candidates(limit=200):
                if str(row.get("candidate_id")) == str(body.get("candidate_id")):
                    candidate = row
                    break
        session_id = str(body.get("session_id") or "global")
        if not bool(body.get("operator_approved")):
            return jsonify({"error": "operator_approved required"}), 403
        auth = authorize_membrane_slot_admission(candidate, session_id=session_id)
        if not auth.get("authorized"):
            return jsonify({"error": auth.get("reason"), "authorized": False, **auth}), 403
        result = multi_organism_governance_membrane_runtime.adopt_membrane_policy(
            candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id=session_id,
        )
        status = 200 if result.get("outcome") == "adopted" else 400
        return jsonify({"adoption": result, **result}), status

    @app.route("/api/operator/workflows/<workflow_id>/runs/<run_id>", methods=["GET"])
    def operator_workflow_run_detail(workflow_id: str, run_id: str):
        from src.workflow_chain_executor import workflow_chain_executor

        run = workflow_chain_executor.get_run(workflow_id, run_id)
        if not run:
            return jsonify({"error": "run not found", "workflow_id": workflow_id, "run_id": run_id}), 404
        return jsonify({"run": run, **run}), 200

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
        try:
            append_brain_decision_event(
                session_id,
                decision=decision,
                session=session,
            )
        except Exception as exc:
            logger.warning("brain decision ledger emit failed: %s", exc)
        return jsonify({"session": session}), 200

    @app.route("/api/operator/ceiling", methods=["GET"])
    def operator_ceiling_status():
        from src.otem_ceiling import otem_ceiling

        status = otem_ceiling.status_for_console()
        return jsonify({"ceiling": status, **status}), 200

    @app.route("/api/operator/ceiling/invoke", methods=["POST"])
    def operator_ceiling_invoke():
        from dataclasses import asdict

        from src.otem_ceiling import otem_ceiling

        body: dict[str, Any] = request.get_json(silent=True) or {}
        os.environ["AAIS_OTEM_CEILING_INVOKE"] = "1"
        event = otem_ceiling.evaluate_trigger(
            trigger_type="operator_invoke",
            severity=str(body.get("severity") or "high"),
            summary=str(body.get("summary") or "operator ceiling invoke"),
            details=dict(body.get("details") or {}),
            scope_id=str(body.get("scope_id") or "").strip() or None,
        )
        payload = {"status": "invoked", "event": asdict(event) if event else None}
        payload.update(otem_ceiling.status_for_console())
        return jsonify(payload), 200

    @app.route("/api/operator/ceiling/preview", methods=["POST"])
    def operator_ceiling_preview():
        from src.otem_ceiling import OtemCeilingError, otem_ceiling

        body: dict[str, Any] = request.get_json(silent=True) or {}
        decision = str(body.get("decision") or "").strip().lower()
        if not decision:
            return jsonify({"error": "decision required"}), 400
        try:
            result = otem_ceiling.preview_decision(
                decision,
                scope_id=str(body.get("scope_id") or "").strip() or None,
                ir_snapshot=dict(body.get("ir_snapshot") or {}),
            )
        except OtemCeilingError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(result), 200

    @app.route("/api/operator/ceiling/apply", methods=["POST"])
    def operator_ceiling_apply():
        from src.otem_ceiling import OtemCeilingError, otem_ceiling

        body: dict[str, Any] = request.get_json(silent=True) or {}
        decision = str(body.get("decision") or "").strip().lower()
        if not decision:
            return jsonify({"error": "decision required"}), 400
        try:
            result = otem_ceiling.apply_decision(
                decision,
                scope_id=str(body.get("scope_id") or "").strip() or None,
                operator_id=str(body.get("operator_id") or "").strip() or None,
                ir_before=dict(body.get("ir_before") or {}),
            )
        except OtemCeilingError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(result), 200

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

    @app.route("/api/operator/dashboard/somatic-health", methods=["GET"])
    def operator_dashboard_somatic_health():
        from src.operator_somatic_health import build_somatic_health_snapshot

        return jsonify(build_somatic_health_snapshot()), 200

    @app.route("/api/jarvis/nova/touch", methods=["POST"])
    def jarvis_nova_touch_admit():
        from src.nova_touch_admission import admit_touch_event

        body: dict[str, Any] = request.get_json(silent=True) or {}
        result = admit_touch_event(body)
        status = 200 if result.get("admitted") else 400
        return jsonify(result), status

    @app.route("/api/jarvis/nova/touch/status", methods=["GET"])
    def jarvis_nova_touch_status():
        from src.nova_touch_admission import build_nova_touch_admission_status

        return jsonify(build_nova_touch_admission_status()), 200

    @app.route("/api/operator/otem/autonomic/<routine_id>", methods=["POST"])
    def operator_otem_autonomic_routine(routine_id: str):
        from src.otem_autonomic_routines import execute_autonomic_routine

        body: dict[str, Any] = request.get_json(silent=True) or {}
        session_id = str(body.get("session_id") or _session_scope())
        result = execute_autonomic_routine(
            routine_id,
            session_id=session_id,
            args=dict(body.get("args") or {}),
        )
        status = 200 if result.get("outcome") == "completed" else 400
        return jsonify(result), status
