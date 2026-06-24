"""Tests for Mission #004/#005 — GRR, RCL, KCL, R-3 certifier."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.governance_reconstruction_receipt import (
    GRRBinding,
    GRRCommitment,
    GRRObservation,
    GRRInterpretation,
    GRROutcome,
    GRRReflection,
    GRRValuation,
    GovernanceReconstructionReceipt,
    EvidenceRef,
    Hypothesis,
    ValueDimension,
    Tradeoff,
)
from src.crk1.invariant_discovery_contract import InvariantDiscoveryContract
from src.crk1.kernel_challenge_loop import KernelChallengeLoop
from src.crk1.reality_contact_layer import (
    ControlLevel,
    RealityDomain,
    RealitySurfaceRegistry,
    assert_reality_contact_layer,
    check_k14_anti_domestication,
    compute_reality_diversity_index,
)
from src.crk1.reconstruction_certifier import Mission005ReconstructionCertifier
from src.crk1.reconstruction_trace import ReconstructionTrace
from src.crk1.schema_validator import CRK1SchemaValidator

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def _sample_grr() -> GovernanceReconstructionReceipt:
    payload = json.loads((FIXTURES / "sample_governance_reconstruction_receipt.json").read_text(encoding="utf-8"))
    return GovernanceReconstructionReceipt.model_validate(payload)


def _sample_trace() -> ReconstructionTrace:
    payload = json.loads((FIXTURES / "sample_reconstruction_trace.json").read_text(encoding="utf-8"))
    return ReconstructionTrace.model_validate(payload)


def _healthy_registry() -> RealitySurfaceRegistry:
    registry = RealitySurfaceRegistry(min_uncontrolled_domains=2, min_independent_channels=2)
    registry.add(
        RealityDomain(
            domain_id="D_market",
            label="external market",
            control_level=ControlLevel.NONE,
            consequence_intensity=0.9,
        )
    )
    registry.add(
        RealityDomain(
            domain_id="D_regulator",
            label="independent regulator",
            control_level=ControlLevel.PARTIAL,
            consequence_intensity=0.8,
        )
    )
    registry.add(
        RealityDomain(
            domain_id="D_redteam",
            label="adversarial red team",
            control_level=ControlLevel.NONE,
            consequence_intensity=0.85,
        )
    )
    return registry


def test_grr_validates_against_schema() -> None:
    grr = _sample_grr()
    CRK1SchemaValidator().validate("GovernanceReconstructionReceipt", grr.to_dict())
    assert grr.interpretation.selected_model == "H1"
    assert "K6" in grr.binding.decisive_invariants


def test_rdi_and_k13_k15() -> None:
    registry = _healthy_registry()
    rdi = compute_reality_diversity_index(registry)
    assert rdi > 0.0
    metrics = assert_reality_contact_layer(registry)
    assert metrics["rdi"] == rdi


def test_k13_fails_when_surfaces_domesticated() -> None:
    registry = RealitySurfaceRegistry(min_uncontrolled_domains=2)
    registry.add(
        RealityDomain(
            domain_id="D_internal",
            label="internal only",
            control_level=ControlLevel.HIGH,
            consequence_intensity=0.9,
        )
    )
    with pytest.raises(ConstitutionalError, match="K13"):
        assert_reality_contact_layer(registry)


def test_k14_blocks_rdi_drop() -> None:
    with pytest.raises(ConstitutionalError, match="K14"):
        check_k14_anti_domestication(0.6, 0.4)


def test_kernel_challenge_loop_emits_kcr() -> None:
    loop = KernelChallengeLoop(failure_rate_threshold=0.4, min_samples=3)
    challenges = []
    for _ in range(3):
        challenges.extend(
            loop.observe_grr(
                decisive_invariants=["K6"],
                grr_id="grr-test",
                continuity_preserved=False,
                context="drift_envelope_breach",
            )
        )
    assert len(loop.docket()) == 1
    assert loop.docket()[0].target_invariant == "K6"
    assert loop.docket()[0].proposed_action in {"refine", "narrow", "deprecate"}


def test_idc_proposes_on_unexplained_failure() -> None:
    idc = InvariantDiscoveryContract()
    proposal = idc.evaluate(
        enforced_invariants=["K6", "K13"],
        continuity_preserved=False,
        grr_id="grr-001",
        rdi=0.1,
    )
    assert proposal is not None
    assert proposal.signal == "rdi_collapse"
    assert len(idc.pending()) == 1


def test_r3_certifier_with_fixtures() -> None:
    grr = _sample_grr()
    trace = _sample_trace()
    registry = _healthy_registry()
    report = Mission005ReconstructionCertifier().certify(
        traces=[trace],
        grrs=[grr],
        reality_registry=registry,
        challenge_loop=KernelChallengeLoop(),
    )
    assert report.seal == "R-3"
    assert report.levels.r1_trace_schema is True
    assert report.levels.r2_grr_complete is True
    assert report.levels.r3_judgment_reconstructable is True
    assert report.levels.r4_reality_contact is True
    assert report.certified is True
