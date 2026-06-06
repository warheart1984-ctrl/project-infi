"""Regression: capability-bridge status survives universal story_forge_audio adapter."""

from __future__ import annotations

import importlib


def test_capability_bridge_snapshot_includes_story_forge_audio_health():
    from src.jarvis_operator import jarvis_operator

    snapshot = jarvis_operator.capability_bridge_snapshot()
    module_health = snapshot.get("module_health") or {}
    story_forge = module_health.get("story_forge") or {}
    assert story_forge.get("module") == "story_forge_audio"
    assert story_forge.get("provider") == "aais_story_forge"


def test_capability_bridge_status_route_returns_200():
    api = importlib.import_module("src.api")
    client = api.app.test_client()
    response = client.get("/api/jarvis/capability-bridge/status")
    assert response.status_code == 200
    body = response.get_json(silent=True) or {}
    assert "capability_service_bridge" in body or "bridge_id" in body
