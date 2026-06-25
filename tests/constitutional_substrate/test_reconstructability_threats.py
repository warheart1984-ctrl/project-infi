"""Reconstructability failure taxonomy (R-F1 … R-F10)."""

from __future__ import annotations

from constitutional.runtime import (
    ConstitutionalDebtState,
    ReconstructabilityFailureClass,
    compute_constitutional_debt_threats,
    compute_personal_debt_threats,
)
from constitutional.runtime.burnout_runtime import BurnoutRuntime
from constitutional.runtime.personal_continuity_runtime import PersonalContinuityRuntime
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER, charter_for
from constitutional.runtime.receipts_v2 import BaseReceiptV2


def test_all_rf_classes_exist() -> None:
    assert len(ReconstructabilityFailureClass) == 10
    assert ReconstructabilityFailureClass.EVIDENCE_LOSS.value == "R-F1 EvidenceLoss"


def test_constitutional_debt_threat_mapping() -> None:
    threats = compute_constitutional_debt_threats(
        missing_receipts=2,
        unresolved_divergences=1,
        overdue_remediations=1,
    )
    assert ReconstructabilityFailureClass.EVIDENCE_LOSS in threats
    assert ReconstructabilityFailureClass.LINEAGE_BREAK in threats
    assert ReconstructabilityFailureClass.REMEDIATION_AMNESIA in threats


def test_personal_debt_threat_mapping() -> None:
    threats = compute_personal_debt_threats(unexternalized_ideas=1, burnout_warnings=1)
    assert ReconstructabilityFailureClass.STEWARD_DISCONTINUITY in threats
    assert ReconstructabilityFailureClass.EVIDENCE_LOSS in threats


def test_runtime_charters_declared() -> None:
    assert charter_for("TruthRuntime") == [
        ReconstructabilityFailureClass.EVIDENCE_LOSS,
        ReconstructabilityFailureClass.SEMANTIC_DRIFT,
    ]
    assert PersonalContinuityRuntime.resists == RUNTIME_CHARTER["PersonalContinuityRuntime"]
    assert BurnoutRuntime.resists == RUNTIME_CHARTER["BurnoutRuntime"]


def test_base_receipt_accepts_threats() -> None:
    receipt = BaseReceiptV2.model_validate(
        {
            "receipt_id": "r1",
            "runtime": "TruthRuntime",
            "timestamp": "2026-06-23T12:00:00Z",
            "action_type": "divergence",
            "threats": [
                ReconstructabilityFailureClass.EVIDENCE_LOSS,
                ReconstructabilityFailureClass.SEMANTIC_DRIFT,
            ],
            "inputs": {
                "request_id": "x",
                "payload_hash": "sha256:abc",
                "context": {},
            },
            "outputs": {"status": "Divergence", "result_hash": "sha256:abc"},
            "invariant": {"name": "t", "description": "d", "satisfied": True},
            "evidence": {
                "bundle_id": "b",
                "sufficiency": {
                    "continuity": True,
                    "truth": True,
                    "sovereignty": True,
                    "institutional": True,
                },
            },
            "authority": {
                "source": "TruthRuntime",
                "jurisdiction": "truth",
                "legitimacy_basis": "Article XV",
            },
            "reproducibility": {"is_reproducible": True, "mode": "exact"},
            "impact_boundary": {"scope_in": ["truth"], "scope_out": []},
            "accountability": {"primary_accountable_party": "Architect"},
            "signatures": {"runtime_signature": "sig"},
            "continuity": {"lineage_hash": "sha256:line"},
            "lifecycle": {"stage": "observation"},
        }
    )
    assert len(receipt.threats) == 2


def test_constitutional_debt_state_shape() -> None:
    threats = compute_constitutional_debt_threats(missing_receipts=1)
    state = ConstitutionalDebtState(debt_score=0.2, threats=threats, missing_receipts=1)
    assert state.threats[0] == ReconstructabilityFailureClass.EVIDENCE_LOSS
