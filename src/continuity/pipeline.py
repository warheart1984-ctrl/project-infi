"""Continuity proof pipeline: Discovery → Evidence → Evaluation → CT → Proof → CVR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.continuity.ccs import CCSStore, ContinuityTrace, trace_from_object
from src.continuity.pod import PODDecision
from src.continuity.proof import Proof, ProofStatus, create_proof, valid_proof
from src.continuity.reputation import ContinuityValidatedReputation, compute_cvr
from src.continuity.substrate import ContinuitySubstrate, bind_pod_decision, substrate_from_store, validate_substrate
from src.continuity.ugr_trace import evaluate_trace_ugr_invariants, valid_continuity_trace

PipelineStage = str


STAGE_DISCOVERY = "discovery"
STAGE_EVIDENCE = "evidence"
STAGE_EVALUATION = "evaluation"
STAGE_CONTINUITY_TRACE = "continuity_trace"
STAGE_PROOF = "proof"
STAGE_CVR = "cvr"

PIPELINE_STAGES = (
    STAGE_DISCOVERY,
    STAGE_EVIDENCE,
    STAGE_EVALUATION,
    STAGE_CONTINUITY_TRACE,
    STAGE_PROOF,
    STAGE_CVR,
)


@dataclass
class PipelineStageResult:
    stage: PipelineStage
    ugr_invariants: dict[str, dict[str, str]] = field(default_factory=dict)
    passed: bool = True
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "ugr_invariants": dict(self.ugr_invariants),
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass
class PipelineResult:
    subject_ref: str
    stages: list[PipelineStageResult] = field(default_factory=list)
    trace: ContinuityTrace | None = None
    proof: Proof | None = None
    cvr: ContinuityValidatedReputation | None = None
    substrate: ContinuitySubstrate | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_ref": self.subject_ref,
            "stages": [stage.to_dict() for stage in self.stages],
            "trace_id": self.trace.id if self.trace else None,
            "proof_id": self.proof.proof_id if self.proof else None,
            "cvr_id": self.cvr.cvr_id if self.cvr else None,
            "substrate_id": self.substrate.substrate_id if self.substrate else None,
        }


def _stage_ugr_for_store(store: CCSStore, trace: ContinuityTrace | None) -> dict[str, dict[str, str]]:
    if trace is None:
        return {}
    return evaluate_trace_ugr_invariants(store, trace)


def run_proof_pipeline(
    *,
    store: CCSStore,
    subject_ref: str,
    trace: ContinuityTrace,
    decision: PODDecision | None = None,
    subject_id: str | None = None,
    domains: list[str] | None = None,
) -> PipelineResult:
    """
    Execute Discovery → Evidence → Evaluation → ContinuityTrace → Proof → CVR.

    UGR checks attach at each stage; ContinuityTrace validity gates Proof;
    Proof basis feeds CVR recomputation.
    """
    result = PipelineResult(subject_ref=subject_ref)
    if trace.id not in store.traces:
        store.add_trace(trace)

    # Discovery — subject and trace scope present
    discovery_ok = bool(subject_ref) and bool(trace.scope.get("event_ids"))
    result.stages.append(
        PipelineStageResult(
            stage=STAGE_DISCOVERY,
            passed=discovery_ok,
            detail="subject and trace scope resolved" if discovery_ok else "missing subject or scope",
        )
    )

    # Evidence — all timeline evidence hash-stable and linked
    evidence_report = _stage_ugr_for_store(store, trace)
    evidence_ok = evidence_report.get("ugr.evidence_integrity", {}).get("status") == "pass"
    result.stages.append(
        PipelineStageResult(
            stage=STAGE_EVIDENCE,
            ugr_invariants={"ugr.evidence_integrity": evidence_report.get("ugr.evidence_integrity", {})},
            passed=evidence_ok,
            detail="evidence integrity satisfied" if evidence_ok else "evidence integrity failed",
        )
    )

    # Evaluation — authority chain on evaluations
    authority_report = _stage_ugr_for_store(store, trace)
    eval_ok = authority_report.get("ugr.authority_continuity", {}).get("status") == "pass"
    result.stages.append(
        PipelineStageResult(
            stage=STAGE_EVALUATION,
            ugr_invariants={"ugr.authority_continuity": authority_report.get("ugr.authority_continuity", {})},
            passed=eval_ok,
            detail="evaluation authority resolved" if eval_ok else "evaluation authority failed",
        )
    )

    # ContinuityTrace — full UGR validity
    trace_report = evaluate_trace_ugr_invariants(store, trace)
    trace_ok = valid_continuity_trace(store, trace)
    result.stages.append(
        PipelineStageResult(
            stage=STAGE_CONTINUITY_TRACE,
            ugr_invariants=trace_report,
            passed=trace_ok,
            detail="continuity trace valid" if trace_ok else "continuity trace invalid",
        )
    )
    result.trace = trace

    # Proof — Valid(Proof) ⇔ Valid(CT)
    proof = create_proof(store=store, subject_ref=subject_ref, trace=trace)
    proof_ok, proof_detail = valid_proof(store, proof)
    if proof_ok and proof.status != ProofStatus.PROVEN:
        proof.status = ProofStatus.PROVEN
    result.stages.append(
        PipelineStageResult(
            stage=STAGE_PROOF,
            ugr_invariants=proof.continuity_invariants,
            passed=proof_ok,
            detail=str(proof_detail.get("reason", "")),
        )
    )
    result.proof = proof

    # CVR — continuity-validated reputation from proof basis
    cvr_subject = subject_id or subject_ref
    cvr = compute_cvr(
        store=store,
        subject_id=cvr_subject,
        proofs=[proof] if proof_ok else [],
        domains=domains,
    )
    cvr_ok = cvr.derived_score > 0.0 if proof_ok else cvr.derived_score == 0.0
    result.stages.append(
        PipelineStageResult(
            stage=STAGE_CVR,
            passed=cvr_ok,
            detail=f"derived_score={cvr.derived_score}",
        )
    )
    result.cvr = cvr

    substrate = substrate_from_store(store, substrate_id=f"substrate:{trace.id}")
    if decision is not None:
        first_event = trace.scope.get("event_ids", [""])[0]
        first_eval = ""
        if trace.timeline:
            evals = trace.timeline[0].get("evaluations", [])
            first_eval = evals[0] if evals else ""
        evidence_ids = trace.timeline[0].get("evidence", []) if trace.timeline else []
        bind_pod_decision(
            substrate,
            decision,
            event_id=first_event,
            evaluation_id=first_eval or None,
            evidence_ids=evidence_ids or None,
            trace=trace,
        )
    validate_substrate(store, substrate)
    result.substrate = substrate

    return result


def load_trace_from_scenario(scenario: dict[str, Any]) -> ContinuityTrace:
    return trace_from_object(scenario["trace"])
