"""Constitutional cockpit API — laws, evidence, epoch engine, CIT comprehension."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


def _ensure_ledgers() -> tuple[Any, Any, Any, Any, Any, Any]:
    from src.continuity.comprehension_ledger import ComprehensionLedgerStore, bootstrap_comprehension_ledger
    from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger
    from src.continuity.git_ledger import GitLedgerStore, bootstrap_git_ledger
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
    from src.continuity.mit_ledger import MitLedgerStore, bootstrap_mit_ledger
    from src.continuity.sit_ledger import SitLedgerStore, bootstrap_sit_ledger

    law_store = LawLedgerStore()
    evidence_store = EvidenceLedgerStore()
    comprehension_store = ComprehensionLedgerStore()
    meaning_store = MitLedgerStore()
    sit_store = SitLedgerStore()
    git_store = GitLedgerStore()
    bootstrap_law_ledger(law_store)
    bootstrap_evidence_ledger(evidence_store)
    bootstrap_comprehension_ledger(comprehension_store)
    bootstrap_mit_ledger(meaning_store)
    bootstrap_sit_ledger(sit_store)
    bootstrap_git_ledger(git_store)
    return law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store


def _enrich_laws_with_spine(
    law_dicts: list[dict[str, Any]],
    *,
    law_store: Any,
    evidence_store: Any,
    comprehension_store: Any,
    meaning_store: Any,
    sit_store: Any | None = None,
    git_store: Any | None = None,
) -> list[dict[str, Any]]:
    from src.continuity.evidence_fitness import build_spine_health

    spine = build_spine_health(
        law_store=law_store,
        evidence_store=evidence_store,
        comprehension_store=comprehension_store,
        mit_store=meaning_store,
        sit_store=sit_store,
        git_store=git_store,
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
    sigma_by_law = {
        item["object_id"]: item["sigma"] for item in spine["structural_health"]["objects"]
    }
    lambda_by_law = {
        item["object_id"]: item["lambda"] for item in spine["generative_health"]["objects"]
    }
    phi_by_law = {
        item["object_id"]: item["phi"] for item in spine["proof_health"]["objects"]
    }

    enriched: list[dict[str, Any]] = []
    for row in law_dicts:
        law_id = row.get("law_id")
        payload = dict(row)
        payload["chi"] = chi_by_law.get(law_id)
        payload["mu"] = mu_by_law.get(law_id)
        payload["omega"] = omega_by_law.get(law_id)
        payload["sigma"] = sigma_by_law.get(law_id)
        payload["lambda"] = lambda_by_law.get(law_id)
        payload["phi"] = phi_by_law.get(law_id)
        enriched.append(payload)
    return enriched


def build_cockpit_summary() -> dict[str, Any]:
    """Aggregate cockpit metrics for the operator UI."""

    from src.continuity.evidence_fitness import build_spine_health

    law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
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
        sit_store=sit_store,
        git_store=git_store,
    )
    comprehension = spine["comprehension_health"]
    meaning = spine["meaning_health"]
    evidence_fitness = spine["evidence_fitness_health"]
    structural = spine["structural_health"]
    generative = spine["generative_health"]
    proof = spine["proof_health"]

    from src.kernel.boundary_service import get_boundary_loop
    from src.kernel.reference_service import get_reference_evaluator
    from src.kernel.telemetry import Telemetry

    boundary_loop = get_boundary_loop()
    boundary_loop.monitor.telemetry = Telemetry.current()
    boundary_detection = boundary_loop.snapshot()
    reference_integrity = get_reference_evaluator().compute_metrics()

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
        "structural_health": {
            "avg_sigma": structural["avg_sigma"],
            "theta_sit": structural["theta_sit"],
            "below_threshold": structural["below_threshold"],
            "warnings": structural["warnings"],
            "epoch_commit_blocked": structural["epoch_commit_blocked"],
        },
        "generative_health": {
            "avg_lambda": generative["avg_lambda"],
            "theta_git": generative["theta_git"],
            "below_threshold": generative["below_threshold"],
            "warnings": generative["warnings"],
            "epoch_commit_blocked": generative["epoch_commit_blocked"],
        },
        "proof_health": {
            "avg_phi": proof["avg_phi"],
            "avg_fitness": proof["avg_fitness"],
            "theta_pit": proof["theta_pit"],
            "below_threshold": proof["below_threshold"],
            "warnings": proof["warnings"],
            "epoch_commit_blocked": proof["epoch_commit_blocked"],
        },
        "outcome_health": {
            "outcome_drift": spine.get("outcome_drift"),
            "theta_outcome_drift": spine["outcome_health"]["theta_outcome_drift"],
            "critical_outcomes": spine["outcome_health"]["critical_outcomes"],
            "concerning_outcomes": spine["outcome_health"]["concerning_outcomes"],
            "epoch_commit_blocked": spine["outcome_health"]["epoch_commit_blocked"],
        },
        "spine_overall": spine.get("overall"),
        "boundary_detection": boundary_detection,
        "reference_integrity": reference_integrity,
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
                "sigma": next(
                    (
                        obj["sigma"]
                        for obj in structural["objects"]
                        if obj["object_id"] == item.law_id
                    ),
                    None,
                ),
                "lambda": next(
                    (
                        obj["lambda"]
                        for obj in generative["objects"]
                        if obj["object_id"] == item.law_id
                    ),
                    None,
                ),
                "phi": next(
                    (
                        obj["phi"]
                        for obj in proof["objects"]
                        if obj["object_id"] == item.law_id
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

    law_store, evidence_store, comprehension_store, _, _, _ = _ensure_ledgers()
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

    law_store, _, _, meaning_store, _, _ = _ensure_ledgers()
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

    law_store, evidence_store, _, _, _, _ = _ensure_ledgers()
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

    law_store, _, _, _, _, _ = _ensure_ledgers()
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
            law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
            laws = [item.to_dict() for item in law_store.list_law_records()]
            laws = _enrich_laws_with_spine(
                laws,
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                meaning_store=meaning_store,
                sit_store=sit_store,
                git_store=git_store,
            )
            return jsonify({"laws": laws, "count": len(laws)}), 200
        except Exception as exc:
            logger.error("Error listing laws: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/laws/<law_id>", methods=["GET"])
    def get_law(law_id: str):
        try:
            from src.continuity.comprehension_ledger import evaluate_law_comprehension

            law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
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
            from src.continuity.sit_ledger import evaluate_law_structure
            from src.continuity.git_ledger import evaluate_law_generative
            from src.continuity.pit_fitness import evaluate_law_pit
            from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness
            from src.continuity.evidence_ledger import evidence_id_for

            lineages = law_store.get_lineages_for_law(law_id)
            mit = evaluate_law_meaning(law_dict, epoch=epoch, store=meaning_store)
            explain = build_explain_payload(law_dict)

            graph = evidence_store.get_lineage_graph(evidence_id) if evidence else None
            sit = evaluate_law_structure(
                law_dict,
                epoch=epoch,
                lineages=lineages,
                graph=graph,
                evidence_present=evidence is not None,
                store=sit_store,
            )
            git = evaluate_law_generative(
                law_dict,
                epoch=epoch,
                lineages=lineages,
                store=git_store,
            )

            eit_strip = None
            evidence_fitness = None
            omega: float | None = None
            if evidence:
                prior_id = evidence_id_for(law_id, epoch - 1) if epoch > 0 else None
                prior = evidence_store.get_evidence(prior_id) if prior_id else None
                evidence_fitness = evaluate_evidence_fitness(
                    evidence, graph=graph, prior=prior
                )
                omega = evidence_fitness["omega"]
                eit_strip = build_evidence_eit_strip(
                    evidence, graph=graph, prior=prior
                ).to_dict()

            pit = evaluate_law_pit(law_dict, omega=omega)

            payload = dict(law_dict)
            payload.pop("_epoch", None)
            payload["ledger_tail"] = law_entries
            payload["latest_evidence_id"] = evidence.evidence_id if evidence else None
            payload["cit_strip"] = cit["cit_strip"]
            payload["comprehension"] = cit["drift"]
            payload["meaning_strip"] = mit["meaning_strip"]
            payload["meaning"] = {"mu": mit["mu"], "status": mit["status"]}
            payload["sit_strip"] = sit["sit_strip"]
            payload["structure"] = {"sigma": sit["sigma"], "status": sit["status"]}
            payload["git_strip"] = git["git_strip"]
            payload["generative"] = {"lambda": git["lambda"], "status": git["status"]}
            payload["pit_strip"] = pit["pit_strip"]
            payload["proof"] = {"phi": pit["phi"], "status": pit["status"]}
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
            from src.continuity.sit_ledger import evaluate_law_structure
            from src.continuity.git_ledger import evaluate_law_generative
            from src.continuity.pit_fitness import evaluate_law_pit

            law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
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
            graph = evidence_store.get_lineage_graph(evidence_id) if stored_evidence else None
            sit = evaluate_law_structure(
                law_dict,
                epoch=epoch,
                lineages=lineages,
                graph=graph,
                evidence_present=stored_evidence is not None,
                store=sit_store,
            )
            git = evaluate_law_generative(
                law_dict,
                epoch=epoch,
                lineages=lineages,
                store=git_store,
            )
            eit = None
            eit_strip = None
            omega: float | None = None
            if stored_evidence:
                graph = evidence_store.get_lineage_graph(evidence_id)
                eit = evaluate_evidence_fitness(stored_evidence, graph=graph)
                omega = eit["omega"]
                eit_strip = build_evidence_eit_strip(stored_evidence, graph=graph).to_dict()
            pit = evaluate_law_pit(law_dict, omega=omega)

            return jsonify(
                {
                    "status": "ok",
                    "law": updated.to_dict(),
                    "evidence_id": evidence_id,
                    "epoch": epoch,
                    "cit": {"chi": cit["cit_strip"]["chi"], "drift": cit["drift"]},
                    "mit": {"mu": mit["mu"], "status": mit["status"]},
                    "sit": {"sigma": sit["sigma"], "status": sit["status"]},
                    "git": {"lambda": git["lambda"], "status": git["status"]},
                    "pit": {"phi": pit["phi"], "status": pit["status"]},
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

            _, evidence_store, _, _, _, _ = _ensure_ledgers()
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

    @app.route("/api/cockpit/spine", methods=["GET"])
    def cockpit_spine():
        try:
            from src.continuity.evidence_fitness import build_spine_health

            law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
            spine = build_spine_health(
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                mit_store=meaning_store,
                sit_store=sit_store,
                git_store=git_store,
            )
            return jsonify(spine), 200
        except Exception as exc:
            logger.error("Error building cockpit spine: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/epoch/run", methods=["POST"])
    def run_epoch():
        try:
            from src.continuity.evidence_fitness import build_spine_health
            from src.continuity.epoch_engine import run_epoch_cycle

            body = request.get_json(silent=True) or {}
            signer = str(body.get("signer") or "operator").strip() or "operator"
            law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
            pre_spine = build_spine_health(
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                mit_store=meaning_store,
                sit_store=sit_store,
                git_store=git_store,
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
                sit_store=sit_store,
                git_store=git_store,
            )
            from src.continuity.identity_object import DEFAULT_IDENTITY
            from src.kernel.boundary_service import get_boundary_loop
            from src.kernel.governance import Governance
            from src.kernel.identity_history_ledger import shared_identity_ledger
            from src.kernel.reference_service import get_reference_evaluator
            from src.kernel.telemetry import Telemetry

            boundary_loop = get_boundary_loop()
            boundary_loop.monitor.telemetry = Telemetry.current()
            boundary_detection = boundary_loop.observe_spine(post_spine)
            Governance.current().set_kernel_version(boundary_loop.kernel_version)
            shared_identity_ledger().append(
                identity=DEFAULT_IDENTITY,
                epoch=int(result.get("epoch") or law_store.get_current_epoch()),
                kernel_version=boundary_loop.kernel_version,
                reason="epoch-run",
            )
            result["boundary_detection"] = boundary_detection
            result["reference_integrity"] = get_reference_evaluator().compute_metrics()
            result["spine_health"] = {
                "avg_chi": post_spine["comprehension_health"]["avg_chi"],
                "avg_mu": post_spine["meaning_health"]["avg_mu"],
                "avg_omega": post_spine["evidence_fitness_health"]["avg_omega"],
                "avg_sigma": post_spine["structural_health"]["avg_sigma"],
                "avg_lambda": post_spine["generative_health"]["avg_lambda"],
                "avg_phi": post_spine["proof_health"]["avg_phi"],
                "warnings": (
                    post_spine["comprehension_health"]["warnings"]
                    + post_spine["meaning_health"]["warnings"]
                    + post_spine["evidence_fitness_health"]["warnings"]
                    + post_spine["structural_health"]["warnings"]
                    + post_spine["generative_health"]["warnings"]
                    + post_spine["proof_health"]["warnings"]
                ),
                "spine_commit_blocked": post_spine["epoch_commit_blocked"],
                "block_reasons": post_spine["block_reasons"],
            }
            return jsonify(result), 200
        except Exception as exc:
            logger.error("Error running epoch cycle: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/cockpit/comprehension", methods=["GET"])
    def cockpit_comprehension():
        try:
            from src.continuity.comprehension_ledger import build_comprehension_health

            law_store, evidence_store, comprehension_store, _, _, _ = _ensure_ledgers()
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
    @app.route("/api/fitness/comprehension/law/<law_id>", methods=["GET"])
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
    @app.route("/api/fitness/meaning/law/<law_id>", methods=["GET"])
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

    @app.route("/api/sit/law/<law_id>", methods=["GET"])
    def sit_law(law_id: str):
        try:
            from src.continuity.sit_ledger import evaluate_law_structure

            law_store, evidence_store, _, _, sit_store, _ = _ensure_ledgers()
            record = law_store.get_law_record(law_id)
            if record is None:
                return jsonify({"error": f"Law not found: {law_id}"}), 404
            epoch = law_store.get_current_epoch()
            evidence_id = f"EV-{law_id}-E{epoch}"
            evidence = evidence_store.get_evidence(evidence_id)
            graph = evidence_store.get_lineage_graph(evidence_id) if evidence else None
            law_dict = record.to_dict()
            result = evaluate_law_structure(
                law_dict,
                epoch=epoch,
                lineages=law_store.get_lineages_for_law(law_id),
                graph=graph,
                evidence_present=evidence is not None,
                store=sit_store,
            )
            return jsonify(
                {
                    "law_id": law_id,
                    "sigma": result["sigma"],
                    "components": result["sit_strip"]["components"],
                    "sit_strip": result["sit_strip"],
                    "status": result["status"],
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading SIT for law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/git/law/<law_id>", methods=["GET"])
    def git_law(law_id: str):
        try:
            from src.continuity.git_ledger import evaluate_law_generative

            law_store, _, _, _, _, git_store = _ensure_ledgers()
            record = law_store.get_law_record(law_id)
            if record is None:
                return jsonify({"error": f"Law not found: {law_id}"}), 404
            epoch = law_store.get_current_epoch()
            result = evaluate_law_generative(
                record.to_dict(),
                epoch=epoch,
                lineages=law_store.get_lineages_for_law(law_id),
                store=git_store,
            )
            return jsonify(
                {
                    "law_id": law_id,
                    "lambda": result["lambda"],
                    "components": result["git_strip"]["components"],
                    "git_strip": result["git_strip"],
                    "status": result["status"],
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading GIT for law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/pit/law/<law_id>", methods=["GET"])
    def pit_law(law_id: str):
        try:
            from src.continuity.evidence_fitness import evaluate_evidence_fitness
            from src.continuity.evidence_ledger import evidence_id_for
            from src.continuity.pit_fitness import evaluate_law_pit

            law_store, evidence_store, _, _, _, _ = _ensure_ledgers()
            record = law_store.get_law_record(law_id)
            if record is None:
                return jsonify({"error": f"Law not found: {law_id}"}), 404
            epoch = law_store.get_current_epoch()
            evidence_id = evidence_id_for(law_id, epoch)
            ev = evidence_store.get_evidence(evidence_id)
            omega: float | None = None
            if ev is not None:
                graph = evidence_store.get_lineage_graph(evidence_id)
                omega = evaluate_evidence_fitness(ev, graph=graph)["omega"]
            result = evaluate_law_pit(record.to_dict(), omega=omega)
            return jsonify(
                {
                    "law_id": law_id,
                    "phi": result["phi"],
                    "fitness": record.current_fitness,
                    "components": result["pit_strip"]["components"],
                    "pit_strip": result["pit_strip"],
                    "status": result["status"],
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading PIT for law %s: %s", law_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/eit/law/<law_id>", methods=["GET"])
    @app.route("/api/fitness/evidence/law/<law_id>", methods=["GET"])
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
    @app.route("/api/fitness/evidence/evidence/<evidence_id>", methods=["GET"])
    def eit_evidence(evidence_id: str):
        try:
            from src.continuity.evidence_fitness import build_evidence_eit_strip, evaluate_evidence_fitness

            _, evidence_store, _, _, _, _ = _ensure_ledgers()
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

            law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
            trace = build_cross_ledger_trace(
                law_id,
                law_store=law_store,
                evidence_store=evidence_store,
                comprehension_store=comprehension_store,
                mit_store=meaning_store,
                sit_store=sit_store,
                git_store=git_store,
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

            law_store, evidence_store, _, _, _, _ = _ensure_ledgers()
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

    @app.route("/api/decisions", methods=["GET"])
    def list_decisions():
        try:
            from src.continuity.decision_ledger import DecisionLedgerStore, bootstrap_decision_ledger

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = law_store.get_current_epoch()
            store = DecisionLedgerStore()
            bootstrap_decision_ledger(store, epoch=epoch)
            decisions = [item.to_dict() for item in store.list_decisions()]
            return jsonify({"decisions": decisions, "count": len(decisions)}), 200
        except Exception as exc:
            logger.error("Error listing decisions: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/decisions/<decision_id>", methods=["GET"])
    def get_decision(decision_id: str):
        try:
            from src.continuity.decision_ledger import DecisionLedgerStore, bootstrap_decision_ledger
            from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = law_store.get_current_epoch()
            decisions = DecisionLedgerStore()
            outcomes = OutcomeLedgerStore()
            bootstrap_decision_ledger(decisions, epoch=epoch)
            bootstrap_outcome_ledger(outcomes, epoch=epoch)
            record = decisions.get(decision_id)
            if record is None:
                return jsonify({"error": f"Decision not found: {decision_id}"}), 404
            outcome = outcomes.get_by_decision(decision_id)
            payload = record.to_dict()
            if outcome is not None:
                from src.continuity.outcome_fitness import build_outcome_strip

                payload["outcome"] = outcome.to_dict()
                payload["outcome_strip"] = build_outcome_strip(outcome).to_dict()
            return jsonify(payload), 200
        except Exception as exc:
            logger.error("Error loading decision %s: %s", decision_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/outcomes", methods=["GET"])
    def list_outcomes():
        try:
            from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = law_store.get_current_epoch()
            store = OutcomeLedgerStore()
            bootstrap_outcome_ledger(store, epoch=epoch)
            outcomes = [item.to_dict() for item in store.list_outcomes()]
            return jsonify({"outcomes": outcomes, "count": len(outcomes)}), 200
        except Exception as exc:
            logger.error("Error listing outcomes: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/outcomes/<outcome_id>", methods=["GET"])
    @app.route("/api/fitness/outcome/<outcome_id>", methods=["GET"])
    def get_outcome(outcome_id: str):
        try:
            from src.continuity.outcome_fitness import build_outcome_strip
            from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = law_store.get_current_epoch()
            store = OutcomeLedgerStore()
            bootstrap_outcome_ledger(store, epoch=epoch)
            record = store.get(outcome_id)
            if record is None:
                return jsonify({"error": f"Outcome not found: {outcome_id}"}), 404
            return jsonify(
                {
                    **record.to_dict(),
                    "outcome_strip": build_outcome_strip(record).to_dict(),
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading outcome %s: %s", outcome_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/outcome/decision/<decision_id>", methods=["GET"])
    @app.route("/api/fitness/outcome/decision/<decision_id>", methods=["GET"])
    def outcome_for_decision(decision_id: str):
        try:
            from src.continuity.outcome_fitness import build_outcome_strip
            from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = law_store.get_current_epoch()
            store = OutcomeLedgerStore()
            bootstrap_outcome_ledger(store, epoch=epoch)
            record = store.get_by_decision(decision_id)
            if record is None:
                return jsonify({"error": f"No outcome for decision: {decision_id}"}), 404
            return jsonify(
                {
                    **record.to_dict(),
                    "outcome_strip": build_outcome_strip(record).to_dict(),
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading outcome for decision %s: %s", decision_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/pods", methods=["GET"])
    def list_pods():
        try:
            from src.ugr.discovery.pod_cockpit import build_pods_cockpit_payload

            return jsonify(build_pods_cockpit_payload()), 200
        except Exception as exc:
            logger.error("Error listing discovery pods: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/pods/<path:pod_id>", methods=["GET"])
    def get_pod(pod_id: str):
        try:
            from src.ugr.discovery.pod_cockpit import get_pod_cockpit_dto

            record = get_pod_cockpit_dto(pod_id)
            if record is None:
                return jsonify({"error": f"Pod not found: {pod_id}"}), 404
            return jsonify(record), 200
        except Exception as exc:
            logger.error("Error loading pod %s: %s", pod_id, exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/fitness/attention", methods=["GET"])
    def attention_allocation_fitness():
        """AIT userland projection — attention-type ResourceObject allocations."""
        try:
            from src.continuity.resource_ledger import ResourceLedgerStore, bootstrap_resource_ledger

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = law_store.get_current_epoch()
            store = ResourceLedgerStore()
            bootstrap_resource_ledger(store, epoch=epoch)
            resources = [
                item.to_dict()
                for item in store.list_resources()
                if item.type in {"attention", "time"}
            ]
            return jsonify(
                {
                    "canonical": "AIT — Attention allocation fitness (ResourceObject projection)",
                    "epoch": epoch,
                    "resources": resources,
                    "count": len(resources),
                }
            ), 200
        except Exception as exc:
            logger.error("Error loading attention allocation fitness: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/survivability/dashboard", methods=["GET"])
    def survivability_dashboard():
        """Article S / S-2 survivability cockpit — metrics, zones, succession, amendment."""
        try:
            from src.survivability_dashboard_api import build_survivability_dashboard_payload

            refresh = request.args.get("refresh", "").lower() in {"1", "true", "yes"}
            payload = build_survivability_dashboard_payload(refresh=refresh)
            return jsonify(payload), 200
        except Exception as exc:
            logger.error("Error building survivability dashboard: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/survivability/amendment-template", methods=["GET"])
    def survivability_amendment_template():
        """Render open survivability remediation amendment as markdown."""
        try:
            from constitutional.runtime.survivability_amendment import (
                load_survivability_amendment,
                render_survivability_amendment_template,
            )
            from src.survivability_dashboard_api import get_survivability_csr

            record = load_survivability_amendment(get_survivability_csr())
            if record is None or record.status != "open":
                return jsonify(
                    {
                        "status": "none",
                        "template_id": None,
                        "markdown": None,
                        "message": "No open survivability remediation amendment.",
                    }
                ), 200
            return jsonify(
                {
                    "status": "open",
                    "template_id": record.template_id,
                    "markdown": render_survivability_amendment_template(record),
                    "record": record.model_dump(mode="json"),
                }
            ), 200
        except Exception as exc:
            logger.error("Error rendering survivability amendment template: %s", exc)
            return jsonify({"error": str(exc)}), 500
