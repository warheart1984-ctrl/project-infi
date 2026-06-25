"""Mission fidelity runtime v0 — falsifies Article P (Purpose Continuity)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import List, Tuple

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    PURPOSE_CONTINUITY_INVARIANT,
    RECONSTRUCTABILITY_INVARIANT,
)
from constitutional.core.models import StateObject
from constitutional.runtime.fitness_risk import get_reconstructability_fitness_state
from constitutional.runtime.purpose_failures import PF_SURFACE_COUNT, PurposeFailureClass as PF
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    BaseReceiptV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    MissionFidelityPayloadV2,
    MissionFidelityReceiptV2,
    ObservationPayloadV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import (
    FITNESS_STATE_ID,
    ReconstructabilityFitnessState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER

MISSION_FIDELITY_STATE_ID = "mission_fidelity__global"
MISSION_STATEMENT_STATE_ID = "mission_statement__global"
MISSION_FIDELITY_RUNTIME_NAME = "MissionFidelityRuntime"
MIN_MISSION_TEXT_LENGTH = 20
MIN_FOUNDING_CONTEXT_LENGTH = 20


class MissionStatementState(BaseModel):
    """Founding purpose artifacts — legibility inputs for Mission Fidelity."""

    state_id: str = MISSION_STATEMENT_STATE_ID
    state_type: str = "mission_statement"
    text: str
    invariant_rationale: str = ""
    founding_context: str = ""
    version: int = Field(default=1, ge=1)


class MissionFidelityState(BaseModel):
    state_id: str = MISSION_FIDELITY_STATE_ID
    state_type: str = "mission_fidelity"
    snapshot_at: datetime
    version: int = Field(ge=1)

    purpose_fidelity_score: float = Field(ge=0.0, le=1.0)
    invariant_interpretation_score: float = Field(ge=0.0, le=1.0)
    mission_legibility_score: float = Field(ge=0.0, le=1.0)
    purpose_continuity_index: float = Field(ge=0.0, le=1.0)

    tested_surfaces: List[PF] = Field(default_factory=list)
    failed_surfaces: List[PF] = Field(default_factory=list)
    missing_purpose_artifacts: List[str] = Field(default_factory=list)
    ambiguous_interpretations: List[str] = Field(default_factory=list)
    conflicting_justifications: List[str] = Field(default_factory=list)


def load_mission_fidelity_state(csr: ConstitutionalStateRuntime) -> MissionFidelityState:
    doc = csr.get_domain_doc(MISSION_FIDELITY_STATE_ID, MissionFidelityState)
    assert isinstance(doc, MissionFidelityState)
    return doc


def load_mission_statement(csr: ConstitutionalStateRuntime) -> MissionStatementState | None:
    try:
        doc = csr.get_domain_doc(MISSION_STATEMENT_STATE_ID, MissionStatementState)
        assert isinstance(doc, MissionStatementState)
        return doc
    except KeyError:
        return None


def build_mission_fidelity_receipt(
    state: MissionFidelityState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> MissionFidelityReceiptV2:
    payload = MissionFidelityPayloadV2(
        purpose_fidelity_score=state.purpose_fidelity_score,
        invariant_interpretation_score=state.invariant_interpretation_score,
        mission_legibility_score=state.mission_legibility_score,
        purpose_continuity_index=state.purpose_continuity_index,
        version=state.version,
        tested_surfaces=[pf.value for pf in state.tested_surfaces],
        failed_surfaces=[pf.value for pf in state.failed_surfaces],
        missing_purpose_artifacts=list(state.missing_purpose_artifacts),
        ambiguous_interpretations=list(state.ambiguous_interpretations),
        conflicting_justifications=list(state.conflicting_justifications),
    )
    payload_hash = stable_json_hash(payload.model_dump())
    receipt_id = new_receipt_id("mfi")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return MissionFidelityReceiptV2(
        receipt_id=receipt_id,
        runtime=MISSION_FIDELITY_RUNTIME_NAME,
        timestamp=ts,
        action_type="mission_fidelity_test",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="test",
            result_hash=payload_hash,
            notes=f"purpose_continuity_index={state.purpose_continuity_index:.2f}",
        ),
        invariant=InvariantBlockV2(
            name=PURPOSE_CONTINUITY_INVARIANT,
            description="System must preserve founding purpose and invariant meaning",
            satisfied=state.purpose_continuity_index >= 0.7,
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
            source=MISSION_FIDELITY_RUNTIME_NAME,
            jurisdiction="purpose",
            legitimacy_basis=ARTICLE_P_REFERENCE,
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance", "mission_preconditions", "amendment_triggers"],
            scope_out=["execution", "state_mutation"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="GovernanceStewards"),
        signatures=SignaturesBlockV2(runtime_signature="sig-mfi-runtime"),
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
            observed_status="test",
            observed_at=ts,
            observer_jurisdiction="mission_fidelity",
            notes=f"failed_surfaces={len(state.failed_surfaces)}",
        ),
        threats=list(state.failed_surfaces),
        mission_fidelity=payload,
    )


class MissionFidelityRuntime:
    """v0: tests whether the system still understands why it exists."""

    resists = list(PF)

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def run_test(self, snapshot_at: datetime | None = None) -> MissionFidelityState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        tested: List[PF] = []
        failed: List[PF] = []
        missing: List[str] = []
        ambiguous: List[str] = []
        conflicting: List[str] = []

        tested.append(PF.MISSION_AMNESIA)
        if not self._mission_is_legible():
            failed.append(PF.MISSION_AMNESIA)
            missing.append("mission_statement")

        tested.append(PF.INVARIANT_DILUTION)
        ok, issues = self._invariant_interpretable()
        if not ok:
            failed.append(PF.INVARIANT_DILUTION)
            ambiguous.extend(issues)

        tested.append(PF.PURPOSE_DRIFT)
        if self._purpose_has_drifted():
            failed.append(PF.PURPOSE_DRIFT)

        tested.append(PF.TELOS_INVERSION)
        if self._detect_telos_inversion():
            failed.append(PF.TELOS_INVERSION)

        tested.append(PF.PURPOSE_FRAGMENTATION)
        if self._detect_fragmentation(conflicting):
            failed.append(PF.PURPOSE_FRAGMENTATION)

        tested.append(PF.CULTURAL_DISCONTINUITY)
        if self._detect_cultural_discontinuity(missing):
            failed.append(PF.CULTURAL_DISCONTINUITY)

        tested.append(PF.PURPOSE_AMBIGUITY)
        if ambiguous:
            failed.append(PF.PURPOSE_AMBIGUITY)

        tested.append(PF.PURPOSE_DEGENERATION)
        if self._detect_purpose_degeneration():
            failed.append(PF.PURPOSE_DEGENERATION)

        tested.append(PF.PURPOSE_CAPTURE)
        if self._detect_purpose_capture(conflicting):
            failed.append(PF.PURPOSE_CAPTURE)

        tested.append(PF.PURPOSE_CORRUPTION)
        if self._detect_purpose_corruption():
            failed.append(PF.PURPOSE_CORRUPTION)

        tested = list(dict.fromkeys(tested))
        failed = list(dict.fromkeys(failed))

        purpose_fidelity_score = max(0.0, 1.0 - len(failed) / float(PF_SURFACE_COUNT))
        invariant_interpretation_score = max(0.0, 1.0 - (len(ambiguous) / 5.0))
        mission_legibility_score = 0.0 if PF.MISSION_AMNESIA in failed else 1.0
        purpose_continuity_index = min(
            purpose_fidelity_score,
            invariant_interpretation_score,
            mission_legibility_score,
        )

        try:
            prev = load_mission_fidelity_state(self.csr)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = MissionFidelityState(
            snapshot_at=now,
            version=version,
            purpose_fidelity_score=purpose_fidelity_score,
            invariant_interpretation_score=invariant_interpretation_score,
            mission_legibility_score=mission_legibility_score,
            purpose_continuity_index=purpose_continuity_index,
            tested_surfaces=tested,
            failed_surfaces=failed,
            missing_purpose_artifacts=missing,
            ambiguous_interpretations=ambiguous,
            conflicting_justifications=conflicting,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=MISSION_FIDELITY_STATE_ID,
                state_type="mission_fidelity",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(MISSION_FIDELITY_STATE_ID, "mission_fidelity", state)
        self._emit_receipt(state)
        return state

    def _emit_receipt(self, state: MissionFidelityState) -> None:
        receipt = build_mission_fidelity_receipt(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash

    def _mission_is_legible(self) -> bool:
        mission = load_mission_statement(self.csr)
        if mission is None:
            return False
        return len(mission.text.strip()) >= MIN_MISSION_TEXT_LENGTH

    def _invariant_interpretable(self) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        registry = self.csr.invariant_registry
        if not registry:
            issues.append("empty_invariant_registry")

        if PURPOSE_CONTINUITY_INVARIANT not in registry and RECONSTRUCTABILITY_INVARIANT not in registry:
            issues.append("core_invariants_not_registered")

        mission = load_mission_statement(self.csr)
        if mission is not None and not mission.invariant_rationale.strip():
            issues.append("missing_invariant_rationale")

        receipt_invariants: set[str] = set()
        for receipt in self._all_receipts():
            name = receipt.invariant.name
            if name:
                receipt_invariants.add(name)
                if registry and name not in registry:
                    issues.append(f"unregistered_invariant:{name}")

        if len(receipt_invariants) > max(len(registry), 1) * 3:
            issues.append("invariant_proliferation")

        return len(issues) == 0, issues

    def _purpose_has_drifted(self) -> bool:
        try:
            fitness = get_reconstructability_fitness_state(self.csr)
        except KeyError:
            return True
        return RF.SEMANTIC_DRIFT in fitness.failed_surfaces

    def _detect_telos_inversion(self) -> bool:
        """Self-preservation metrics high while mission legibility fails."""
        try:
            fitness = self.csr.get_domain_doc(FITNESS_STATE_ID, ReconstructabilityFitnessState)
            assert isinstance(fitness, ReconstructabilityFitnessState)
        except KeyError:
            return False
        survivability_proxy = fitness.fitness_score
        return survivability_proxy >= 0.6 and not self._mission_is_legible()

    def _detect_fragmentation(self, conflicting: List[str]) -> bool:
        runtime_names = set(RUNTIME_CHARTER)
        receipt_runtimes = {receipt.runtime for receipt in self._all_receipts() if receipt.runtime}
        orphan_runtimes = receipt_runtimes - runtime_names - {MISSION_FIDELITY_RUNTIME_NAME}
        if orphan_runtimes:
            conflicting.extend(f"orphan_runtime:{name}" for name in sorted(orphan_runtimes))
            return True
        return False

    def _detect_cultural_discontinuity(self, missing: List[str]) -> bool:
        mission = load_mission_statement(self.csr)
        if mission is None:
            missing.append("founding_context")
            return True
        if len(mission.founding_context.strip()) < MIN_FOUNDING_CONTEXT_LENGTH:
            missing.append("founding_context")
            return True
        return False

    def _detect_purpose_degeneration(self) -> bool:
        mission = load_mission_statement(self.csr)
        if mission is None:
            return False
        words = mission.text.lower().split()
        if len(words) < 8:
            return True
        trivial = {"maintain", "operate", "run", "continue", "system", "the", "a", "to"}
        substantive = [word for word in words if word not in trivial]
        return len(substantive) < 4

    def _detect_purpose_capture(self, conflicting: List[str]) -> bool:
        parties: set[str] = set()
        for receipt in self._all_receipts():
            party = receipt.accountability.primary_accountable_party
            if party:
                parties.add(party)
        if len(parties) == 1 and parties != {"GovernanceStewards"}:
            conflicting.append(f"single_accountable_party:{next(iter(parties))}")
            return True
        return False

    def _detect_purpose_corruption(self) -> bool:
        mission = load_mission_statement(self.csr)
        if mission is None:
            return False
        corruption_markers = ("weaponize", "exploit", "deceive", "invert purpose", "subvert")
        lowered = mission.text.lower()
        return any(marker in lowered for marker in corruption_markers)

    def _all_receipts(self) -> list[BaseReceiptV2]:
        return self.csr.get_all_receipts()
