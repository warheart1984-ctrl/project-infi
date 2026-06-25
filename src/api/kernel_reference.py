"""CRK-T5 reference integrity API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify

from src.kernel.reference_service import get_reference_evaluator

bp = Blueprint("kernel_reference", __name__)


@bp.route("/api/kernel/reference", methods=["GET"])
def get_reference_metrics():
    evaluator = get_reference_evaluator()
    return jsonify(evaluator.compute_metrics())


def register_kernel_reference_routes(app) -> None:
    app.register_blueprint(bp)
