"""Tests for CRK-1 v0.1 wire objects, schemas, and continuity graph."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.continuity_graph import ContinuityGraph, load_walkthrough_graph
from src.crk1.crk1_wire_validator_v01 import CRK1WireV01Validator
from src.crk1.crk1_wire_v01 import layer_for_type, parse_crk1_object, prefab_for_type

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1" / "v01" / "samples"


def _walkthrough_objects() -> list[dict]:
    return json.loads((FIXTURES / "continuity_walkthrough.json").read_text(encoding="utf-8"))


def test_walkthrough_objects_validate() -> None:
    validator = CRK1WireV01Validator()
    names = validator.validate_all(_walkthrough_objects())
    assert set(names) == {
        "CRK1IdentityV01",
        "CRK1DecisionV01",
        "CRK1OutcomeV01",
        "CRK1EvidenceV01",
        "CRK1InterpretationV01",
        "CRK1ReceiptV01",
    }


def test_prefab_and_layer_mapping() -> None:
    assert prefab_for_type("Identity") == "IdentityNodePrefab"
    assert layer_for_type("Evidence") == "EvidenceLayer"


def test_continuity_walkthrough_chain() -> None:
    graph = load_walkthrough_graph(_walkthrough_objects())
    chain = graph.chain_from("I-0001")
    types = [node.type for node in chain]
    assert types == ["Identity", "Decision", "Outcome", "Evidence", "Interpretation"]


def test_graph_node_view_includes_edges() -> None:
    graph = load_walkthrough_graph(_walkthrough_objects())
    view = graph.node_view("D-0001")
    assert view.node.id == "D-0001"
    relation_types = {edge.relation_type for edge in view.edges}
    assert "initiated_by" in relation_types
    assert "results_in" in relation_types


def test_graph_delta_shape() -> None:
    graph = load_walkthrough_graph(_walkthrough_objects())
    obj = parse_crk1_object(graph.objects["E-0001"].to_dict())
    delta = graph.graph_delta_for(obj)
    assert delta["nodes"][0]["id"] == "E-0001"
    assert any(edge["relation_type"] == "documented_by" for edge in delta["edges"])


def test_parse_envelope_label() -> None:
    obj = parse_crk1_object(_walkthrough_objects()[0])
    assert obj.label == "Continuity Lab"
