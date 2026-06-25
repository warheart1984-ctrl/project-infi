"""Personal Constitutional State v0 — governed builder condition snapshot."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from constitutional.runtime.constitutional_debt import compute_personal_debt_threats
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass
from constitutional.runtime.reconstructability_fitness_runtime import (
    FITNESS_STATE_ID,
    ReconstructabilityFitnessState,
)
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
    ObservationReceiptV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
    utc_now_rfc3339,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

PERSONAL_STATE_ID = "personal_constitutional_state__global"
BURNOUT_LATEST_KEY = "burnout__latest"

Trend = Literal["improving", "stable", "worsening"]


class PersonalConstitutionalState(BaseModel):
    state_id: str = PERSONAL_STATE_ID
    state_type: str = "personal_constitutional_state"
    snapshot_at: datetime
    version: int

    architectural_continuity: float = Field(ge=0.0, le=1.0)
    capacity_continuity: float = Field(ge=0.0, le=1.0)

    unexternalized_ideas: int = Field(ge=0)
    burnout_warnings: int = Field(ge=0)
    debt_score: float = Field(ge=0.0, le=1.0)
    threats: list[ReconstructabilityFailureClass] = Field(default_factory=list)
    trend: Trend

    @model_validator(mode="after")
    def _enforce_pcs_invariants(self) -> PersonalConstitutionalState:
        if self.burnout_warnings > 0 and self.capacity_continuity >= 1.0:
            raise ValueError("PCS-2: capacity_continuity cannot be 1.0 when burnout_warnings > 0")
        if self.unexternalized_ideas > 0 and self.architectural_continuity >= 1.0:
            raise ValueError(
                "PCS-3: architectural_continuity cannot be 1.0 when unexternalized_ideas > 0"
            )
        return self


def burnout_health_score(burnout_state: object) -> float:
    sleep = float(getattr(burnout_state, "sleep_quality", 1.0))
    stress = float(getattr(burnout_state, "stress_level", 0.0))
    cognitive = float(getattr(burnout_state, "cognitive_load", 0.0))
    meetings = float(getattr(burnout_state, "meeting_load", 0.0))
    recovery = float(getattr(burnout_state, "recovery_index", 1.0))
    return max(
        0.0,
        min(
            1.0,
            0.3 * sleep
            + 0.2 * (1.0 - stress)
            + 0.2 * (1.0 - cognitive)
            + 0.1 * (1.0 - meetings)
            + 0.2 * recovery,
        ),
    )


def compute_architectural_continuity(
    foundational: list[object],
    unexternalized: list[object],
) -> float:
    if not foundational:
        return 1.0
    externalized_count = len(foundational) - len(unexternalized)
    return max(0.0, min(1.0, externalized_count / len(foundational)))


def compute_debt_score(unexternalized_count: int, burnout_warnings: int) -> float:
    """PCS-1: deterministic function of underlying counts."""
    idea_component = min(1.0, unexternalized_count / 5.0)
    burnout_component = min(1.0, float(burnout_warnings))
    return max(0.0, min(1.0, 0.5 * idea_component + 0.5 * burnout_component))


def compute_trend(
    debt_score: float,
    previous: PersonalConstitutionalState | None,
) -> Trend:
    if previous is None:
        return "stable"
    if debt_score < previous.debt_score - 0.05:
        return "improving"
    if debt_score > previous.debt_score + 0.05:
        return "worsening"
    return "stable"


def build_personal_observation_receipt(
    state: PersonalConstitutionalState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> ObservationReceiptV2:
    payload = {
        "architectural_continuity": state.architectural_continuity,
        "capacity_continuity": state.capacity_continuity,
        "unexternalized_ideas": state.unexternalized_ideas,
        "burnout_warnings": state.burnout_warnings,
        "debt_score": state.debt_score,
        "threats": [t.value for t in state.threats],
        "trend": state.trend,
        "version": state.version,
    }
    payload_hash = stable_json_hash(payload)
    receipt_id = new_receipt_id("pcs")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return ObservationReceiptV2(
        receipt_id=receipt_id,
        runtime="PersonalConstitutionalStateRuntime",
        timestamp=ts,
        action_type="personal_constitutional_snapshot",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="observed",
            result_hash=payload_hash,
            notes="PersonalConstitutionalState v0 snapshot",
        ),
        invariant=InvariantBlockV2(
            name="BUILDER_CONDITION_MUST_BE_GOVERNED_AND_VISIBLE",
            description="Personal constitutional state is receipted and reproducible",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"pcs-evidence-{state.version}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source="PersonalConstitutionalStateRuntime",
            jurisdiction="personal",
            legitimacy_basis="Article PX-0",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["personal_governance"],
            scope_out=["system_constitutional_state"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="Architect"),
        signatures=SignaturesBlockV2(runtime_signature="sig-pcs-runtime"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            lineage_hash=lineage_hash,
        ),
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=previous_receipt_id,
            next_stage_expected="closure",
        ),
        observation=ObservationPayloadV2(
            observed_status="snapshot",
            observed_at=ts,
            observer_jurisdiction="personal",
            notes=f"PCS v{state.version} debt={state.debt_score:.2f} trend={state.trend}",
        ),
        threats=list(state.threats),
    )


class PersonalConstitutionalStateRuntime:
    """v0: aggregates PersonalContinuityRuntime + BurnoutRuntime into PCS + receipt."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def update_snapshot(
        self,
        snapshot_at: datetime | None = None,
    ) -> PersonalConstitutionalState:
        now = snapshot_at or datetime.now(UTC).replace(microsecond=0)

        ideas = self.csr.states_of_type("idea")
        foundational = [idea for idea in ideas if getattr(idea, "foundational", False)]
        unexternalized = [
            idea for idea in foundational if not getattr(idea, "evidence_links", [])
        ]

        try:
            burnout = self.csr.get_state_doc(BURNOUT_LATEST_KEY)
            burnout_risk = 1.0 - burnout_health_score(burnout)
            burnout_warnings = 1 if burnout_risk > 0.6 else 0
            capacity_continuity = max(0.0, min(1.0, 1.0 - burnout_risk))
        except KeyError:
            burnout_warnings = 0
            capacity_continuity = 1.0

        try:
            rf_state = self.csr.get_domain_doc(FITNESS_STATE_ID, ReconstructabilityFitnessState)
            assert isinstance(rf_state, ReconstructabilityFitnessState)
            if rf_state.stewardship_readiness_score < 0.5:
                burnout_warnings += 1
                capacity_continuity = min(
                    capacity_continuity,
                    max(0.0, rf_state.stewardship_readiness_score),
                )
        except KeyError:
            pass

        architectural_continuity = compute_architectural_continuity(
            foundational,
            unexternalized,
        )
        debt_score = compute_debt_score(len(unexternalized), burnout_warnings)
        threats = compute_personal_debt_threats(
            unexternalized_ideas=len(unexternalized),
            burnout_warnings=burnout_warnings,
        )

        try:
            prev = self.csr.get_personal_snapshot()
            assert isinstance(prev, PersonalConstitutionalState)
            trend = compute_trend(debt_score, prev)
            version = prev.version + 1
        except KeyError:
            trend = "stable"
            version = 1

        state = PersonalConstitutionalState(
            snapshot_at=now,
            version=version,
            architectural_continuity=architectural_continuity,
            capacity_continuity=capacity_continuity,
            unexternalized_ideas=len(unexternalized),
            burnout_warnings=burnout_warnings,
            debt_score=debt_score,
            threats=threats,
            trend=trend,
        )

        self.csr.register_personal_snapshot(state)
        receipt = build_personal_observation_receipt(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash
        return state
