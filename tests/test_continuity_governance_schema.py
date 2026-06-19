"""Schema shape checks for continuity_governance.v1.json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.continuity.trace_v1 import project_trace_v1
from src.continuity.ccs import build_store_from_scenario, load_scenario, trace_from_object


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "continuity_governance.v1.json"
CHIWERE_SCENARIO = REPO_ROOT / "fixtures" / "ccs" / "chiwere_lexeme_scenario.v1.json"


@pytest.fixture
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_includes_v1_trace_projection_defs(schema):
    defs = schema["$defs"]
    assert "ContinuityTraceV1" in defs
    assert "ContinuityMetrics" in defs
    assert "ContinuityGovernanceReceipt" in defs
    assert "ReputationWeights" in defs
    trace_required = set(defs["ContinuityTraceV1"]["required"])
    assert trace_required == {
        "trace_id",
        "subject_ref",
        "identity_refs",
        "event_refs",
        "evaluation_refs",
        "evidence_refs",
        "metrics_ref",
        "law_surfaces",
        "trace_hash",
    }


def test_chiwere_trace_v1_matches_schema_shape(schema):
    scenario = load_scenario(CHIWERE_SCENARIO)
    store = build_store_from_scenario(scenario)
    trace = trace_from_object(scenario["trace"])
    store.add_trace(trace)
    trace_v1 = project_trace_v1(
        trace,
        subject_ref="LEX-0001",
        metrics_ref="metrics.lexeme.chiwere.0001",
        created_at="2026-06-19T15:00:00Z",
    ).to_dict()

    defs = schema["$defs"]
    trace_schema = defs["ContinuityTraceV1"]
    for field in trace_schema["required"]:
        assert field in trace_v1
    assert len(trace_v1["trace_hash"]) == 64
    assert all(isinstance(item, str) for item in trace_v1["identity_refs"])
