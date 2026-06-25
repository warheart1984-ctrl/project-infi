"""Observer Verification Handbook — independent verification procedure."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from constitutional.runtime.amendments import AmendmentState, replay_amendment
from constitutional.runtime.constitutional_state import StateObject, replay_state
from constitutional.runtime.receipts_v2 import (
    AmendmentReceiptV2,
    BaseReceiptV2,
    ObserverAccountabilitySummaryV2,
    ObserverClosurePayloadV2,
    ObserverClosureReceiptV2,
    ObserverDivergencePayloadV2,
    ObserverDivergenceReceiptV2,
    ObserverRemediationRequestPayloadV2,
    ObserverRemediationRequestReceiptV2,
    ObserverVerificationPayloadV2,
    ObserverVerificationReceiptV2,
    TransitionReceiptV2,
    is_amendment_trigger_receipt,
    is_receipt_v2_complete,
    new_receipt_id,
    utc_now_rfc3339,
)
from constitutional.runtime.transition_ledger import ConstitutionalTransitionLedger


class ObserverVerificationContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    target_id: str
    receipts: list[BaseReceiptV2] = Field(default_factory=list)
    transition_receipts: list[TransitionReceiptV2] = Field(default_factory=list)
    amendment_receipts: list[AmendmentReceiptV2] = Field(default_factory=list)
    canonical_state: StateObject | None = None
    amendment_state: AmendmentState | None = None
    trigger_receipt: BaseReceiptV2 | None = None
    ledger: ConstitutionalTransitionLedger | None = None
    responsible_parties: list[str] = Field(default_factory=list)


class ObserverVerificationReport(BaseModel):
    verification: ObserverVerificationPayloadV2
    failures: list[str] = Field(default_factory=list)
    verification_receipt: ObserverVerificationReceiptV2 | None = None
    divergence_receipt: ObserverDivergenceReceiptV2 | None = None
    remediation_request_receipt: ObserverRemediationRequestReceiptV2 | None = None
    closure_receipt: ObserverClosureReceiptV2 | None = None


def _base_observer_receipt_fields() -> dict:
    return {
        "inputs": {"request_id": new_receipt_id("obs-req"), "payload_hash": "sha256:observer"},
        "outputs": {"status": "completed", "result_hash": "sha256:observer"},
        "invariant": {
            "name": "independent_verification",
            "description": "Observer may verify without runtime authority",
            "satisfied": True,
        },
        "evidence": {
            "bundle_id": "observer-bundle",
            "sources": [],
            "modalities": ["inspection"],
            "chain_of_custody": [],
            "sufficiency": {
                "continuity": True,
                "truth": True,
                "sovereignty": True,
                "institutional": True,
            },
        },
        "authority": {
            "source": "observer",
            "jurisdiction": "external",
            "delegation_chain": [],
            "legitimacy_basis": "Article XVI Observer Handbook",
        },
        "reproducibility": {
            "is_reproducible": True,
            "mode": "exact",
        },
        "impact_boundary": {
            "scope_in": ["verification"],
            "scope_out": ["execution"],
        },
        "accountability": {
            "primary_accountable_party": "observer",
            "accountability_chain": [],
        },
        "signatures": {"runtime_signature": "observer"},
        "continuity": {"lineage_hash": "sha256:observer"},
        "lifecycle": {
            "stage": "decision",
            "previous_stage_receipt_id": None,
            "next_stage_expected": None,
        },
    }


def run_observer_verification(ctx: ObserverVerificationContext) -> ObserverVerificationReport:
    """Execute the 8-step observer verification procedure."""
    failures: list[str] = []

    # Step 1 — receipts collected (caller provides)
    if not ctx.receipts and not ctx.transition_receipts:
        failures.append("no receipts supplied")

    # Step 2 — Six-Dimension Contract
    for receipt in ctx.receipts:
        if not is_receipt_v2_complete(receipt):
            failures.append(f"incomplete receipt: {receipt.receipt_id}")

    # Step 3 — transition legality via ledger
    state_reconstructed = False
    state_replayed = False
    divergence_detected = False
    if ctx.ledger is not None:
        ledger_failures = ctx.ledger.detect_failures()
        for lf in ledger_failures:
            failures.append(f"{lf.code}: {lf.message}")
        divergence_detected = any(f.code in {"illegal_transition", "broken_lineage"} for f in ledger_failures)

    # Step 4–5 — reconstruct + replay state
    if ctx.canonical_state is not None and ctx.transition_receipts:
        replay = replay_state(ctx.transition_receipts, ctx.canonical_state)
        state_reconstructed = True
        state_replayed = True
        if replay.diverged:
            divergence_detected = True
            failures.append("state replay diverged")

    # Step 6 — remediation lifecycle (presence of closure when divergence flagged)
    remediation_valid = not divergence_detected or any(
        r.lifecycle.stage == "closure" for r in ctx.receipts if hasattr(r, "lifecycle")
    )

    # Step 7 — amendment path
    amendments_valid = True
    if ctx.amendment_receipts and ctx.trigger_receipt and ctx.amendment_state:
        if not is_amendment_trigger_receipt(ctx.trigger_receipt):
            amendments_valid = False
            failures.append("amendment without lawful trigger receipt")
        else:
            replay = replay_amendment(
                ctx.trigger_receipt,
                ctx.amendment_receipts,
                ctx.amendment_state,
            )
            if replay.diverged:
                amendments_valid = False
                failures.append("amendment replay diverged")

    verification = ObserverVerificationPayloadV2(
        state_reconstructed=state_reconstructed,
        state_replayed=state_replayed,
        divergence_detected=divergence_detected,
        remediation_valid=remediation_valid,
        amendments_valid=amendments_valid,
        target_id=ctx.target_id,
    )

    report = ObserverVerificationReport(verification=verification, failures=failures)

    if failures:
        report.divergence_receipt = ObserverDivergenceReceiptV2(
            receipt_id=new_receipt_id("observer-divergence"),
            runtime="observer",
            timestamp=utc_now_rfc3339(),
            action_type="observer_divergence",
            observer_divergence=ObserverDivergencePayloadV2(
                divergence_points=failures,
                target_receipt_ids=[r.receipt_id for r in ctx.receipts[:5]],
                rationale="Observer verification failed",
            ),
            **_base_observer_receipt_fields(),
        )
        report.remediation_request_receipt = ObserverRemediationRequestReceiptV2(
            receipt_id=new_receipt_id("observer-remediation"),
            runtime="observer",
            timestamp=utc_now_rfc3339(),
            action_type="observer_remediation_request",
            observer_remediation_request=ObserverRemediationRequestPayloadV2(
                requested_actions=["investigate failures", "issue remediation receipts"],
                responsible_party=ctx.responsible_parties[0] if ctx.responsible_parties else "operator",
                trigger_receipt_id=report.divergence_receipt.receipt_id,
            ),
            **_base_observer_receipt_fields(),
        )
        return report

    # Step 8 — observer verification receipt
    report.verification_receipt = ObserverVerificationReceiptV2(
        receipt_id=new_receipt_id("observer-verify"),
        runtime="observer",
        timestamp=utc_now_rfc3339(),
        action_type="observer_verification",
        verification=verification,
        observer_accountability=ObserverAccountabilitySummaryV2(
            responsible_parties=list(ctx.responsible_parties),
        ),
        **_base_observer_receipt_fields(),
    )
    report.closure_receipt = ObserverClosureReceiptV2(
        receipt_id=new_receipt_id("observer-closure"),
        runtime="observer",
        timestamp=utc_now_rfc3339(),
        action_type="observer_closure",
        observer_closure=ObserverClosurePayloadV2(
            verification_receipt_id=report.verification_receipt.receipt_id,
            closed=True,
        ),
        **_base_observer_receipt_fields(),
    )
    return report
