"""Flask entrypoint for the isolated EvolveEngine service."""

from __future__ import annotations

from flask import Flask, jsonify, request

from evolve_engine.service import EvolveEngineService


app = Flask(__name__)
evolve_engine_service = EvolveEngineService()


@app.get("/health")
def health():
    """Basic runtime health for the separate EvolveEngine service."""

    return jsonify(evolve_engine_service.health().model_dump())


@app.post("/evolve")
def evolve():
    """Run one bounded evolution job."""

    payload = request.get_json(silent=True) or {}
    result, status_code = evolve_engine_service.evolve(payload)
    response = jsonify(result.model_dump(exclude_none=True))
    response.status_code = status_code
    return response


@app.get("/traces/jobs/<job_id>")
def job_trace(job_id: str):
    """Return one persisted evolve job trace."""

    payload = evolve_engine_service.get_job_trace(job_id)
    if payload is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(payload)


@app.get("/traces/jobs/<job_id>/evaluations")
def job_evaluations(job_id: str):
    """Return one job's individual evaluation records."""

    limit = max(1, min(int(request.args.get("limit", 200)), 1000))
    return jsonify(evolve_engine_service.get_job_evaluations(job_id, limit=limit))


@app.get("/traces/runs/<jarvis_run_id>")
def run_trace(jarvis_run_id: str):
    """Return all evolve jobs linked to one Jarvis run trace."""

    return jsonify(evolve_engine_service.get_run_trace(jarvis_run_id))


@app.get("/traces/hall-of-fame")
def hall_of_fame():
    """Return the latest successful mutations."""

    limit = max(1, min(int(request.args.get("limit", 20)), 200))
    return jsonify(evolve_engine_service.list_hall_of_fame(limit=limit))


@app.get("/traces/hall-of-shame")
def hall_of_shame():
    """Return the latest failed mutations."""

    limit = max(1, min(int(request.args.get("limit", 20)), 200))
    return jsonify(evolve_engine_service.list_hall_of_shame(limit=limit))


@app.post("/maintenance/prune")
def prune():
    """Prune retained evolve traces and mutation halls."""

    payload = request.get_json(silent=True) or {}
    result = evolve_engine_service.prune_retention(
        max_jobs=int(payload.get("max_jobs")) if payload.get("max_jobs") is not None else None,
        max_hall_entries=int(payload.get("max_hall_entries")) if payload.get("max_hall_entries") is not None else None,
        max_evaluations=int(payload.get("max_evaluations")) if payload.get("max_evaluations") is not None else None,
    )
    return jsonify(result)
