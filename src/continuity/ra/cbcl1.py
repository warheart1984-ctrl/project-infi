"""CBCL-1 — Consequence-Based Continuity Ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.ra.models import DriftSignals, LedgerEntry, RAState, ValidationResult
from src.continuity.ra.spec import CBCL1_REFERENCE
from src.continuity.ra.vas1 import VAS1Result

CBCLReviewStatus = Literal["Validated", "Rejected", "Under Review"]


class CBCL1Entry(BaseModel):
    """External memory of how accepted improvements perform in reality."""

    reference: str = CBCL1_REFERENCE
    improvement_id: str
    surpassment_evidence: str = ""
    acceptance_evidence: str = ""
    validation_results: VAS1Result | None = None
    operational_outcomes: list[str] = Field(default_factory=list)
    predictive_performance: float | None = None
    cross_domain_signals: list[str] = Field(default_factory=list)
    reconstructability_impact: float = 0.0
    steward_load_impact: float = 0.0
    drift_signals: DriftSignals | None = None
    review_status: CBCLReviewStatus = "Under Review"
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0))
    notes: list[str] = Field(default_factory=list)


def review_status_from_ledger(
    final_status: str,
    validation_result: ValidationResult,
    *,
    psd_flagged: bool = False,
) -> CBCLReviewStatus:
    if final_status == "VALIDATED" and validation_result == "PASSED":
        return "Validated"
    if final_status in ("REJECTED", "ROLLED_BACK") or validation_result == "FAILED":
        return "Rejected"
    if psd_flagged or final_status == "PROVISIONAL":
        return "Under Review"
    return "Under Review"


def ledger_entry_to_cbcl(entry: LedgerEntry, change_id: str) -> CBCL1Entry:
    psd_flagged = False
    if entry.drift_signals is not None:
        psd_flagged = entry.drift_signals.aggregate_psd >= 0.6

    validation_results = None
    if entry.validation_result != "PENDING":
        validation_results = VAS1Result(
            passed=entry.validation_result == "PASSED",
            criteria_passed=[] if entry.validation_result == "FAILED" else ["ledger-record"],
            criteria_failed=[] if entry.validation_result == "PASSED" else ["ledger-record"],
            reality_veto=entry.validation_result == "FAILED",
        )

    return CBCL1Entry(
        improvement_id=change_id,
        surpassment_evidence=entry.surpassment_evidence,
        acceptance_evidence=entry.acceptance_evidence,
        validation_results=validation_results,
        operational_outcomes=[
            note for note in entry.notes if "operational" in note.lower()
        ],
        predictive_performance=entry.predictive_performance,
        cross_domain_signals=list(entry.cross_domain_signals),
        reconstructability_impact=entry.reconstructability_impact,
        steward_load_impact=entry.steward_load_impact,
        drift_signals=entry.drift_signals,
        review_status=review_status_from_ledger(
            entry.final_status,
            entry.validation_result,
            psd_flagged=psd_flagged,
        ),
        notes=list(entry.notes),
    )


def get_cbcl_ledger(state: RAState) -> list[CBCL1Entry]:
    """Return the full consequence-based continuity ledger."""
    return [
        ledger_entry_to_cbcl(entry, change_id)
        for change_id, entry in state.ledger.items()
    ]


def update_ledger_from_validation(
    entry: LedgerEntry,
    *,
    vas1: VAS1Result,
    predictive_performance: float | None = None,
    cross_domain_signals: list[str] | None = None,
    reconstructability_impact: float = 0.0,
    steward_load_impact: float = 0.0,
    operational_outcomes: list[str] | None = None,
) -> LedgerEntry:
    return entry.model_copy(
        update={
            "validation_result": "PASSED" if vas1.passed else "FAILED",
            "predictive_performance": predictive_performance,
            "cross_domain_signals": cross_domain_signals or [],
            "reconstructability_impact": reconstructability_impact,
            "steward_load_impact": steward_load_impact,
            "operational_outcomes": operational_outcomes or [],
        }
    )
