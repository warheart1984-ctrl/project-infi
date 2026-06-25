"""Tests for /api/pods — Discovery Pod ledger-truth cockpit API."""

from __future__ import annotations

from src.api import app
from src.ugr.discovery.pod_cockpit import build_pods_cockpit_payload, get_pod_cockpit_dto


def test_build_pods_payload_includes_jon_halstead() -> None:
    payload = build_pods_cockpit_payload()
    assert payload["count"] >= 1
    pods = {row["pod_id"]: row for row in payload["pods"]}
    jon = pods.get("pod:jon-halstead")
    assert jon is not None
    assert jon["display_name"] == "Jon Halstead"
    assert jon["proven_count"] == 28
    assert jon["total_reputation_awarded"] == 1790.0
    assert jon["discovery_count"] == 110
    assert jon["arc_tier"] == "beyond_body"
    assert jon["pod_reward_multiplier"] == 10.0


def test_get_pod_cockpit_dto_unknown() -> None:
    assert get_pod_cockpit_dto("pod:does-not-exist") is None


def test_list_pods_api() -> None:
    client = app.test_client()
    response = client.get("/api/pods")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == len(payload["pods"])
    jon = next((p for p in payload["pods"] if p["pod_id"] == "pod:jon-halstead"), None)
    assert jon is not None
    assert jon["proven_count"] == 28


def test_get_pod_api() -> None:
    client = app.test_client()
    response = client.get("/api/pods/pod:jon-halstead")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pod_id"] == "pod:jon-halstead"
    assert payload["operator_id"] == "operator:jon-halstead"


def test_get_pod_api_not_found() -> None:
    client = app.test_client()
    response = client.get("/api/pods/pod:missing")
    assert response.status_code == 404
