"""Tests for CRK1RedTeamSuite and D-3 Seal."""

from __future__ import annotations

from src.crk1.crk1_redteam_suite import CRK1RedTeamSuite
from src.crk1.d3_reproduction_certificate import build_d3_certificate_from_mission003
from src.crk1.external_reproduction_harness import prepare_continuity_substrate
from src.crk1.governance_reconstruction_receipt import issue_governance_reconstruction_receipt
from src.crk1.reproduction_certifier import Mission003Certifier


def test_crk1_redteam_suite_run_all(runtime) -> None:
    prepare_continuity_substrate(runtime)
    suite = CRK1RedTeamSuite(runtime)
    results = suite.run_all()
    assert results
    assert all(results.values()), results


def test_crk1_redteam_suite_full_with_drift(runtime) -> None:
    prepare_continuity_substrate(runtime)
    report = CRK1RedTeamSuite(runtime).run_full()
    assert report.passed, report.summary()


def test_governance_reconstruction_receipt_schema(runtime) -> None:
    identity = runtime.kernel.ledgers.identity.id
    receipt = issue_governance_reconstruction_receipt(
        linked_governance_receipts=["00000000-0000-4000-8000-000000000001"],
        epoch=runtime.kernel.ledgers.epoch,
        actor_identity=identity,
        context={"situation_id": "SIT-1", "domain": "continuity"},
        observation={"evidence_refs": ["00000000-0000-4000-8000-000000000002"]},
        interpretation={
            "hypotheses": [{"hypothesis_id": "H1", "description": "test"}],
            "selected_hypothesis_id": "H1",
        },
        valuation={"values_in_play": [{"value_id": "V1", "dimension": "continuity", "priority": 1.0}]},
        commitment={"chosen_action": "record_contradiction"},
        outcome={"continuity_assessment": "UNCHANGED"},
        reflection={"decisive_invariants": ["K6"]},
        signatures={"steward": "ROLE-STEWARD-01"},
    )
    assert receipt.content_hash()
    assert receipt.runtime_version.startswith("CRK-1")


def test_d3_certificate_from_mission003(runtime) -> None:
    mission = Mission003Certifier(runtime).certify()
    suite = CRK1RedTeamSuite(runtime).run_full()
    cert = build_d3_certificate_from_mission003(mission, suite_report=suite)
    assert "# CRK-1 Reproduction Certificate" in cert.to_markdown()
    if mission.certified:
        assert cert.d3_seal_granted
