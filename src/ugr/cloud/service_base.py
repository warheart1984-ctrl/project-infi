"""Shared Flask helpers for UGR cloud services."""

from __future__ import annotations

import json
import os
from typing import Any, Callable

from flask import Flask, jsonify, request


def create_ugr_service_app(
    *,
    service_id: str,
    service_version: str = "0.1",
    register_routes: Callable[[Flask], None] | None = None,
) -> Flask:
    app = Flask(service_id)
    app.config["UGR_SERVICE_ID"] = service_id
    app.config["UGR_SERVICE_VERSION"] = service_version

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "service_id": service_id,
                "service_version": service_version,
                "status": "ok",
                "deployment_mode": os.getenv("UGR_DEPLOYMENT_MODE", "monolith"),
            }
        )

    @app.before_request
    def _mesh_identity_check():
        if request.path == "/health":
            return None
        expected = os.getenv("UGR_MESH_TOKEN")
        if not expected:
            return None
        token = request.headers.get("X-UGR-Mesh-Token")
        if token != expected:
            return jsonify({"error": "mesh_auth_failed"}), 401
        return None

    if register_routes:
        register_routes(app)

    @app.errorhandler(Exception)
    def _handle_error(exc):  # pragma: no cover - generic safety net
        return jsonify({"error": str(exc), "service_id": service_id}), 500

    return app


def read_json_body() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {}
    return dict(payload)
