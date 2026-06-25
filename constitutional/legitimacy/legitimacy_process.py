"""Legitimacy Process — five-phase public certification (Protocol §2)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.legitimacy.legitimacy_criterion import (
    load_legitimacy_criterion_result,
    load_reconstruction_demonstration,
)
from constitutional.legitimacy.legitimacy_exam import StewardshipLegitimacyExam
from constitutional.legitimacy.legitimacy_receipts import (
    LegitimacyReceiptBundle,
    build_receipt_bundle_from_evidence,
    load_legitimacy_receipts,
    record_legitimacy_receipts,
)
from constitutional.legitimacy.spec import LEGITIMACY_PROCESS_PHASES, LegitimacyProcessPhase
from constitutional.runtime.runtime import ConstitutionalStateRuntime

LEGITIMACY_PROCESS_STATE_ID = "legitimacy_process__latest"


class PhaseOutcome(BaseModel):
    phase: LegitimacyProcessPhase
    passed: bool
    notes: list[str] = Field(default_factory=list)


class LegitimacyRatificationRecord(BaseModel):
    candidate_id: str
    ratified_at: datetime
    ratified_by: list[str] = Field(default_factory=list)
    plural: bool = False
    capture_detected: bool = False
    rationale: str = ""


class LegitimacyProcessResult(BaseModel):
    candidate_id: str
    completed_at: datetime
    passed: bool
    phases: list[PhaseOutcome] = Field(default_factory=list)
    ratification: LegitimacyRatificationRecord | None = None
    receipt_bundle: LegitimacyReceiptBundle | None = None
    blockers: list[str] = Field(default_factory=list)


class InterrogationChallenge(BaseModel):
    challenger_id: str
    challenge: str
    addressed: bool = True


class RedTeamFinding(BaseModel):
    tester_id: str
    finding: str
    withstood: bool = True


class LegitimacyProcessInput(BaseModel):
    candidate_id: str
    ratifiers: list[str] = Field(default_factory=list)
    interrogation_challenges: list[InterrogationChallenge] = Field(default_factory=list)
    red_team_findings: list[RedTeamFinding] = Field(default_factory=list)
    approval_rationale: str = "Ratified by prior cohort using Protocol v1.0."
    stewardship_reflection: str = ""


class StewardshipLegitimacyProcess:
    """Run the five-phase legitimacy process for a candidate steward."""

    def run(
        self,
        csr: ConstitutionalStateRuntime,
        process_input: LegitimacyProcessInput,
    ) -> LegitimacyProcessResult:
        now = datetime.now(UTC).replace(microsecond=0)
        candidate = process_input.candidate_id
        phases: list[PhaseOutcome] = []
        blockers: list[str] = []

        demo = load_reconstruction_demonstration(csr, candidate)
        criterion = load_legitimacy_criterion_result(csr, candidate)
        exam = StewardshipLegitimacyExam().evaluate(csr, candidate)
        demo_passed = demo is not None and criterion is not None and criterion.passed
        phases.append(
            PhaseOutcome(
                phase="demonstration",
                passed=demo_passed and exam.passed,
                notes=[] if demo_passed and exam.passed else ["Demonstration or exam incomplete."],
            )
        )
        if not (demo_passed and exam.passed):
            blockers.append("Phase 1 (Demonstration) failed.")

        unaddressed = [c.challenge for c in process_input.interrogation_challenges if not c.addressed]
        interrogation_passed = not unaddressed
        phases.append(
            PhaseOutcome(
                phase="interrogation",
                passed=interrogation_passed,
                notes=unaddressed or ["Interrogation challenges addressed."],
            )
        )
        if not interrogation_passed:
            blockers.append("Phase 2 (Interrogation) failed.")

        failed_stress = [f.finding for f in process_input.red_team_findings if not f.withstood]
        red_team_passed = not failed_stress
        phases.append(
            PhaseOutcome(
                phase="red_team",
                passed=red_team_passed,
                notes=failed_stress or ["Red team stress tests withstood."],
            )
        )
        if not red_team_passed:
            blockers.append("Phase 3 (Red Team) failed.")

        evidence_refs = demo.evidence_refs if demo else []
        bundle = build_receipt_bundle_from_evidence(
            candidate,
            evidence_refs=evidence_refs,
            approval_rationale=process_input.approval_rationale,
            reflection=process_input.stewardship_reflection,
        )
        record_legitimacy_receipts(csr, bundle)
        receipts_passed = bundle.complete
        phases.append(
            PhaseOutcome(
                phase="receipts",
                passed=receipts_passed,
                notes=[] if receipts_passed else ["Receipt bundle incomplete."],
            )
        )
        if not receipts_passed:
            blockers.append("Phase 4 (Receipts) failed.")

        ratifiers = list(dict.fromkeys(process_input.ratifiers))
        capture_detected = len(ratifiers) == 1 and ratifiers[0] in {"founder", "steward-founder"}
        plural = len(ratifiers) >= 2
        ratification_passed = (
            plural
            and not capture_detected
            and all(p.passed for p in phases[:4])
        )
        ratification = LegitimacyRatificationRecord(
            candidate_id=candidate,
            ratified_at=now,
            ratified_by=ratifiers,
            plural=plural,
            capture_detected=capture_detected,
            rationale=process_input.approval_rationale,
        )
        phases.append(
            PhaseOutcome(
                phase="ratification",
                passed=ratification_passed,
                notes=[] if ratification_passed else ["Ratification requires plural, capture-free approval."],
            )
        )
        if not ratification_passed:
            blockers.append("Phase 5 (Ratification) failed.")

        passed = all(p.passed for p in phases)
        result = LegitimacyProcessResult(
            candidate_id=candidate,
            completed_at=now,
            passed=passed,
            phases=phases,
            ratification=ratification if ratification_passed else ratification,
            receipt_bundle=bundle,
            blockers=blockers,
        )
        csr.put_domain_doc(
            f"{LEGITIMACY_PROCESS_STATE_ID}__{candidate}",
            "legitimacy_process_result",
            result,
        )
        if ratification_passed:
            csr.put_domain_doc(
                f"legitimacy_ratification__{candidate}",
                "legitimacy_ratification",
                ratification,
            )
        return result


def run_legitimacy_process(
    csr: ConstitutionalStateRuntime,
    process_input: LegitimacyProcessInput,
) -> LegitimacyProcessResult:
    return StewardshipLegitimacyProcess().run(csr, process_input)


def load_legitimacy_process_result(
    csr: ConstitutionalStateRuntime,
    candidate_id: str,
) -> LegitimacyProcessResult | None:
    try:
        doc = csr.get_domain_doc(
            f"{LEGITIMACY_PROCESS_STATE_ID}__{candidate_id}",
            LegitimacyProcessResult,
        )
        assert isinstance(doc, LegitimacyProcessResult)
        return doc
    except KeyError:
        return None


def load_legitimacy_ratification(
    csr: ConstitutionalStateRuntime,
    candidate_id: str,
) -> LegitimacyRatificationRecord | None:
    try:
        doc = csr.get_domain_doc(f"legitimacy_ratification__{candidate_id}", LegitimacyRatificationRecord)
        assert isinstance(doc, LegitimacyRatificationRecord)
        return doc
    except KeyError:
        return None


def default_process_input(
    candidate_id: str,
    ratifiers: list[str],
) -> LegitimacyProcessInput:
    """Reference process input with passing interrogation and red-team defaults."""
    return LegitimacyProcessInput(
        candidate_id=candidate_id,
        ratifiers=ratifiers,
        interrogation_challenges=[
            InterrogationChallenge(
                challenger_id=ratifiers[0] if ratifiers else "cohort",
                challenge="Verify purpose reconstruction against founding intent.",
                addressed=True,
            ),
        ],
        red_team_findings=[
            RedTeamFinding(
                tester_id=ratifiers[-1] if ratifiers else "red-team",
                finding="Test for over-sacralization of adaptive signals.",
                withstood=True,
            ),
        ],
    )
