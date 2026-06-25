"""Reconstructability fitness runtime — v0 audit suite (R-F1 … R-F10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from constitutional.core.models import StateObject
from constitutional.runtime import (
    ReconstructabilityFailureClass as RF,
    ReconstructabilityFitnessRuntime,
    ConstitutionalStateRuntime,
)
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AmendmentEvaluationReceiptV2,
    AmendmentImplementationReceiptV2,
    AmendmentPayloadV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    DecisionReceiptV2,
    DivergencePayloadV2,
    DivergenceReceiptV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    new_receipt_id,
)
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER


@pytest.fixture(autouse=True)
def _isolate_receipt_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def _base_blocks(*, lifecycle_stage: str = "decision") -> dict:
    return {
        "inputs": ReceiptInputsV2(request_id="task-1", payload_hash="sha256:abc"),
        "outputs": ReceiptOutputsV2(status="executed", result_hash="sha256:def"),
        "invariant": InvariantBlockV2(
            name="workspace_integrity",
            description="Paths stay inside workspace jail",
            satisfied=True,
        ),
        "evidence": EvidenceBundleV2(
            bundle_id="evb-1",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        "authority": AuthorityBlockV2(
            source="operator:builder",
            jurisdiction="workspace",
            legitimacy_basis="Article XIII",
        ),
        "reproducibility": ReproducibilityBlockV2(is_reproducible=True, mode="structural"),
        "impact_boundary": ImpactBoundaryV2(
            scope_in=["workspace"],
            scope_out=["network", "secrets"],
        ),
        "accountability": AccountabilityBlockV2(primary_accountable_party="operator"),
        "signatures": SignaturesBlockV2(runtime_signature="sig-runtime"),
        "continuity": ContinuityBlockV2(lineage_hash="sha256:lineage"),
        "lifecycle": LifecycleBlockV2(stage=lifecycle_stage),
    }


def _decision(**overrides: object) -> DecisionReceiptV2:
    blocks = _base_blocks()
    blocks.update(overrides)
    return DecisionReceiptV2(
        receipt_id=new_receipt_id("decision"),
        runtime="operator",
        timestamp="2026-06-23T12:00:00Z",
        action_type="tool_governance",
        **blocks,
    )


def _seed_healthy_csr(csr: ConstitutionalStateRuntime) -> None:
    csr.register_or_replace_state(
        StateObject(state_id="task-1", state_type="operator_task", current_state="Evaluated")
    )
    csr.register_invariant("workspace_integrity", "Paths stay inside workspace jail")
    csr.append_observation_receipt(_decision())


def test_fitness_runtime_charter_resists_all_surfaces() -> None:
    assert len(ReconstructabilityFitnessRuntime.resists) == 10
    assert RUNTIME_CHARTER["ReconstructabilityFitnessRuntime"] == list(RF)


def test_rf1_evidence_loss_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    bad = _decision(
        evidence=EvidenceBundleV2(
            bundle_id="",
            sufficiency=EvidenceSufficiencyV2(
                continuity=False,
                truth=False,
                sovereignty=False,
                institutional=False,
            ),
        )
    )
    csr.append_observation_receipt(bad)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.EVIDENCE_LOSS in state.failed_surfaces


def test_rf2_state_loss_detected() -> None:
    csr = ConstitutionalStateRuntime()
    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.STATE_LOSS in state.failed_surfaces
    assert "no_states_present" in state.missing_artifacts


def test_rf3_lineage_break_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    amendment = AmendmentEvaluationReceiptV2(
        receipt_id=new_receipt_id("amend-eval"),
        runtime="constitutional",
        timestamp="2026-06-23T12:00:00Z",
        amendment=AmendmentPayloadV2(
            article="XVII",
            change_type="addition",
            justification="new article",
            trigger_receipt_id="trg-1",
            amendment_stage="evaluated",
        ),
        **_base_blocks(lifecycle_stage="decision"),
    )
    csr.append_observation_receipt(amendment)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.LINEAGE_BREAK in state.failed_surfaces
    assert "no_amendment_supersession_links" in state.missing_lineage_links


def test_rf4_authority_opacity_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    bad = _decision(
        authority=AuthorityBlockV2(source="", jurisdiction="workspace", legitimacy_basis=""),
    )
    csr.append_observation_receipt(bad)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.AUTHORITY_OPACITY in state.failed_surfaces


def test_rf5_accountability_erosion_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    bad = _decision(
        accountability=AccountabilityBlockV2(primary_accountable_party=""),
    )
    csr.append_observation_receipt(bad)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.ACCOUNTABILITY_EROSION in state.failed_surfaces


def test_rf6_remediation_amnesia_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    divergence = DivergenceReceiptV2(
        receipt_id=new_receipt_id("div"),
        runtime="reality",
        timestamp="2026-06-23T12:01:00Z",
        action_type="divergence_record",
        divergence=DivergencePayloadV2(nature="outcome_mismatch", magnitude="high"),
        **_base_blocks(lifecycle_stage="divergence"),
    )
    csr.append_observation_receipt(divergence)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.REMEDIATION_AMNESIA in state.failed_surfaces


def test_rf7_learning_amnesia_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    implemented = AmendmentImplementationReceiptV2(
        receipt_id=new_receipt_id("amend-impl"),
        runtime="constitutional",
        timestamp="2026-06-23T12:02:00Z",
        amendment=AmendmentPayloadV2(
            article="XVII",
            change_type="addition",
            justification="implemented",
            trigger_receipt_id="trg-1",
            amendment_stage="implemented",
        ),
        **_base_blocks(lifecycle_stage="decision"),
    )
    csr.append_observation_receipt(implemented)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.LEARNING_AMNESIA in state.failed_surfaces


def test_rf8_steward_discontinuity_detected() -> None:
    csr = ConstitutionalStateRuntime()
    csr.register_or_replace_state(
        StateObject(state_id="task-1", state_type="operator_task", current_state="Evaluated")
    )
    bad = _decision(
        invariant=InvariantBlockV2(name="", description="", satisfied=False),
        authority=AuthorityBlockV2(source="", jurisdiction="workspace", legitimacy_basis=""),
        evidence=EvidenceBundleV2(
            bundle_id="",
            sufficiency=EvidenceSufficiencyV2(
                continuity=False,
                truth=False,
                sovereignty=False,
                institutional=False,
            ),
        ),
    )
    csr.append_observation_receipt(bad)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.STEWARD_DISCONTINUITY in state.failed_surfaces
    assert state.implicit_assumptions_required > 0


def test_rf9_semantic_drift_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    csr.register_invariant("workspace_integrity", "registered meaning")
    drift = _decision(
        invariant=InvariantBlockV2(
            name="unknown_invariant",
            description="not in registry",
            satisfied=True,
        )
    )
    csr.append_observation_receipt(drift)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.SEMANTIC_DRIFT in state.failed_surfaces


def test_rf10_boundary_confusion_detected() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    bad = _decision(
        impact_boundary=ImpactBoundaryV2(scope_in=["workspace"], scope_out=[]),
    )
    csr.append_observation_receipt(bad)

    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert RF.BOUNDARY_CONFUSION in state.failed_surfaces


def test_healthy_audit_passes_all_surfaces() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    state = ReconstructabilityFitnessRuntime(csr).run_audit()
    assert state.failed_surfaces == []
    assert state.fitness_score == 1.0
    assert state.stewardship_readiness_score == 1.0


def test_fitness_receipt_emitted_on_audit() -> None:
    csr = ConstitutionalStateRuntime()
    _seed_healthy_csr(csr)
    ReconstructabilityFitnessRuntime(csr).run_audit()
    receipts = csr.domain_receipts_for("reconstructability_fitness__global")
    assert len(receipts) == 1
    assert receipts[0].action_type == "reconstructability_fitness_audit"
