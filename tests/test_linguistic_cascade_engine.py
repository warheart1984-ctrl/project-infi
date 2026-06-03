#!/usr/bin/env python3
"""Tests for linguistic_cascade_engine (Wave 10)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_cascade_engine import (  # noqa: E402
    affected_children,
    cascade_impact,
    validate_cascade_ack,
)

PARENT = "operator_cognition_coherence_fabric"
EXPECTED_CHILDREN = {
    "ai_factory_organ",
    "continuity_witness_organ",
    "forge_contractor_organ",
    "jarvis_protocol_organ",
    "project_infi_state_machine_organ",
    "reasoning_executive_organ",
}


def test_coherence_fabric_children():
    children = {g for g, _ in affected_children(PARENT, ROOT)}
    assert EXPECTED_CHILDREN.issubset(children)


def test_cascade_impact_no_change_when_fingerprint_same():
    before = {
        "mythic_label": "Coherence Fabric",
        "engineering_class": "OperatorCognitionCoherenceLayer",
    }
    report = cascade_impact(PARENT, {"genome": before}, {"genome": dict(before)}, ROOT)
    assert report.parent_changed is False
    assert report.children == []


def test_cascade_impact_lists_children_on_parent_change():
    before = {
        "mythic_label": "Old Mythic",
        "engineering_class": "OperatorCognitionCoherenceLayer",
    }
    after = {
        "mythic_label": "New Mythic",
        "engineering_class": "OperatorCognitionCoherenceLayer",
    }
    report = cascade_impact(PARENT, {"genome": before}, {"genome": after}, ROOT)
    assert report.parent_changed is True
    child_genes = {c.gene for c in report.children}
    assert EXPECTED_CHILDREN.issubset(child_genes)


def test_validate_cascade_ack_off_by_default():
    delta = {
        "gene": PARENT,
        "before": {"mythic_label": "A", "engineering_class": "OperatorCognitionCoherenceLayer"},
        "after": {"mythic_label": "B", "engineering_class": "OperatorCognitionCoherenceLayer"},
    }
    assert validate_cascade_ack(delta, ROOT) == []
