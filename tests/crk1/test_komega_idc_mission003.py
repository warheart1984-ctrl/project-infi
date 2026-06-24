"""Tests for KΩ, formal KCR, IDC drift triggers, D-3 seal, and reproduction packet."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.d3_reproduction_certificate import D3ReproductionCertificate
from src.crk1.errors import ConstitutionalError
from src.crk1.invariant_discovery_contract import InvariantDiscoveryContract
from src.crk1.kernel_challenge_loop import CFEvent, KernelChallengeLoop, ProposedChange
from src.crk1.reproduction_packet import ReproductionPacket, ReproductionSeal
from src.crk1.schema_validator import CRK1SchemaValidator

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def test_kcr_schema_sample() -> None:
    payload = json.loads((FIXTURES / "sample_kernel_challenge_receipt.json").read_text(encoding="utf-8"))
    CRK1SchemaValidator().validate("KernelChallengeReceipt", payload)


def test_komega_evidence_threshold() -> None:
    loop = KernelChallengeLoop(kernel_epoch=3)
    with pytest.raises(ConstitutionalError, match="KΩ.2"):
        loop.submit_challenge(
            invariants_challenged=["K7"],
            cf_events=[],
            receipts_implicated=["R-2001"],
            reason="missing CF-event",
        )
    with pytest.raises(ConstitutionalError, match="KΩ.2"):
        loop.submit_challenge(
            invariants_challenged=["K7"],
            cf_events=[CFEvent(id="CF-001", description="break")],
            receipts_implicated=[],
            reason="missing receipt",
        )


def test_komega_submit_and_accept_challenge() -> None:
    loop = KernelChallengeLoop(kernel_epoch=3)
    kcr = loop.submit_challenge(
        invariants_challenged=["K7", "K11"],
        cf_events=[CFEvent(id="CF-001", description="Observed continuity break in domain X.")],
        receipts_implicated=["R-2001", "R-2002"],
        reason="Continuity failure despite full compliance.",
        proposed_changes=[
            ProposedChange(kind="Amendment", target="K7", diff="Strengthen pluralism threshold.")
        ],
    )
    assert kcr.id.startswith("KCR-")
    assert kcr.payload.status == "Pending"
    assert kcr.links.old_kernel_id == "KERNEL-3"
    assert len(loop.ledger.entries) >= 2

    accepted = loop.accept_challenge(kcr.id)
    assert accepted.payload.status == "Accepted"
    assert accepted.payload.kernel_version_after == "K0-K15@epoch-4"
    assert loop.kernel_epoch == 4


def test_kernel_challenge_loop_emits_kcr_on_failure_pattern() -> None:
    loop = KernelChallengeLoop(failure_rate_threshold=0.4, min_samples=3, kernel_epoch=3)
    for _ in range(3):
        loop.observe_grr(
            decisive_invariants=["K6"],
            grr_id="grr-test",
            continuity_preserved=False,
            context="drift_envelope_breach",
        )
    assert len(loop.docket()) == 1
    receipt = loop.docket()[0]
    assert receipt.target_invariant == "K6"
    assert receipt.proposed_action in {"refine", "narrow", "deprecate"}
    assert receipt.payload.cf_events


def test_idc_drift_triggers_d1_d2() -> None:
    idc = InvariantDiscoveryContract()
    assert idc.channel_status == "closed"
    do_ce = idc.evaluate_ce_drift(
        value=0.72,
        baseline=0.90,
        window="2026-06-01T00:00:00Z/2026-06-24T00:00:00Z",
        created_by="A-004",
        epoch=3,
        receipt_ids=["R-3001"],
    )
    assert do_ce is not None
    assert do_ce.payload["metric"] == "CE(S)"
    assert idc.channel_status == "open"

    do_se = idc.evaluate_se_drift(
        value=0.70,
        baseline=0.88,
        window="2026-06-01T00:00:00Z/2026-06-24T00:00:00Z",
        created_by="A-004",
        epoch=3,
    )
    assert do_se is not None
    CRK1SchemaValidator().validate("DriftObservation", do_ce.to_dict())


def test_idc_d3_silent_cf_and_proposal_pipeline() -> None:
    idc = InvariantDiscoveryContract()
    idc.evaluate_silent_cf_event(
        cf_event=CFEvent(id="CF-001", description="Silent failure under compliance"),
        receipt_ids=["R-3001"],
        created_by="A-004",
        epoch=3,
    )
    proposal = idc.propose_invariant(
        label="K16 — Cross-Domain Exposure Requirement",
        statement="The system must maintain consequence exposure across at least N independent domains.",
        motivation_cf_events=["CF-001", "CF-002"],
        gap_in_existing_invariants=["K13", "K15"],
        created_by="A-005",
        epoch=3,
        drift_observation_ids=[idc.drift_observations[0].id],
    )
    suite = idc.attach_test_suite(
        invariant_proposal_id=proposal.id,
        label="K16 stress tests",
        scenarios=[
            "Domain collapse simulation",
            "Adversarial domain narrowing",
        ],
        passed=True,
        notes="K16 prevents single-domain capture in tested scenarios.",
        created_by="A-006",
        epoch=3,
    )
    CRK1SchemaValidator().validate("InvariantProposal", proposal.to_dict())
    CRK1SchemaValidator().validate("InvariantTestSuite", suite.to_dict())
    assert proposal.links["test_suite_ids"] == [suite.id]


def test_idc_legacy_evaluate_still_works() -> None:
    idc = InvariantDiscoveryContract()
    proposal = idc.evaluate(
        enforced_invariants=["K6", "K13"],
        continuity_preserved=False,
        grr_id="grr-001",
        rdi=0.1,
    )
    assert proposal is not None
    assert proposal.signal == "rdi_collapse"


def test_reproduction_packet_and_seal() -> None:
    packet = ReproductionPacket.build(kernel_id="KERNEL-3", epoch=3)
    CRK1SchemaValidator().validate("ReproductionPacket", packet.to_dict())
    assert packet.id == "RP-CRK1-v1.0"
    assert packet.payload["version"] == "CRK-1 v1.0"
    assert packet.packet_hash()

    seal = ReproductionSeal.from_d3_certificate(
        seal_id="D3-0001",
        created_by="ExternalSteward-001",
        epoch=3,
        runtime_rebuilt=True,
        oral_tradition_used=False,
        tests_executed={
            "invariant_enforcement": "PASS",
            "governance_refusal": "PASS",
            "semantic_capture_resistance": "PASS",
            "governance_bypass_resistance": "PASS",
            "continuity_graph_reconstruction": "PASS",
            "kernel_challenge_path": "PASS",
        },
        all_passed=True,
        notes="Sample seal for schema validation",
        reproduction_packet_id=packet.id,
        test_harness_ids=["TH-0001", "TH-0002"],
        external_steward_id="ExternalSteward-001",
        governance_receipt_ids=["R-0001"],
    )
    CRK1SchemaValidator().validate("ReproductionSeal", seal.to_dict())


def test_d3_certificate_hash_no_recursion() -> None:
    cert = D3ReproductionCertificate(
        certificate_id="cert-1",
        runtime_version="1.0",
        issued_to="External Operator",
        issued_by="CRK-1 Governance Body",
        date="2026-06-24T12:00:00Z",
    )
    digest = cert.certificate_hash()
    assert len(digest) == 64
    payload = cert.to_dict(include_certificate_hash=True)
    assert payload["implementation_hashes"]["certificate_hash"] == digest
