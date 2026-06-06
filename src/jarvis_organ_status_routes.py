"""Jarvis organ status route registrations (api.py decomposition slice)."""

# Mythic: Jarvis Organ Status Routes
# Engineering: JarvisOrganStatusRoutesEngine
from __future__ import annotations

import logging
from typing import Any, Callable

from flask import Flask, jsonify, request

from src.aais_ul_substrate import attach_ul_substrate

logger = logging.getLogger(__name__)

StatusBuilder = Callable[[], dict[str, Any]]

_ORGAN_STATUS_ROUTES: tuple[tuple[str, str, StatusBuilder], ...] = (
    (
        "/api/jarvis/memory-path-governance/status",
        "memory_path_governance",
        lambda: __import__(
            "src.memory_path_governance_organ",
            fromlist=["build_memory_path_governance_status"],
        ).build_memory_path_governance_status(),
    ),
    (
        "/api/jarvis/mission-board/status",
        "mission_board",
        lambda: __import__(
            "src.mission_board_organ",
            fromlist=["build_mission_board_status"],
        ).build_mission_board_status(
            session_id=str(request.args.get("session_id") or "").strip() or None
        ),
    ),
    (
        "/api/jarvis/otem-execution-substrate/status",
        "otem_execution_substrate",
        lambda: __import__(
            "src.otem_execution_substrate",
            fromlist=["build_otem_execution_status"],
        ).build_otem_execution_status(),
    ),
)


def register_jarvis_organ_status_routes(app: Flask) -> None:
    """Register a governed subset of /api/jarvis/*/status routes."""

    def _make_handler(key: str, builder: StatusBuilder):
        def _handler():
            try:
                return jsonify(attach_ul_substrate({key: builder()}))
            except Exception as exc:
                logger.error("Error reading %s status: %s", key, exc)
                return jsonify({"error": str(exc)}), 500

        _handler.__name__ = f"get_{key}_status"
        return _handler

    for path, key, builder in _ORGAN_STATUS_ROUTES:
        app.add_url_rule(path, endpoint=f"jarvis_{key}_status", view_func=_make_handler(key, builder), methods=["GET"])
