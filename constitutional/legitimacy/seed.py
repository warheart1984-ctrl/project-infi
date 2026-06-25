"""Seed helpers for Stewardship Legitimacy Protocol v1.0."""

from __future__ import annotations

from constitutional.eck2 import ECK2Runtime
from constitutional.jpss import canonical_passing_responses
from constitutional.legitimacy.jpss_c_exam import canonical_passing_constitutional_responses, run_jpss_c_exam
from constitutional.legitimacy.legitimacy_criterion import (
    passing_reconstruction_demonstration,
    record_reconstruction_demonstration,
)
from constitutional.legitimacy.legitimacy_exam import run_legitimacy_exam
from constitutional.legitimacy.legitimacy_process import default_process_input, run_legitimacy_process
from constitutional.legitimacy.legitimacy_register import certify_steward
from constitutional.runtime.runtime import ConstitutionalStateRuntime


def _steward_inputs(steward_id: str, decision_id: str) -> dict:
    return {
        "decision_id": decision_id,
        "steward_id": steward_id,
        "available_signals": ["fitness", "continuity"],
        "expected_signals": ["reconstructability"],
        "constraints_active": ["article_r"],
        "environmental_factors": ["succession_pressure"],
        "outcome": "observe",
        "rationale": "Legitimacy Protocol v1.0 certification stack.",
        "expected_result": "observe",
        "success": True,
        "invariant_defaults": {
            "purpose_clauses": ["preserve constitutional continuity"],
            "core_values": ["non-derogable"],
            "commitments": ["succession gate required"],
            "identity_markers": ["eck-2 dual pipeline"],
            "sacred_constraints": ["never bypass succession gate"],
        },
        "stewardship_responses": canonical_passing_responses(),
    }


def _certify_one(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
    ratifiers: list[str],
) -> None:
    ECK2Runtime(csr).run(_steward_inputs(steward_id, f"leg-{steward_id}"))
    run_jpss_c_exam(csr, steward_id, canonical_passing_constitutional_responses())
    record_reconstruction_demonstration(csr, passing_reconstruction_demonstration(steward_id))
    exam = run_legitimacy_exam(csr, steward_id)
    process = run_legitimacy_process(csr, default_process_input(steward_id, ratifiers))
    certify_steward(
        csr,
        steward_id=steward_id,
        certified_by=ratifiers,
        exam_passed=exam.passed,
        process_passed=process.passed,
        legitimacy_index=exam.legitimacy_index,
        receipt_refs=[
            "eck2_pipeline",
            "invariant_register",
            "legitimacy_receipts",
            "legitimacy_ratification",
        ],
    )


def seed_stewardship_legitimacy(
    csr: ConstitutionalStateRuntime,
    *,
    primary_steward_id: str = "steward-a",
    secondary_steward_id: str = "steward-b",
    certifier_cohort: list[str] | None = None,
) -> None:
    """Run full Protocol v1.0 stack and certify a plural steward cohort."""
    cohort = certifier_cohort or ["steward-founder", "steward-legacy"]
    _certify_one(csr, primary_steward_id, cohort + [secondary_steward_id])
    _certify_one(csr, secondary_steward_id, cohort + [primary_steward_id])
