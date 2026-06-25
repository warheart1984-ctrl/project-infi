"""Mission Fidelity Test v1 — interactive steward articulation (Article P)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.core.articles import ARTICLE_P_REFERENCE, PURPOSE_CONTINUITY_INVARIANT
from constitutional.core.models import StateObject
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    PurposeContinuityPayloadV2,
    PurposeContinuityReceiptV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

MISSION_FIDELITY_INTERACTIVE_STATE_ID = "mission_fidelity_interactive__global"
MIN_ANSWER_LENGTH = 20

SectionId = Literal[
    "purpose_reconstruction",
    "purpose_interpretation",
    "purpose_alignment",
    "purpose_evolution",
    "purpose_continuity",
]


class MissionFidelityQuestion(BaseModel):
    question_id: str
    section: SectionId
    prompt: str
    pf_surface: str


MISSION_FIDELITY_QUESTIONS: list[MissionFidelityQuestion] = [
    MissionFidelityQuestion(
        question_id="why_exist",
        section="purpose_reconstruction",
        prompt="Why does this system exist?",
        pf_surface="P-F3",
    ),
    MissionFidelityQuestion(
        question_id="protected_invariant",
        section="purpose_reconstruction",
        prompt="What invariant does it protect?",
        pf_surface="P-F2",
    ),
    MissionFidelityQuestion(
        question_id="never_optimize_away",
        section="purpose_reconstruction",
        prompt="What must never be optimized away?",
        pf_surface="P-F1",
    ),
    MissionFidelityQuestion(
        question_id="system_telos",
        section="purpose_reconstruction",
        prompt="What is the system's telos?",
        pf_surface="P-F4",
    ),
    MissionFidelityQuestion(
        question_id="purpose_vs_implementation",
        section="purpose_interpretation",
        prompt="What is the difference between purpose and implementation?",
        pf_surface="P-F7",
    ),
    MissionFidelityQuestion(
        question_id="sacred_parts",
        section="purpose_interpretation",
        prompt="Which parts of the system are sacred?",
        pf_surface="P-F2",
    ),
    MissionFidelityQuestion(
        question_id="replaceable_parts",
        section="purpose_interpretation",
        prompt="Which parts are replaceable?",
        pf_surface="P-F6",
    ),
    MissionFidelityQuestion(
        question_id="decision_alignment",
        section="purpose_alignment",
        prompt="How does this decision align with the founding purpose?",
        pf_surface="P-F1",
    ),
    MissionFidelityQuestion(
        question_id="purpose_drift_definition",
        section="purpose_alignment",
        prompt="What would constitute purpose drift?",
        pf_surface="P-F1",
    ),
    MissionFidelityQuestion(
        question_id="telos_inversion_detection",
        section="purpose_alignment",
        prompt="How would you detect telos inversion?",
        pf_surface="P-F4",
    ),
    MissionFidelityQuestion(
        question_id="evolve_without_losing_self",
        section="purpose_evolution",
        prompt="How should the system evolve without losing itself?",
        pf_surface="P-F9",
    ),
    MissionFidelityQuestion(
        question_id="legitimate_vs_illegitimate_evolution",
        section="purpose_evolution",
        prompt="What is legitimate evolution vs illegitimate drift?",
        pf_surface="P-F1",
    ),
    MissionFidelityQuestion(
        question_id="teach_future_steward",
        section="purpose_continuity",
        prompt="How would you teach the purpose to a future steward?",
        pf_surface="P-F5",
    ),
    MissionFidelityQuestion(
        question_id="cultural_context_required",
        section="purpose_continuity",
        prompt="What cultural context is required to interpret the invariant?",
        pf_surface="P-F5",
    ),
]

QUESTION_BY_ID = {q.question_id: q for q in MISSION_FIDELITY_QUESTIONS}


class StewardAnswer(BaseModel):
    question_id: str
    answer: str
    answered_at: datetime
    steward_id: str = "steward"


class MissionFidelityInteractiveState(BaseModel):
    state_id: str = MISSION_FIDELITY_INTERACTIVE_STATE_ID
    state_type: str = "mission_fidelity_interactive"
    version: int = Field(default=1, ge=1)
    last_submitted_at: datetime | None = None
    steward_id: str = "steward"
    answers: dict[str, StewardAnswer] = Field(default_factory=dict)
    unanswered_pf_threats: list[str] = Field(default_factory=list)
    interactive_passed: bool = False

    def unanswered_question_ids(self) -> list[str]:
        return [
            q.question_id
            for q in MISSION_FIDELITY_QUESTIONS
            if q.question_id not in self.answers
            or len(self.answers[q.question_id].answer.strip()) < MIN_ANSWER_LENGTH
        ]


def load_mission_fidelity_interactive(
    csr: ConstitutionalStateRuntime,
) -> MissionFidelityInteractiveState | None:
    try:
        doc = csr.get_domain_doc(MISSION_FIDELITY_INTERACTIVE_STATE_ID, MissionFidelityInteractiveState)
        assert isinstance(doc, MissionFidelityInteractiveState)
        return doc
    except KeyError:
        return None


def submit_mission_fidelity_answers(
    csr: ConstitutionalStateRuntime,
    answers: dict[str, str],
    *,
    steward_id: str = "steward",
    submitted_at: datetime | None = None,
) -> MissionFidelityInteractiveState:
    """Record steward answers for the interactive Mission Fidelity Test v1."""
    now = submitted_at or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    prev = load_mission_fidelity_interactive(csr)
    version = (prev.version + 1) if prev else 1
    existing = dict(prev.answers) if prev else {}

    merged = dict(existing)
    for question_id, text in answers.items():
        if question_id not in QUESTION_BY_ID:
            continue
        merged[question_id] = StewardAnswer(
            question_id=question_id,
            answer=text.strip(),
            answered_at=now,
            steward_id=steward_id,
        )

    state = MissionFidelityInteractiveState(
        version=version,
        last_submitted_at=now,
        steward_id=steward_id,
        answers=merged,
    )
    state = evaluate_interactive_state(state)
    csr.register_or_replace_state(
        StateObject(
            state_id=MISSION_FIDELITY_INTERACTIVE_STATE_ID,
            state_type="mission_fidelity_interactive",
            current_state="Observed" if state.interactive_passed else "Proposed",
        )
    )
    csr.put_domain_doc(MISSION_FIDELITY_INTERACTIVE_STATE_ID, "mission_fidelity_interactive", state)
    return state


def evaluate_interactive_state(
    state: MissionFidelityInteractiveState,
) -> MissionFidelityInteractiveState:
    unanswered = state.unanswered_question_ids()
    pf_threats = sorted(
        {
            QUESTION_BY_ID[qid].pf_surface
            for qid in unanswered
            if qid in QUESTION_BY_ID
        }
    )
    return state.model_copy(
        update={
            "unanswered_pf_threats": pf_threats,
            "interactive_passed": len(unanswered) == 0,
        }
    )


def build_purpose_continuity_receipt(
    state: MissionFidelityInteractiveState,
    *,
    purpose_interpretation: str = "",
    purpose_justification: str = "",
    purpose_constraints: list[str] | None = None,
    non_negotiables: list[str] | None = None,
    drift_vectors_detected: list[str] | None = None,
    tested_surfaces: list[str] | None = None,
    failed_surfaces: list[str] | None = None,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> PurposeContinuityReceiptV2:
    """Emit a Purpose Continuity Receipt documenting steward articulation."""
    constraints = purpose_constraints or []
    non_negotiables_list = non_negotiables or []
    drift = drift_vectors_detected or list(state.unanswered_pf_threats)
    tested = tested_surfaces or [q.pf_surface for q in MISSION_FIDELITY_QUESTIONS]
    failed = failed_surfaces or list(state.unanswered_pf_threats)
    missing = state.unanswered_question_ids()

    interpretation = purpose_interpretation or _summarize_answers(state, "purpose_reconstruction")
    justification = purpose_justification or _summarize_answers(state, "purpose_continuity")

    ts = (state.last_submitted_at or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")
    payload = PurposeContinuityPayloadV2(
        kind="PurposeContinuity",
        invariant=PURPOSE_CONTINUITY_INVARIANT,
        purpose_interpretation=interpretation,
        purpose_justification=justification,
        purpose_constraints=constraints,
        non_negotiables=non_negotiables_list,
        drift_vectors_detected=drift,
        missing_purpose_artifacts=missing,
        tested_surfaces=tested,
        failed_surfaces=failed,
        timestamp=ts,
    )
    payload_hash = stable_json_hash(payload.model_dump())
    receipt_id = new_receipt_id("pcr")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    threats = [PF.MISSION_AMNESIA] if missing else []
    return PurposeContinuityReceiptV2(
        receipt_id=receipt_id,
        runtime="MissionFidelityInteractiveRuntime",
        timestamp=ts,
        action_type="purpose_continuity",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.steward_id),
        ),
        outputs=ReceiptOutputsV2(
            status="passed" if state.interactive_passed else "failed",
            result_hash=payload_hash,
            notes=f"missing_artifacts={len(missing)}",
        ),
        invariant=InvariantBlockV2(
            name=PURPOSE_CONTINUITY_INVARIANT,
            description="Founding purpose must be preserved and articulable without founder context",
            satisfied=state.interactive_passed,
        ),
        evidence=EvidenceBundleV2(
            bundle_id="constitutional_ledger",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source="MissionFidelityInteractiveRuntime",
            jurisdiction="purpose",
            legitimacy_basis=ARTICLE_P_REFERENCE,
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance", "succession", "amendment_triggers"],
            scope_out=["execution"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party=state.steward_id),
        signatures=SignaturesBlockV2(runtime_signature="sig-pcr-runtime"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            lineage_hash=lineage_hash,
        ),
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=previous_receipt_id,
            next_stage_expected=None,
        ),
        observation=ObservationPayloadV2(
            observed_status="passed" if state.interactive_passed else "failed",
            observed_at=ts,
            observer_jurisdiction="mission_fidelity_interactive",
            notes=f"interactive_passed={state.interactive_passed}",
        ),
        threats=threats,
        purpose_continuity=payload,
    )


def emit_purpose_continuity_receipt(
    csr: ConstitutionalStateRuntime,
    state: MissionFidelityInteractiveState,
) -> PurposeContinuityReceiptV2:
    receipt = build_purpose_continuity_receipt(state)
    csr.append_observation_receipt(receipt)
    return receipt


def _summarize_answers(state: MissionFidelityInteractiveState, section: SectionId) -> str:
    parts: list[str] = []
    for question in MISSION_FIDELITY_QUESTIONS:
        if question.section != section:
            continue
        answer = state.answers.get(question.question_id)
        if answer and len(answer.answer.strip()) >= MIN_ANSWER_LENGTH:
            parts.append(f"{question.prompt} {answer.answer.strip()}")
    return " | ".join(parts) if parts else ""
