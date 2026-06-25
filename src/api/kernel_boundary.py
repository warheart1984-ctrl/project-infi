"""Kernel boundary (CRK-T2) API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.kernel.boundary_service import get_boundary_loop
from src.kernel.governance import Governance
from src.kernel.telemetry import Telemetry

bp = Blueprint("kernel_boundary", __name__)


@bp.route("/api/kernel/boundary", methods=["GET"])
def get_kernel_boundary_signals():
    loop = get_boundary_loop()
    loop.monitor.telemetry = Telemetry.current()
    return jsonify(loop.snapshot())


@bp.route("/api/kernel/boundary/step", methods=["POST"])
def step_kernel_boundary():
    """Advance outer loop one epoch tick (called from epoch simulation)."""
    loop = get_boundary_loop()
    loop.monitor.telemetry = Telemetry.current()
    body = request.get_json(silent=True) or {}
    result = loop.step(ratify=bool(body.get("ratify")))
    governance = Governance.current()
    governance.set_kernel_version(loop.kernel_version)
    return jsonify(result)


@bp.route("/api/kernel/amendments", methods=["GET"])
def list_kernel_amendments():
    ledger = Governance.current().amendment_ledger()
    return jsonify(
        {
            "amendments": [
                {
                    "id": rec.id,
                    "timestamp": rec.timestamp,
                    "kernel_version": rec.kernel_version,
                    "insufficiency": rec.insufficiency,
                    "signals": rec.signals,
                    "reason": rec.reason,
                    "ratified": rec.ratified,
                }
                for rec in ledger.list()
            ],
            "count": len(ledger.list()),
        }
    )


def register_kernel_boundary_routes(app) -> None:
    app.register_blueprint(bp)
