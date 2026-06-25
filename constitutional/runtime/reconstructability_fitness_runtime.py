"""Reconstructability fitness runtime — v0 auditor of last resort (R-F1 … R-F10)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from constitutional.core.articles import RECONSTRUCTABILITY_INVARIANT
from constitutional.core.models import StateObject
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AmendmentReceiptV2,
    AuthorityBlockV2,
    BaseReceiptV2,
    ContinuityBlockV2,
    DecisionReceiptV2,
    DivergenceReceiptV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReconstructabilityFitnessPayloadV2,
    ReconstructabilityFitnessReceiptV2,
    RemediationReceiptV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    TransitionReceiptV2,
    compute_lineage_hash,
    is_receipt_v2_complete,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

FITNESS_STATE_ID = "reconstructability_fitness__global"
FITNESS_RUNTIME_NAME = "ReconstructabilityFitnessRuntime"
FITNESS_INVARIANT = RECONSTRUCTABILITY_INVARIANT
RF_SURFACE_COUNT = 10


class ReconstructabilityFitnessState(BaseModel):
    state_id: str = FITNESS_STATE_ID
    state_type: str = "reconstructability_fitness"
    snapshot_at: datetime
    version: int = Field(ge=1)

    fitness_score: float = Field(ge=0.0, le=1.0)
    stewardship_readiness_score: float = Field(ge=0.0, le=1.0)

    tested_surfaces: List[RF] = Field(default_factory=list)
    failed_surfaces: List[RF] = Field(default_factory=list)

    implicit_assumptions_required: int = Field(default=0, ge=0)
    missing_artifacts: List[str] = Field(default_factory=list)
    missing_receipts: List[str] = Field(default_factory=list)
    missing_lineage_links: List[str] = Field(default_factory=list)


def build_fitness_receipt(
    state: ReconstructabilityFitnessState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> ReconstructabilityFitnessReceiptV2:
    payload = ReconstructabilityFitnessPayloadV2(
        fitness_score=state.fitness_score,
        stewardship_readiness_score=state.stewardship_readiness_score,
        version=state.version,
        tested_surfaces=[rf.value for rf in state.tested_surfaces],
        failed_surfaces=[rf.value for rf in state.failed_surfaces],
        implicit_assumptions_required=state.implicit_assumptions_required,
        missing_artifacts=list(state.missing_artifacts),
        missing_receipts=list(state.missing_receipts),
        missing_lineage_links=list(state.missing_lineage_links),
    )
    payload_hash = stable_json_hash(payload.model_dump())
    receipt_id = new_receipt_id("rfa")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return ReconstructabilityFitnessReceiptV2(
        receipt_id=receipt_id,
        runtime=FITNESS_RUNTIME_NAME,
        timestamp=ts,
        action_type="reconstructability_fitness_audit",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="audit",
            result_hash=payload_hash,
            notes=f"fitness_score={state.fitness_score:.2f}",
        ),
        invariant=InvariantBlockV2(
            name=FITNESS_INVARIANT,
            description="Independent stewards must reconstruct and operate from constitution + ledger",
            satisfied=state.fitness_score >= 0.8,
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
            source=FITNESS_RUNTIME_NAME,
            jurisdiction="governance",
            legitimacy_basis="reconstructability_fitness_audit",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance_only"],
            scope_out=["execution", "state_mutation"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="GovernanceStewards"),
        signatures=SignaturesBlockV2(runtime_signature="sig-rfa-runtime"),
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
            observed_status="audit",
            observed_at=ts,
            observer_jurisdiction="reconstructability_fitness",
            notes=f"failed_surfaces={len(state.failed_surfaces)}",
        ),
        threats=list(state.failed_surfaces),
        reconstructability_fitness=payload,
    )


class ReconstructabilityFitnessRuntime:
    """v0: periodically tests whether an independent steward could reconstruct the system."""

    resists = list(RF)

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def run_audit(self, snapshot_at: Optional[datetime] = None) -> ReconstructabilityFitnessState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        tested_surfaces: List[RF] = []
        failed_surfaces: List[RF] = []
        missing_artifacts: List[str] = []
        missing_receipts: List[str] = []
        missing_lineage_links: List[str] = []
        implicit_assumptions_required = 0

        tested_surfaces.extend([RF.STATE_LOSS, RF.LINEAGE_BREAK])
        state_ok, state_missing, lineage_from_state = self._test_historical_state()
        if not state_ok:
            failed_surfaces.append(RF.STATE_LOSS)
            missing_artifacts.extend(state_missing)
        if lineage_from_state:
            failed_surfaces.append(RF.LINEAGE_BREAK)
            missing_lineage_links.extend(lineage_from_state)

        tested_surfaces.extend([RF.EVIDENCE_LOSS, RF.AUTHORITY_OPACITY, RF.SEMANTIC_DRIFT])
        dec_ok, dec_missing_receipts, dec_missing_lineage = self._test_decision_replay()
        if not dec_ok:
            failed_surfaces.append(RF.EVIDENCE_LOSS)
            missing_receipts.extend(dec_missing_receipts)
            missing_lineage_links.extend(dec_missing_lineage)

        tested_surfaces.extend([RF.AUTHORITY_OPACITY, RF.ACCOUNTABILITY_EROSION])
        auth_ok, auth_missing = self._test_authority_chain()
        if not auth_ok:
            failed_surfaces.append(RF.AUTHORITY_OPACITY)
            missing_lineage_links.extend(auth_missing)

        tested_surfaces.append(RF.ACCOUNTABILITY_EROSION)
        acct_ok, acct_missing = self._test_accountability()
        if not acct_ok:
            failed_surfaces.append(RF.ACCOUNTABILITY_EROSION)
            missing_lineage_links.extend(acct_missing)

        tested_surfaces.extend([RF.LINEAGE_BREAK, RF.REMEDIATION_AMNESIA])
        amend_ok, amend_missing = self._test_amendment_lineage()
        if not amend_ok:
            if RF.LINEAGE_BREAK not in failed_surfaces:
                failed_surfaces.append(RF.LINEAGE_BREAK)
            missing_lineage_links.extend(amend_missing)

        tested_surfaces.append(RF.REMEDIATION_AMNESIA)
        rem_ok, rem_missing = self._test_remediation_history()
        if not rem_ok:
            failed_surfaces.append(RF.REMEDIATION_AMNESIA)
            missing_receipts.extend(rem_missing)

        tested_surfaces.append(RF.LEARNING_AMNESIA)
        learn_ok, learn_missing = self._test_learning_history()
        if not learn_ok:
            failed_surfaces.append(RF.LEARNING_AMNESIA)
            missing_receipts.extend(learn_missing)

        tested_surfaces.append(RF.STEWARD_DISCONTINUITY)
        steward_ok, assumptions_needed = self._test_cold_start_steward()
        if not steward_ok:
            failed_surfaces.append(RF.STEWARD_DISCONTINUITY)
        implicit_assumptions_required += assumptions_needed

        tested_surfaces.append(RF.SEMANTIC_DRIFT)
        if not self._test_semantic_stability():
            failed_surfaces.append(RF.SEMANTIC_DRIFT)

        tested_surfaces.append(RF.BOUNDARY_CONFUSION)
        if not self._test_boundary_clarity():
            failed_surfaces.append(RF.BOUNDARY_CONFUSION)

        tested_surfaces = list(dict.fromkeys(tested_surfaces))
        failed_surfaces = list(dict.fromkeys(failed_surfaces))

        fitness_score = 1.0 - (len(failed_surfaces) / float(RF_SURFACE_COUNT))
        fitness_score = max(0.0, min(1.0, fitness_score))
        stewardship_readiness_score = 1.0 - min(1.0, implicit_assumptions_required / 10.0)

        try:
            prev = self.csr.get_domain_doc(FITNESS_STATE_ID, ReconstructabilityFitnessState)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = ReconstructabilityFitnessState(
            snapshot_at=now,
            version=version,
            fitness_score=fitness_score,
            stewardship_readiness_score=stewardship_readiness_score,
            tested_surfaces=tested_surfaces,
            failed_surfaces=failed_surfaces,
            implicit_assumptions_required=implicit_assumptions_required,
            missing_artifacts=missing_artifacts,
            missing_receipts=missing_receipts,
            missing_lineage_links=missing_lineage_links,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=FITNESS_STATE_ID,
                state_type="reconstructability_fitness",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(FITNESS_STATE_ID, "reconstructability_fitness", state)
        self._emit_fitness_receipt(state)
        return state

    def _all_receipts(self) -> list[BaseReceiptV2]:
        return self.csr.get_all_receipts()

    def _decision_like_receipts(self) -> list[BaseReceiptV2]:
        receipts: list[BaseReceiptV2] = []
        for receipt in self._all_receipts():
            if isinstance(receipt, DecisionReceiptV2):
                receipts.append(receipt)
            elif isinstance(receipt, TransitionReceiptV2):
                receipts.append(receipt)
            elif receipt.lifecycle.stage == "decision":
                receipts.append(receipt)
        return receipts

    def _test_historical_state(self) -> Tuple[bool, List[str], List[str]]:
        missing: List[str] = []
        lineage_missing: List[str] = []
        states = [
            state
            for state in self.csr.all_states()
            if state.state_id != FITNESS_STATE_ID
        ]
        if not states:
            missing.append("no_states_present")
            return False, missing, lineage_missing

        for state in states:
            transition_receipts = self.csr.receipts_for(state.state_id)
            if not transition_receipts:
                continue
            try:
                replay = self.csr.replay(state.state_id)
            except Exception:
                missing.append(f"state_replay_failed:{state.state_id}")
                continue
            if replay.diverged:
                lineage_missing.append(f"replay_diverged:{state.state_id}")
        if missing:
            return False, missing, lineage_missing
        return True, missing, lineage_missing

    def _test_decision_replay(self) -> Tuple[bool, List[str], List[str]]:
        missing_receipts: List[str] = []
        missing_lineage: List[str] = []
        decisions = self._decision_like_receipts()
        if not decisions:
            return True, missing_receipts, missing_lineage

        for receipt in decisions:
            if not receipt.evidence.bundle_id:
                missing_receipts.append(receipt.receipt_id)
            if not receipt.evidence.sources and not is_receipt_v2_complete(receipt):
                missing_receipts.append(receipt.receipt_id)

        ok = not missing_receipts
        return ok, missing_receipts, missing_lineage

    def _test_authority_chain(self) -> Tuple[bool, List[str]]:
        missing: List[str] = []
        receipts = self._all_receipts()
        if not receipts:
            return True, missing
        for receipt in receipts:
            if not receipt.authority.source or not receipt.authority.legitimacy_basis:
                missing.append(f"authority_missing:{receipt.receipt_id}")
        if missing:
            missing.append("no_authority_chain_present")
            return False, missing
        return True, missing

    def _test_accountability(self) -> Tuple[bool, List[str]]:
        missing: List[str] = []
        for receipt in self._all_receipts():
            party = receipt.accountability.primary_accountable_party
            if not party or not str(party).strip():
                missing.append(f"accountable_party_missing:{receipt.receipt_id}")
        return not missing, missing

    def _test_amendment_lineage(self) -> Tuple[bool, List[str]]:
        missing: List[str] = []
        amendments = [
            receipt
            for receipt in self._all_receipts()
            if isinstance(receipt, AmendmentReceiptV2)
        ]
        if not amendments:
            return True, missing

        for receipt in amendments:
            stage = receipt.amendment.amendment_stage
            if stage == "proposed":
                continue
            if not receipt.lifecycle.previous_stage_receipt_id:
                missing.append(f"amendment_lineage_missing:{receipt.receipt_id}")
        if missing:
            missing.append("no_amendment_supersession_links")
            return False, missing
        return True, missing

    def _test_remediation_history(self) -> Tuple[bool, List[str]]:
        missing: List[str] = []
        receipts = self._all_receipts()
        divergences = [receipt for receipt in receipts if isinstance(receipt, DivergenceReceiptV2)]
        if not divergences:
            return True, missing

        remediation_parents = {
            receipt.lifecycle.previous_stage_receipt_id
            for receipt in receipts
            if isinstance(receipt, RemediationReceiptV2)
            and receipt.lifecycle.previous_stage_receipt_id
        }
        for divergence in divergences:
            if divergence.receipt_id not in remediation_parents:
                missing.append(f"remediation_missing_for:{divergence.receipt_id}")
        return not missing, missing

    def _test_learning_history(self) -> Tuple[bool, List[str]]:
        missing: List[str] = []
        receipts = self._all_receipts()
        amendments = [
            receipt
            for receipt in receipts
            if isinstance(receipt, AmendmentReceiptV2)
            and receipt.amendment.amendment_stage in ("implemented", "observed", "closed")
        ]
        if not amendments:
            return True, missing

        learning = [
            receipt
            for receipt in receipts
            if receipt.action_type == "constitutional_learning"
        ]
        if not learning:
            missing.append("no_learning_receipts_for_amendments")
            return False, missing
        return True, missing

    def _test_cold_start_steward(self) -> Tuple[bool, int]:
        assumptions = 0
        decisions = self._decision_like_receipts()
        if not decisions:
            return True, assumptions

        for receipt in decisions:
            if not receipt.invariant.name:
                assumptions += 1
            if not receipt.authority.source or not receipt.authority.legitimacy_basis:
                assumptions += 1
            if not receipt.evidence.bundle_id:
                assumptions += 1

        return assumptions == 0, assumptions

    def _test_semantic_stability(self) -> bool:
        registry = self.csr.invariant_registry
        if not registry:
            return True
        for receipt in self._all_receipts():
            name = receipt.invariant.name
            if name and name not in registry:
                return False
        return True

    def _test_boundary_clarity(self) -> bool:
        for receipt in self._all_receipts():
            boundary = receipt.impact_boundary
            if not boundary.scope_in or not boundary.scope_out:
                return False
        return True

    def _emit_fitness_receipt(self, state: ReconstructabilityFitnessState) -> None:
        receipt = build_fitness_receipt(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash
