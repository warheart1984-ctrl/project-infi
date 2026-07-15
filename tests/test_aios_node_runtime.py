from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from constitutional.aios_node_runtime import (  # noqa: E402
    AIOSConstitutionalNodeRuntime,
    ConstitutionalAccessError,
)


def test_aios_ledger_is_hash_chained_and_replayable() -> None:
    runtime = AIOSConstitutionalNodeRuntime(node_id="node-001")
    runtime.record_provenance("prov-001", "", "seed", ("seed",))
    identity = runtime.invoke(
        "identity runtime",
        "register",
        {
            "identity_id": "person-001",
            "type": "person",
            "attributes": {"name": "Ada"},
            "provenance_id": "prov-001",
        },
    )
    runtime.invoke(
        "evidence runtime",
        "ingest",
        {
            "evidence_id": "evid-001",
            "identity_id": "person-001",
            "type": "receipt",
            "content_ref": "hash://evid-001",
            "provenance_id": "prov-001",
        },
    )
    runtime.record_relationship(
        "rel-001",
        "person-001",
        "person-001",
        "stewardship",
        "prov-001",
        steward_identity_id="person-001",
    )
    runtime.assert_trust(
        "trust-001",
        "rel-001",
        "person-001",
        0.82,
        {"scope": "node"},
        ("evid-001",),
    )

    packet = runtime.evaluate_governance(
        node_id="node-001",
        inputs={"simulation": True, "commitment": False},
        evidence_ids=("evid-001",),
        relationship_ids=("rel-001",),
        trust_ids=("trust-001",),
        governance_clauses=("evidence before assertion", "governance before autonomy"),
    )

    snapshot = runtime.snapshot()

    assert identity["identity_id"] == "person-001"
    assert runtime.ledger.verify_chain() is True
    assert runtime.replay()
    assert snapshot["ledger"]["chainValid"] is True
    assert packet.allowed is True
    assert packet.receipt_id
    assert packet.decision_id in runtime.ledger.decisions
    assert packet.receipt_id in runtime.ledger.receipts


def test_aios_runtime_rejects_unguarded_api_calls() -> None:
    runtime = AIOSConstitutionalNodeRuntime()

    try:
        runtime.invoke("unknown runtime", "register", {})
    except ConstitutionalAccessError as exc:
        assert "Unknown runtime" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected runtime guard to reject unknown runtime")

    try:
        runtime.invoke("identity runtime", "delete", {})
    except ConstitutionalAccessError as exc:
        assert "is not available" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected runtime guard to reject undeclared api")


def test_aios_governance_engine_emits_a_governed_decision_packet() -> None:
    runtime = AIOSConstitutionalNodeRuntime(node_id="node-002")
    runtime.record_provenance("prov-002", "", "bootstrap", ("bootstrap",))
    runtime.invoke(
        "identity runtime",
        "register",
        {
            "identity_id": "steward-001",
            "type": "person",
            "attributes": {"name": "Steward"},
            "provenance_id": "prov-002",
        },
    )
    runtime.invoke(
        "evidence runtime",
        "ingest",
        {
            "evidence_id": "evid-002",
            "identity_id": "steward-001",
            "type": "note",
            "content_ref": "hash://evid-002",
            "provenance_id": "prov-002",
        },
    )
    runtime.record_relationship(
        "rel-002",
        "steward-001",
        "steward-001",
        "stewardship",
        "prov-002",
        steward_identity_id="steward-001",
    )
    runtime.assert_trust("trust-002", "rel-002", "steward-001", 0.51, {"scope": "governance"}, ("evid-002",))

    packet = runtime.evaluate_governance(
        node_id="node-002",
        inputs={"execution": True, "simulation": False, "boundary": True},
        evidence_ids=("evid-002",),
        relationship_ids=("rel-002",),
        trust_ids=("trust-002",),
        governance_clauses=(
            "evidence before assertion",
            "governance before autonomy",
            "simulation before execution",
            "human judgment at boundaries",
        ),
    )

    assert packet.status in {"warning", "blocked", "allowed"}
    assert packet.governance_factor >= 0.0
    assert "evidence before assertion" in packet.clause_results[0]
    assert packet.conformance_status in {"pass", "fail"}
    assert packet.decision_id.startswith("decision::node-002")
    assert packet.receipt_id.startswith("receipt::node-002")


def test_aios_truth_runtime_is_interpretive() -> None:
    runtime = AIOSConstitutionalNodeRuntime(node_id="node-003")
    runtime.record_provenance("prov-003", "", "seed", ("seed",))
    runtime.invoke(
        "identity runtime",
        "register",
        {
            "identity_id": "source-001",
            "type": "system",
            "attributes": {"name": "Sensor"},
            "provenance_id": "prov-003",
        },
    )
    runtime.invoke(
        "evidence runtime",
        "ingest",
        {
            "evidence_id": "evid-003",
            "identity_id": "source-001",
            "type": "signal",
            "content_ref": "hash://evid-003",
            "provenance_id": "prov-003",
        },
    )
    runtime.invoke(
        "evidence runtime",
        "ingest",
        {
            "evidence_id": "evid-004",
            "identity_id": "source-001",
            "type": "signal",
            "content_ref": "hash://evid-004",
            "provenance_id": "prov-003",
        },
    )

    truth = runtime.evaluate_truth(("evid-003", "evid-004"), {"topic": "contextual"})

    assert truth["result"] == "interpretive"
    assert truth["band"] in {"low", "medium", "high"}
    assert truth["evidenceIds"] == ["evid-003", "evid-004"]
