"""Constitutional cockpit API — laws, evidence, epoch engine, CIT comprehension."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


def _ensure_ledgers() -> tuple[Any, Any, Any, Any]:
    from src.continuity.comprehension_ledger import ComprehensionLedgerStore, bootstrap_comprehension_ledger
    from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
    from src.continuity.mit_ledger import MitLedgerStore, bootstrap_mit_ledger

    law_store = LawLedgerStore()
    evidence_store = EvidenceLedgerStore()
    comprehension_store = ComprehensionLedgerStore()
    meaning_store = MitLedgerStore()
    bootstrap_law_ledger(law_store)
    bootstrap_evidence_ledger(evidence_store)
    bootstrap_comprehension_ledger(comprehension_store)
    bootstrap_mit_ledger(meaning_store)
    return law_store, evidence_store, comprehension_store, meaning_store


def _enrich_laws_with_spine(
    law_dicts: list[dict[str, Any]],
    *,
    law_store: Any,
    evidence_store: Any,
    comprehension_store: Any,
    meaning_store: Any,
) -> list[dict[str, Any]]:
    from src.continuity.evidence_fitness import build_spine_health

    spine = build_spine_health(
        law_store=law_store,
        evidence_store=evidence_store,
        comprehension_store=comprehension_store,
        mit_store=meaning_store,
    )
    chi_by_law = {
        item["object_id"]: item["chi"]
        for item in spine["comprehension_health"]["objects"]
        if item.get("object_type") == "law"
    }
    mu_by_law = {
        item["object_id"]: item["mu"] for item in spine["meaning_health"]["objects"]
    }
    omega_by_law = {
        item["law_id"]: item["omega"] for item in spine["evidence_fitness_health"]["objects"]
    }

    enriched: list[dict[str, Any]] = []
    for row in law_dicts:
        law_id = row.get("law_id")
        payload = dict(row)
        payload["chi"] = chi_by_law.get(law_id)
        payload["mu"] = mu_by_law.get(law_id)
        payload["omega"] = omega_by_law.get(law_id)
        enriched.append(payload)
    return enriched


def build_cockpit_summary() -> dict[str, Any]:
    """Aggregate cockpit metrics for the operator UI."""

    from src.continuity.evidence_fitness import build_spine_health

    law_store, evidence_store, comprehension_store, meaning_store = _ensure_ledgers()
    laws = law_store.all_laws()
    current_epoch = law_store.get_current_epoch()
    fitness_values = [item.current_fitness for item in laws if item.current_fitness > 0]
    avg_fitness = round(sum(fitness_values) / len(fitness_values), 6) if fitness_values else 0.0

    pending = [
        item.law_id
        for item in laws
        if item.status.value in {"proposed", "experimental"}
        and item.current_fitness < item.admit_threshold
    ]

    law_tail = law_store.ledger_entries()[-8:]
    evidence_tail = evidence_store.ledger_entries()[-8:]
    spine = build_spine_health(
        law_store=law_store,
        evidence_store=evidence_store,
        comprehension_store=comprehension_store,
        mit_store=meaning_store,
    )
    comprehension = spine["comprehension_health"]
    meaning = spine["meaning_health"]
    evidence_fitness = spine["evidence_fitness_health"]

    return {
        "epoch": current_epoch,
        "law_count": len(laws),
        "avg_fitness": avg_fitness,
        "pending_evaluations": pending,
        "chain_status": "verified",
        "law_ledger_tail": [entry.to_dict() for entry in law_tail],
        "evidence_ledger_tail": [entry.to_dict() for entry in evidence_tail],
        "spine_commit_blocked": spine["epoch_commit_blocked"],
        "spine_block_reasons": spine["block_reasons"],
        "comprehension_health": {
            "avg_chi": comprehension["avg_chi"],
            "theta_min": comprehension["theta_min"],
            "delta_max": comprehension["delta_max"],
            "below_threshold": comprehension["below_threshold"],
            "warnings": comprehension["warnings"],
            "drift_detected": comprehension["drift_detected"],
            "epoch_commit_blocked": comprehension["epoch_commit_blocked"],
        },
        "meaning_health": {
            "avg_mu": meaning["avg_mu"],
            "theta_mit": meaning["theta_mit"],
            "below_threshold": meaning["below_threshold"],
            "warnings": meaning["warnings"],
        },
        "evidence_fitness_health": {
            "avg_omega": evidence_fitness["avg_omega"],
            "theta_evidence": evidence_fitness["theta_evidence"],
            "below_threshold": evidence_fitness["below_threshold"],
            "warnings": evidence_fitness["warnings"],
            "convergence_detected": evidence_fitness["convergence_detected"],
            "epoch_commit_blocked": evidence_fitness["epoch_commit_blocked"],
        },
        "sovereign_laws": [
            {
                "law_id": item.law_id,
                "status": item.status.value,
                "fitness": round(item.current_fitness, 6),
                "chi": next(
                    (
                        obj["chi"]
                        for obj in comprehension["objects"]
                        if obj["object_id"] == item.law_id
                    ),
                    None,
                ),
                "mu": next(
                    (
                        obj["mu"]
                        for obj in meaning["objects"]
                        if obj["object_id"] == item.law_id
                    ),
                    None,
                ),
                "omega": next(
                    (
                        obj["omega"]
                        for obj in evidence_fitness["objects"]
                        if obj["law_id"] == item.law_id
                    ),
                    None,
                ),
            }
            for item in laws
        ],
    }


def _build_cit_result(object_type: str, object_id: str) -> tuple[dict[str, Any] | None, int]:
    from src.continuity.comprehension_ledger import (
        evaluate_evidence_comprehension,
        evaluate_law_comprehension,
    )

    law_store, evidence_store, comprehension_store, _ = _ensure_ledgers()
    epoch = law_store.get_current_epoch()

    if object_type == "law":
        record = law_store.get_law_record(object_id)
        if record is None:
            return None, 404
        evidence_id = f"EV-{object_id}-E{epoch}"
        evidence = evidence_store.get_evidence(evidence_id)
        return (
            evaluate_law_comprehension(
                record.to_dict(),
                epoch=epoch,
                evidence_id=evidence.evidence_id if evidence else None,
                store=comprehension_store,
            ),
            200,
        )

    if object_type == "evidence":
        evidence = evidence_store.get_evidence(object_id)
        if evidence is None:
            return None, 404
        graph = evidence_store.get_lineage_graph(object_id)
        payload = evidence.to_dict()
        payload["law_id"] = evidence.law_id
        return (
            evaluate_evidence_comprehension(
                payload,
                graph=graph,
                store=comprehension_store,
            ),
            200,
        )

    return None, 400


def _build_mit_result(object_type: str, object_id: str) -> tuple[dict[str, Any] | None, int]:
    from src.continuity.mit_ledger import evaluate_law_meaning

    law_store, _, _, meaning_store = _ensure_ledgers()
    epoch = law_store.get_current_epoch()

    if object_type != "law":
        return None, 400

    record = law_store.get_law_record(object_id)
    if record is None:
        return None, 404

    law_dict = record.to_dict()
    law_dict["_epoch"] = epoch
    result = evaluate_law_meaning(law_dict, epoch=epoch, store=meaning_store)
    return (
        {
            "law_id": object_id,
            "mu": result["mu"],
            "components": result["meaning_strip"]["components"],
            "meaning_strip": result["meaning_strip"],
            "status": result["status"],
        },
        200,
    )


def _build_eit_result(law_id: str, *, epoch: int | None = None) -> tuple[dict[str, Any] | None, int]:
    from src.continuity.cross_ledger_trace import build_cross_ledger_trace
    from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness
    from src.continuity.evidence_ledger import evidence_id_for

    law_store, evidence_store, _, _ = _ensure_ledgers()
    record = law_store.get_law_record(law_id)
    if record is None:
        return None, 404

    resolved_epoch = epoch if epoch is not None else law_store.get_current_epoch()
    evidence_id = evidence_id_for(law_id, resolved_epoch)
    ev = evidence_store.get_evidence(evidence_id)
    if ev is None:
        return (
            {
                "law_id": law_id,
                "evidence_id": evidence_id,
                "epoch": resolved_epoch,
                "found": False,
                "omega": None,
            },
            200,
        )

    graph = evidence_store.get_lineage_graph(evidence_id)
    prior_id = evidence_id_for(law_id, resolved_epoch - 1) if resolved_epoch > 0 else None
    prior = evidence_store.get_evidence(prior_id) if prior_id else None
    fitness = evaluate_evidence_fitness(ev, graph=graph, prior=prior)
    strip = build_evidence_eit_strip(ev, graph=graph, prior=prior)
    trace = build_cross_ledger_trace(
        law_id,
        law_store=law_store,
        evidence_store=evidence_store,
        epoch=resolved_epoch,
    )

    return (
        {
            "law_id": law_id,
            "evidence_id": evidence_id,
            "epoch": resolved_epoch,
            "found": True,
            "omega": fitness["omega"],
            "components": fitness["components"],
            "convergence": fitness["convergence"],
            "status": fitness["status"],
            "eit_strip": strip.to_dict(),
            "trace_summary": {
                "node_count": len(trace.get("nodes") or []),
                "edge_count": len(trace.get("edges") or []),
            },
        },
        200,
    )


def _build_law_explain(law_id: str) -> tuple[dict[str, Any] | None, int]:
    from src.continuity.mit_ledger import build_explain_payload

    law_store, _, _, _ = _ensure_ledgers()
    record = law_store.get_law_record(law_id)
    if record is None:
        return None, 404

    law_dict = record.to_dict()
    law_dict["_epoch"] = law_store.get_current_epoch()
    return build_explain_payload(law_dict), 200


def register_constitutional_cockpit_routes(app: Flask) -> None:
    """Register /api/laws, /api/evidence, /api/cockpit, /api/epoch routes."""

    @app.route("/api/laws", methods=["GET"])
    def list_laws():
        try:
            law_store, evidence_store, comprehension_store, meaning_store = _ensure_ledgers()
            laws = [item.to_dict() for item in law_store.list_law_records()]
            laws = _enrich_laws_with_spine(
                laws,
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                meaning_store=meaning_store,
            )
            return jsonify({"laws": laws, "count": len(laws)}), 200
        except Exception as exc:
            logger.error("Error listing laws: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/laws/<law_id>", methods=["GET"])
    def get_law(law_id: str):
        try:
            from src.continuity.comprehension_ledger import evaluate_law_comprehension

            law_store, evidence_store, comprehension_store, meaning_store = _ensure_ledgers()
            record = law_store.get_law_record(law_id)
            if record is None:
                return jsonify({"error": f"Law not found: {law_id}"}), 404

            epoch = law_store.get_current_epoch()
            evidence_id = f"EV-{law_id}-E{epoch}"
            evidence = evidence_store.get_evidence(evidence_id)
            law_entries = [
                entry.to_dict()
                for entry in law_store.ledger_entries()
                if entry.law_id == law_id
            ][-12:]

            law_dict = record.to_dict()
            law_dict["_epoch"] = epoch
            cit = evaluate_law_comprehension(
                law_dict,
                epoch=epoch,
                evidence_id=evidence.evidence_id if evidence else None,
                store=comprehension_store,
            )

            from src.continuity.mit_ledger import build_explain_payload, evaluate_law_meaning
            from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness
            from src.continuity.evidence_ledger import evidence_id_for

            mit = evaluate_law_meaning(law_dict, epoch=epoch, store=meaning_store)
            explain = build_explain_payload(law_dict)

            eit_strip = None
            evidence_fitness = None
            if evidence:
                graph = evidence_store.get_lineage_graph(evidence.evidence_id)
                prior_id = evidence_id_for(law_id, epoch - 1) if epoch > 0 else None
                prior = evidence_store.get_evidence(prior_id) if prior_id else None
                evidence_fitness = evaluate_evidence_fitness(
                    evidence, graph=graph, prior=prior
                )
                eit_strip = build_evidence_eit_strip(
                    evidence, graph=graph, prior=prior
                ).to_dict()

            payload = dict(law_dict)
            payload.pop("_epoch", None)
            payload["ledger_tail"] = law_entries
            payload["latest_evidence_id"] = evidence.evidence_id if evidence else None
            payload["cit_strip"] = cit["cit_strip"]
            payload["comprehension"] = cit["drift"]
            payload["meaning_strip"] = mit["meaning_strip"]
            payload["meaning"] = {"mu": mit["mu"], "status": mit["status"]}
            payload["explain"] = explain
            payload["eit_strip"] = eit_strip
            payload["evidence_fitness"] = evidence_fitness
            return jsonify(payload), 200
        except Exception as exc:
            logger.error("Error loading law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/laws/<law_id>/evaluate", methods=["POST"])
    def evaluate_law_endpoint(law_id: str):
        try:
            from src.continuity.comprehension_ledger import evaluate_law_comprehension
            from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness
            from src.continuity.evidence_ledger import evaluate_law_with_evidence, evidence_id_for
            from src.continuity.mit_ledger import evaluate_law_meaning

            law_store, evidence_store, comprehension_store, meaning_store = _ensure_ledgers()
            record = law_store.get_law_record(law_id)
            if record is None:
                return jsonify({"error": f"Law not found: {law_id}"}), 404

            body = request.get_json(silent=True) or {}
            signer = str(body.get("signer") or "operator").strip() or "operator"
            epoch = int(body.get("epoch") or (law_store.get_current_epoch() + 1))
            thresholds = body.get("thresholds") or {
                "admit": record.admit_threshold,
                "reject": record.reject_threshold,
            }
            lineages = law_store.get_lineages_for_law(law_id)

            updated = evaluate_law_with_evidence(
                record,
                epoch,
                lineages,
                thresholds=thresholds,
                signer=signer,
                law_store=law_store,
                evidence_store=evidence_store,
            )
            law_store.update_law_record(updated)
            evidence_id = evidence_id_for(law_id, epoch)
            stored_evidence = evidence_store.get_evidence(evidence_id)
            law_dict = updated.to_dict()
            law_dict["_epoch"] = epoch

            cit = evaluate_law_comprehension(
                law_dict,
                epoch=epoch,
                evidence_id=evidence_id,
                store=comprehension_store,
            )
            mit = evaluate_law_meaning(law_dict, epoch=epoch, store=meaning_store)
            eit = None
            eit_strip = None
            if stored_evidence:
                graph = evidence_store.get_lineage_graph(evidence_id)
                eit = evaluate_evidence_fitness(stored_evidence, graph=graph)
                eit_strip = build_evidence_eit_strip(stored_evidence, graph=graph).to_dict()

            return jsonify(
                {
                    "status": "ok",
                    "law": updated.to_dict(),
                    "evidence_id": evidence_id,
                    "epoch": epoch,
                    "cit": {"chi": cit["cit_strip"]["chi"], "drift": cit["drift"]},
                    "mit": {"mu": mit["mu"], "status": mit["status"]},
                    "eit": eit,
                    "eit_strip": eit_strip,
                }
            ), 200
        except Exception as exc:
            logger.error("Error evaluating law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/evidence/<evidence_id>", methods=["GET"])
    def get_evidence_lineage(evidence_id: str):
        try:
            from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness

            _, evidence_store, _, _ = _ensure_ledgers()
            graph = evidence_store.get_lineage_graph(evidence_id)
            if not graph.get("found"):
                return jsonify({"error": f"Evidence not found: {evidence_id}"}), 404
            record = evidence_store.get_evidence(evidence_id)
            if record is not None:
                fitness = evaluate_evidence_fitness(record, graph=graph)
                strip = build_evidence_eit_strip(record, graph=graph)
                graph["eit_strip"] = strip.to_dict()
                graph["evidence_fitness"] = fitness
            return jsonify(graph), 200
        except Exception as exc:
            logger.error("Error loading evidence %s: %s", evidence_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/cockpit/summary", methods=["GET"])
    def cockpit_summary():
        try:
            return jsonify(build_cockpit_summary()), 200
        except Exception as exc:
            logger.error("Error building cockpit summary: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/epoch/run", methods=["POST"])
    def run_epoch():
        try:
            from src.continuity.evidence_fitness import build_spine_health
            from src.continuity.epoch_engine import run_epoch_cycle

            body = request.get_json(silent=True) or {}
            signer = str(body.get("signer") or "operator").strip() or "operator"
            law_store, evidence_store, comprehension_store, meaning_store = _ensure_ledgers()
            pre_spine = build_spine_health(
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                mit_store=meaning_store,
            )
            if pre_spine.get("epoch_commit_blocked"):
                reasons = ", ".join(pre_spine.get("block_reasons") or ["SPINE-BLOCK"])
                return jsonify(
                    {
                        "status": "blocked",
                        "reason": f"{reasons}: sovereign spine below threshold",
                        "spine_health": pre_spine,
                    }
                ), 409

            result = run_epoch_cycle(signer=signer)
            post_spine = build_spine_health(
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                mit_store=meaning_store,
            )
            result["spine_health"] = {
                "avg_chi": post_spine["comprehension_health"]["avg_chi"],
                "avg_mu": post_spine["meaning_health"]["avg_mu"],
                "avg_omega": post_spine["evidence_fitness_health"]["avg_omega"],
                "warnings": (
                    post_spine["comprehension_health"]["warnings"]
                    + post_spine["meaning_health"]["warnings"]
                    + post_spine["evidence_fitness_health"]["warnings"]
                ),
                "spine_commit_blocked": post_spine["epoch_commit_blocked"],
            }
            return jsonify(result), 200
        except Exception as exc:
            logger.error("Error running epoch cycle: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/cockpit/comprehension", methods=["GET"])
    def cockpit_comprehension():
        try:
            from src.continuity.comprehension_ledger import build_comprehension_health

            law_store, evidence_store, comprehension_store, _ = _ensure_ledgers()
            return jsonify(
                build_comprehension_health(
                    law_store=law_store,
                    evidence_store=evidence_store,
                    comprehension_store=comprehension_store,
                )
            ), 200
        except Exception as exc:
            logger.error("Error building comprehension health: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/cockpit/cit/<object_type>/<object_id>", methods=["GET"])
    def cockpit_cit_strip(object_type: str, object_id: str):
        try:
            result, status = _build_cit_result(object_type, object_id)
            if result is None:
                if status == 404:
                    return jsonify({"error": f"{object_type} not found: {object_id}"}), 404
                return jsonify({"error": f"Unsupported object_type: {object_type}"}), 400
            return jsonify(result), 200
        except Exception as exc:
            logger.error("Error building CIT strip for %s/%s: %s", object_type, object_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/cockpit/explain/<object_type>/<object_id>", methods=["GET"])
    def cockpit_explain(object_type: str, object_id: str):
        """Steward mode — bounded explanation for an object."""
        try:
            result, status = _build_cit_result(object_type, object_id)
            if result is None:
                if status == 404:
                    return jsonify({"error": f"{object_type} not found: {object_id}"}), 404
                return jsonify({"error": f"Unsupported object_type: {object_type}"}), 400
            strip = result.get("cit_strip") or {}
            return jsonify(
                {
                    "object_type": object_type,
                    "object_id": object_id,
                    "steward_summary": strip.get("summarize"),
                    "explain": strip.get("explain"),
                    "what_breaks_if_removed": strip.get("what_breaks_if_removed"),
                    "chi": strip.get("chi"),
                    "trace_links": strip.get("trace_links") or [],
                }
            ), 200
        except Exception as exc:
            logger.error("Error explaining %s/%s: %s", object_type, object_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/cit/law/<law_id>", methods=["GET"])
    def cit_law(law_id: str):
        try:
            result, status = _build_cit_result("law", law_id)
            if result is None:
                if status == 404:
                    return jsonify({"error": f"Law not found: {law_id}"}), 404
                return jsonify({"error": "Unsupported request"}), 400
            strip = result.get("cit_strip") or {}
            return jsonify(
                {
                    "law_id": law_id,
                    "chi": strip.get("chi"),
                    "components": strip.get("components"),
                    "cit_strip": strip,
                    "drift": result.get("drift"),
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading CIT for law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/mit/law/<law_id>", methods=["GET"])
    def mit_law(law_id: str):
        try:
            result, status = _build_mit_result("law", law_id)
            if result is None:
                if status == 404:
                    return jsonify({"error": f"Law not found: {law_id}"}), 404
                return jsonify({"error": "Unsupported request"}), 400
            return jsonify(result), 200
        except Exception as exc:
            logger.error("Error loading MIT for law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/explain/law/<law_id>", methods=["GET"])
    def explain_law(law_id: str):
        try:
            payload, status = _build_law_explain(law_id)
            if payload is None:
                if status == 404:
                    return jsonify({"error": f"Law not found: {law_id}"}), 404
                return jsonify({"error": "Unsupported request"}), 400
            return jsonify(payload), 200
        except Exception as exc:
            logger.error("Error explaining law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/eit/law/<law_id>", methods=["GET"])
    def eit_law(law_id: str):
        try:
            result, status = _build_eit_result(law_id)
            if result is None:
                if status == 404:
                    return jsonify({"error": f"Law not found: {law_id}"}), 404
                return jsonify({"error": "Unsupported request"}), 400
            return jsonify(result), 200
        except Exception as exc:
            logger.error("Error loading EIT for law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/eit/evidence/<evidence_id>", methods=["GET"])
    def eit_evidence(evidence_id: str):
        try:
            from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness

            _, evidence_store, _, _ = _ensure_ledgers()
            ev = evidence_store.get_evidence(evidence_id)
            if ev is None:
                return jsonify({"error": f"Evidence not found: {evidence_id}"}), 404
            graph = evidence_store.get_lineage_graph(evidence_id)
            fitness = evaluate_evidence_fitness(ev, graph=graph)
            strip = build_evidence_eit_strip(ev, graph=graph)
            return jsonify(
                {
                    "evidence_id": evidence_id,
                    "omega": fitness["omega"],
                    "components": fitness["components"],
                    "convergence": fitness["convergence"],
                    "status": fitness["status"],
                    "eit_strip": strip.to_dict(),
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading EIT for evidence %s: %s", evidence_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/trace/law/<law_id>", methods=["GET"])
    def trace_law(law_id: str):
        try:
            from src.continuity.cross_ledger_trace import build_cross_ledger_trace

            law_store, evidence_store, comprehension_store, meaning_store = _ensure_ledgers()
            trace = build_cross_ledger_trace(
                law_id,
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                mit_store=meaning_store,
            )
            if not trace.get("found"):
                return jsonify({"error": f"Law not found: {law_id}"}), 404
            return jsonify(trace), 200
        except Exception as exc:
            logger.error("Error tracing law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/replay/law/<law_id>", methods=["POST"])
    def replay_law(law_id: str):
        try:
            from src.continuity.cross_ledger_trace import replay_law_evidence

            law_store, evidence_store, _, _ = _ensure_ledgers()
            body = request.get_json(silent=True) or {}
            signer = str(body.get("signer") or "operator").strip() or "operator"
            epoch = body.get("epoch")
            resolved_epoch = int(epoch) if epoch is not None else None
            result = replay_law_evidence(
                law_id,
                epoch=resolved_epoch,
                signer=signer,
                law_store=law_store,
                evidence_store=evidence_store,
            )
            if not result.get("found") and result.get("reason") == "law not found":
                return jsonify({"error": f"Law not found: {law_id}"}), 404
            return jsonify(result), 200
        except Exception as exc:
            logger.error("Error replaying law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500
