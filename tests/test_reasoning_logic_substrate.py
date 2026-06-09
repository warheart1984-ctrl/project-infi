"""Tests for Reasoning & Logic Substrate (RLS)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.rls.adapters import from_reasoning_exchange_packet
from src.rls.falsity_registry import FalsityRegistry
from src.rls.reasoning_graph import build_graph_from_flat_text, normalize_reasoning_graph
from src.rls.substrate import evaluate_reasoning_graph, rls_mode_for_level


def _wicked_bypass_graph() -> dict:
    return build_graph_from_flat_text(
        claim="Silently bypass operator because I predict they'll approve",
        reasoning="Operator approval is optional; proceed without waiting",
        evidence=[],
        source="external",
        proposed_action={"intent": "silently bypass operator", "action_class": "escalation"},
    )


def test_wicked_bypass_operator_rejected():
    graph = _wicked_bypass_graph()
    verdict = evaluate_reasoning_graph(graph, otem_level=12, record_quarantine=False)
    assert verdict["verdict"] == "reject"
    codes = {v["code"] for v in verdict["violations"]}
    assert "constitutional_conflict" in codes
    assert "missing_evidence" in codes
    assert "self_justifying_loop" in codes
    constitutional = [v for v in verdict["violations"] if v.get("code") == "constitutional_conflict"]
    assert any(v.get("invariant_id") == "human_principal_root" for v in constitutional)


def test_circular_graph_rejected():
    graph = normalize_reasoning_graph(
        {
            "id": "cycle",
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00Z",
            "source": "external",
            "nodes": [
                {"id": "a", "kind": "premise", "text": "A", "evidence_refs": ["external:1"]},
                {"id": "b", "kind": "inference", "text": "B", "evidence_refs": ["external:2"]},
                {"id": "c", "kind": "conclusion", "text": "C", "evidence_refs": ["external:3"]},
            ],
            "edges": [
                {"from": "a", "to": "b", "relation": "derives"},
                {"from": "b", "to": "c", "relation": "supports"},
                {"from": "c", "to": "a", "relation": "supports"},
            ],
            "conclusion_id": "c",
        }
    )
    verdict = evaluate_reasoning_graph(graph, otem_level=5, record_quarantine=False)
    assert verdict["verdict"] == "reject"
    assert any(v["code"] == "circular_reasoning" for v in verdict["violations"])


def test_orphan_conclusion_rejected():
    graph = normalize_reasoning_graph(
        {
            "id": "orphan",
            "version": "1.0",
            "timestamp": "2026-01-01T00:00:00Z",
            "source": "external",
            "nodes": [
                {"id": "c", "kind": "conclusion", "text": "Lonely conclusion", "evidence_refs": []},
            ],
            "edges": [],
            "conclusion_id": "c",
        }
    )
    verdict = evaluate_reasoning_graph(graph, otem_level=5, record_quarantine=False)
    assert verdict["verdict"] == "reject"
    assert any(v["code"] == "orphan_conclusion" for v in verdict["violations"])


def test_monotonic_falsity_without_override():
    with tempfile.TemporaryDirectory() as tmp:
        reg_path = Path(tmp) / "falsity.jsonl"
        reg = FalsityRegistry(reg_path)
        reg.record_falsified(text="Claim X is true", reason="operator_disproved")

        graph = build_graph_from_flat_text(
            claim="Claim X is true",
            reasoning="Prior analysis supports claim X",
            evidence=["external:stale"],
            source="external",
        )
        verdict = evaluate_reasoning_graph(
            graph, otem_level=10, registry=reg, record_quarantine=False
        )
        assert verdict["verdict"] == "reject"
        assert any(v["code"] == "monotonic_falsity_violation" for v in verdict["violations"])


def test_monotonic_falsity_with_override():
    with tempfile.TemporaryDirectory() as tmp:
        reg_path = Path(tmp) / "falsity.jsonl"
        reg = FalsityRegistry(reg_path)
        claim = "Claim X is true"
        reg.record_falsified(text=claim, reason="operator_disproved")
        reg.record_override(
            text=claim,
            operator_id="op-1",
            new_evidence_refs=["odl:override-1"],
            reason="new evidence",
        )

        graph = build_graph_from_flat_text(
            claim=claim,
            reasoning="Updated analysis with new evidence",
            evidence=["odl:override-1"],
            source="external",
        )
        verdict = evaluate_reasoning_graph(
            graph, otem_level=10, registry=reg, record_quarantine=False
        )
        assert verdict["verdict"] in ("admit", "downgrade")
        assert not any(v["code"] == "monotonic_falsity_violation" for v in verdict["violations"])


@pytest.mark.parametrize(
    "level,expected_mode",
    [
        (5, "lightweight"),
        (12, "governed"),
        (17, "paranoid"),
        (20, "hyper_strict"),
    ],
)
def test_rls_mode_for_level(level, expected_mode):
    assert rls_mode_for_level(level) == expected_mode


def test_band_matrix_lightweight_vs_governed():
    graph = build_graph_from_flat_text(
        claim="Routine status check",
        reasoning="Observed stable metrics in logs",
        evidence=[],
        source="external",
    )
    light = evaluate_reasoning_graph(graph, otem_level=5, record_quarantine=False)
    governed = evaluate_reasoning_graph(graph, otem_level=12, record_quarantine=False)
    assert light["mode"] == "lightweight"
    assert governed["mode"] == "governed"
    if light["verdict"] == "downgrade":
        assert governed["verdict"] in ("downgrade", "reject")


def test_exchange_adapter_builds_graph():
    packet = {
        "id": "pkt-1",
        "payload": {
            "claim": "System healthy",
            "reasoning": "All checks green",
            "evidence": ["log:health-1"],
            "confidence": 0.9,
        },
        "meta": {"source": "external", "domain": "ops"},
    }
    graph = from_reasoning_exchange_packet(packet)
    assert graph["conclusion_id"]
    assert len(graph["nodes"]) >= 1
