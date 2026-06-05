"""Adaptive Lane Organ — Alt-6 wake and lane resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _repo(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(REPO))


def test_wake_adaptive_lanes_persists_snapshot():
    from src.adaptive_lane_organ import wake_adaptive_lanes

    report = wake_adaptive_lanes(REPO)
    assert report["awakened"] is True
    assert report["lane_count"] >= 1
    assert "operator" in report["authority_lane"]
    path = REPO / ".runtime/governance/adaptive_lanes.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["lanes"]


def test_recipe_module_lane_in_registry():
    from src.adaptive_lane_organ import wake_adaptive_lanes

    report = wake_adaptive_lanes(REPO)
    assert "recipe_module_organ" in report["genes_with_lanes"]
    lane_ids = {lane["lane_id"] for lane in report["lanes"]}
    assert "operator" in lane_ids


def test_fabric_minimum_genes_in_awakened_registry():
    from src.adaptive_lane_organ import wake_adaptive_lanes
    from tools.governance.check_alt6_governed_eligibility import FABRIC_MINIMUM_GENES

    report = wake_adaptive_lanes(REPO)
    genes_with_lanes = set(report.get("genes_with_lanes") or [])
    for gene in FABRIC_MINIMUM_GENES:
        assert gene in genes_with_lanes, f"{gene} missing from awakened registry"


def test_resolve_lane_for_gene():
    from src.adaptive_lane_organ import resolve_lane_for_gene

    resolution = resolve_lane_for_gene("recipe_module_organ", root=REPO)
    assert resolution.lane_id == "operator"
    assert resolution.gene == "recipe_module_organ"


def test_lane_authorizes_non_policy_capability():
    from src.adaptive_lane_organ import lane_authorizes_capability, resolve_lane_for_gene

    resolution = resolve_lane_for_gene("recipe_module_organ", root=REPO)
    allowed = lane_authorizes_capability(resolution, "mystic")
    assert allowed.allowed


def test_lane_authorizes_policy_cap_blocks_on_mismatch():
    from src.adaptive_lane_organ import LaneResolution, lane_authorizes_capability

    resolution = LaneResolution(
        lane_id="builder",
        weight=0.5,
        capabilities=("approve_policy_changes",),
        gene="recipe_module",
    )
    blocked = lane_authorizes_capability(resolution, "approve_policy_changes")
    assert not blocked.allowed
    assert blocked.reason
    assert "operator" in blocked.reason


def test_status_api_shape():
    from src.adaptive_lane_organ import build_adaptive_lane_status

    status = build_adaptive_lane_status(REPO)
    assert status["adaptive_lane_organ_version"] == "adaptive_lane_organ.v1"
    assert status["awakened"] is True


def test_tier5_health_includes_lane_wake():
    from src.adaptive_lane_organ import wake_adaptive_lanes
    from src.governance_organs.adaptive_engine import AdaptiveEngine

    wake_adaptive_lanes(REPO)
    report = AdaptiveEngine(REPO).health_check()
    assert report.get("adaptive_lanes_awakened") is True
    assert report.get("adaptive_lane_count", 0) >= 1
