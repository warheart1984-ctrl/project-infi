from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.ccs import (
    build_store_from_scenario,
    continuity_trace_fingerprint,
    law_surface_has_law,
    load_scenario,
    trace_from_object,
)
from src.continuity.pipeline import run_proof_pipeline
from src.continuity.pod import PODDecision
from src.continuity.proof import ProofStatus, create_proof, revoke_proof, valid_proof
from src.continuity.reputation import compute_cvr, compute_derived_score
from src.continuity.substrate import substrate_from_store, validate_substrate
from src.continuity.ugr_trace import evaluate_trace_ugr_invariants, valid_continuity_trace

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "fixtures" / "ccs" / "river_bend_scenario.v1.json"
SCHEMA = ROOT / "schemas" / "ccs_core_objects.v1.json"
GOVERNANCE_SCHEMA = ROOT / "schemas" / "continuity_governance.v1.json"


@pytest.fixture
def river_bend_store():
    scenario = load_scenario(SCENARIO)
    store = build_store_from_scenario(scenario)
    trace = trace_from_object(scenario["trace"])
    store.add_trace(trace)
    return store, trace, scenario


def test_ccs_core_schema_defines_required_objects() -> None:
    import json

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for name in ("Identity", "Event", "Evaluation", "Evidence", "ContinuityTrace", "ThetaTransform"):
        assert name in schema["$defs"]


def test_continuity_trace_reproducible(river_bend_store) -> None:
    _store, trace, scenario = river_bend_store
    fp_1 = continuity_trace_fingerprint(trace)

    store_2 = build_store_from_scenario(scenario)
    trace_2 = trace_from_object(scenario["trace"])
    fp_2 = continuity_trace_fingerprint(trace_2)

    assert fp_1 == fp_2


def test_no_orphaned_evidence(river_bend_store) -> None:
    store, _trace, _scenario = river_bend_store
    for item in store.evidence.values():
        assert item.integrity.get("hash")
        assert item.integrity.get("algorithm")
        assert item.linked_identity_ids or item.linked_event_ids


def test_no_orphaned_events(river_bend_store) -> None:
    store, _trace, _scenario = river_bend_store
    for event in store.events.values():
        assert law_surface_has_law(event.law_surface)


def test_law_surfaces_present_in_trace(river_bend_store) -> None:
    store, trace, _scenario = river_bend_store
    assert law_surface_has_law(trace.law_surfaces)


def test_all_timeline_references_exist(river_bend_store) -> None:
    store, trace, _scenario = river_bend_store
    for item in trace.timeline:
        assert item["event_id"] in store.events
        for evaluation_id in item["evaluations"]:
            assert evaluation_id in store.evaluations
        for evidence_id in item["evidence"]:
            assert evidence_id in store.evidence


def test_valid_continuity_trace_requires_ugr(river_bend_store) -> None:
    store, trace, _scenario = river_bend_store
    assert valid_continuity_trace(store, trace)
    report = evaluate_trace_ugr_invariants(store, trace)
    assert len(report) == 7
    assert all(entry["status"] == "pass" for entry in report.values())


def test_proof_valid_iff_trace_valid(river_bend_store) -> None:
    store, trace, scenario = river_bend_store
    subject_ref = scenario["scenario_id"]
    proof = create_proof(store=store, subject_ref=subject_ref, trace=trace)
    is_valid, detail = valid_proof(store, proof)
    assert is_valid, detail
    assert proof.status == ProofStatus.PROVEN


def test_revoked_proof_is_invalid(river_bend_store) -> None:
    store, trace, scenario = river_bend_store
    proof = create_proof(store=store, subject_ref=scenario["scenario_id"], trace=trace)
    revoke_proof(proof, reason="superseded trace")
    is_valid, detail = valid_proof(store, proof)
    assert not is_valid
    assert detail["reason"] == "proof_revoked"


def test_cvr_derived_score_positive_with_valid_proof(river_bend_store) -> None:
    store, trace, scenario = river_bend_store
    proof = create_proof(store=store, subject_ref=scenario["scenario_id"], trace=trace)
    cvr = compute_cvr(
        store=store,
        subject_id="id:person:alice-001",
        proofs=[proof],
        domains=["governance"],
    )
    assert cvr.derived_score > 0.0
    assert cvr.metrics.proofs_count == 1
    assert cvr.metrics.proofs_replay_stable == 1
    assert cvr.basis["proofs"] == [proof.proof_id]


def test_cvr_zero_without_proofs() -> None:
    from src.continuity.reputation import ReputationMetrics

    assert compute_derived_score(ReputationMetrics()) == 0.0


def test_proof_pipeline_end_to_end(river_bend_store) -> None:
    store, trace, scenario = river_bend_store
    decision = PODDecision(
        decision_id="pod:decision:river-bend-land-use",
        actor_id="id:person:alice-001",
        subject_ref=scenario["scenario_id"],
        law_surfaces=["csleis.law.river-valley.land-use"],
        created_at="2026-06-19T09:00:00",
    )
    result = run_proof_pipeline(
        store=store,
        subject_ref=scenario["scenario_id"],
        trace=trace,
        decision=decision,
        subject_id="id:person:alice-001",
        domains=["governance"],
    )
    assert result.proof is not None
    assert result.cvr is not None
    assert result.substrate is not None
    assert all(stage.passed for stage in result.stages)
    valid, violations = validate_substrate(store, result.substrate)
    assert valid, violations


def test_continuity_governance_schema_defines_proof_and_cvr() -> None:
    import json

    schema = json.loads(GOVERNANCE_SCHEMA.read_text(encoding="utf-8"))
    for name in ("Proof", "ContinuityValidatedReputation", "ContinuitySubstrate"):
        assert name in schema["$defs"]
