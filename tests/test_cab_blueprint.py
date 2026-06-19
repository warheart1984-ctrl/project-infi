"""CAB blueprint tests — ontology, ledger, invariants, Nova receipt ingest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.continuity.cab import (
    CABLedger,
    CABObjectType,
    DecisionRecord,
    IntentRecord,
    ingest_ciems_transformation_event,
    ingest_neomundi_measurement,
    ingest_nova_continuity_governance,
    load_cab_scenario,
    populate_ledger_from_scenario,
)
from src.continuity.cab_invariants import evaluate_cab_invariants

ROOT = Path(__file__).resolve().parents[1]
CAB_SCHEMA = ROOT / "schemas" / "cab.v1.json"
GOVERNANCE_DEMO = ROOT / "fixtures" / "cab" / "governance_lineage_demo.v1.yaml"


@pytest.fixture
def cab_schema() -> dict:
    return json.loads(CAB_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture
def governance_ledger() -> CABLedger:
    scenario = load_cab_scenario(GOVERNANCE_DEMO)
    return populate_ledger_from_scenario(scenario)


def test_cab_schema_defines_eight_object_types(cab_schema):
    defs = cab_schema["$defs"]
    expected = {
        "IntentRecord",
        "DecisionRecord",
        "AssumptionRecord",
        "EvidenceChain",
        "ContinuityReceipt",
        "FounderKnowledgeSnapshot",
        "SuccessionProtocol",
        "ReconstructionPlan",
    }
    assert expected.issubset(set(defs.keys()))


def test_governance_lineage_demo_passes_cab_invariants(governance_ledger):
    report = evaluate_cab_invariants(governance_ledger)
    assert report.passed, report.to_dict()


def test_cab_ledger_supersede_preserves_non_erasure():
    ledger = CABLedger()
    intent_v1 = IntentRecord(
        intent_id="cab.intent.test",
        authors=["steward:a"],
        articulated_at="2026-06-19T10:00:00Z",
        scope={"system": "test"},
        problem_statement="initial",
        desired_outcomes=["v1"],
        created_at="2026-06-19T10:00:00Z",
    )
    ledger.append(intent_v1)
    intent_v2 = IntentRecord(
        intent_id="cab.intent.test.v2",
        authors=["steward:a"],
        articulated_at="2026-06-19T11:00:00Z",
        scope={"system": "test"},
        problem_statement="refined",
        desired_outcomes=["v2"],
        prior_intent_refs=["cab.intent.test"],
        created_at="2026-06-19T11:00:00Z",
    )
    ledger.supersede("cab.intent.test", intent_v2)
    assert len(ledger.entries) == 2
    old = ledger.get_latest("cab.intent.test")
    assert old is not None
    assert old.superseded
    assert old.payload.get("superseded_by") == "cab.intent.test.v2"


def test_ingest_nova_continuity_governance():
    ledger = CABLedger()
    continuity_governance = {
        "proof": {
            "proof_id": "proof.nova.test",
            "status": "PROVEN",
            "law_surfaces": ["aais.law.runtime.system", "ugr.continuity"],
            "replay_fingerprint": "a" * 64,
        },
        "cvr": {"cvr_id": "cvr.nova:test", "derived_score": 0.75, "law_surfaces": ["ugr.continuity"]},
        "continuity_trace": {
            "trace_id": "ct.nova.test",
            "trace_hash": "b" * 64,
        },
    }
    receipt = ingest_nova_continuity_governance(
        trace_id="nova-turn-test",
        identity_context={"instance_id": "nova-test", "tenant_id": "local"},
        continuity_governance=continuity_governance,
        event_description="test lawful turn",
        created_at="2026-06-19T12:00:00Z",
        decision_refs=["cab.decision.nova-in-urg"],
        ledger=ledger,
    )
    assert receipt.proof_id == "proof.nova.test"
    assert receipt.cvr_id == "cvr.nova:test"
    assert ledger.get_latest(receipt.receipt_id) is not None


def test_orphan_decision_fails_causal_linkage_invariant():
    ledger = CABLedger()
    ledger.append(
        DecisionRecord(
            decision_id="cab.decision.orphan",
            decision_makers=["steward:x"],
            chosen_option="orphan",
            rationale="no intent",
            intent_refs=["cab.intent.missing"],
            created_at="2026-06-19T12:00:00Z",
        )
    )
    report = evaluate_cab_invariants(ledger)
    cl = next(item for item in report.results if item.invariant_id == "CL")
    assert cl.status == "fail"


def test_ciems_transformation_event_ingests_as_linked_decision():
    from tools.stress.cc01_controlled_collapse_harness import CiemsEvent

    ledger = CABLedger()
    ledger.append(
        IntentRecord(
            intent_id="cab.intent.ciems.cc01",
            authors=["steward:jon"],
            articulated_at="2026-06-19T12:00:00Z",
            scope={"system": "CIEMS", "harness": "CC-01"},
            problem_statement="Governed transformation events must remain reconstructable.",
            desired_outcomes=["link transformation decisions to evidence"],
            created_at="2026-06-19T12:00:00Z",
        )
    )
    event = CiemsEvent(
        timestamp="2026-06-19T12:01:00Z",
        thread_id="thread-7",
        event_type="workload_edit",
        input="normalize transform",
        context_hash_before="a" * 64,
        context_hash_after="b" * 64,
        output_hash="c" * 64,
        state_change="edit",
        file_target="agent/project/main.py",
        conflict_flag=False,
        failure_code="",
        latency_ms=42,
        backend="nova",
        nova_request_id="req-7",
        nova_session_id="sess-7",
    ).to_dict()

    decision = ingest_ciems_transformation_event(
        event,
        intent_refs=["cab.intent.ciems.cc01"],
        decision_makers=["ciems:cc01"],
        govern_policy_refs=["policy:ciems.cc01"],
        continuity_receipt_refs=["cab.receipt.nova-turn-7"],
        ledger=ledger,
    )

    evidence = ledger.list_by_type(CABObjectType.EVIDENCE_CHAIN)
    assert len(evidence) == 1
    assert decision.intent_refs == ["cab.intent.ciems.cc01"]
    assert decision.evidence_chain_refs == [evidence[0].object_id]
    assert decision.continuity_receipt_refs == ["cab.receipt.nova-turn-7"]
    assert evaluate_cab_invariants(ledger).passed


def test_neomundi_measurement_ingest_is_stable_and_deduplicated():
    ledger = CABLedger()
    measurement = {
        "measurement_id": "neomundi.measurement.mri.001",
        "source": "neomundi:mri",
        "method": "runMRI",
        "integrity": "sha3-256:" + "d" * 64,
        "measured_at": "2026-06-19T12:02:00Z",
    }

    first = ingest_neomundi_measurement(
        measurement,
        decision_refs=["cab.decision.ciems.thread-7"],
        continuity_receipt_refs=["cab.receipt.nova-turn-7"],
        ledger=ledger,
    )
    second = ingest_neomundi_measurement(
        measurement,
        decision_refs=["cab.decision.ciems.thread-7"],
        continuity_receipt_refs=["cab.receipt.nova-turn-7"],
        ledger=ledger,
    )

    assert first.chain_id == second.chain_id
    assert len(ledger.list_by_type(CABObjectType.EVIDENCE_CHAIN)) == 1
    assert first.neomundi_measurement_refs == ["neomundi.measurement.mri.001"]
    assert "sha3-256:" in first.integrity_assessment


def test_cvr_recompute_auto_ingests_cab_receipt_when_enabled(tmp_path, monkeypatch):
    from nova.governance.cvr_recompute import CVRRegistry, recompute_cvr_for_lawful_turn
    from nova.identity import NovaIdentity

    cab_store = tmp_path / "cab" / "ledger.jsonl"
    monkeypatch.setenv("CAB_AUTO_INGEST", "1")
    monkeypatch.setenv("CAB_STORE", str(cab_store))

    recompute_cvr_for_lawful_turn(
        identity=NovaIdentity(tier="nova", operator_session_id="test", instance_id="cab-auto"),
        trace_id="cab-auto-001",
        tenant_id="local",
        capability="observe",
        prompt_sha256="1" * 64,
        output_sha256="2" * 64,
        memory_facts_sha256="3" * 64,
        timestamp="2026-06-19T12:03:00Z",
        nova_ugr_report={"identity": {"status": "pass"}},
        registry=CVRRegistry(),
    )

    ledger = CABLedger.open(cab_store)
    receipts = ledger.list_by_type(CABObjectType.CONTINUITY_RECEIPT)
    assert [receipt.object_id for receipt in receipts] == ["cab.receipt.cab-auto-001"]
    assert receipts[0].payload["proof_id"] == "proof.nova.cab-auto-001"
