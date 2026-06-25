"""Hiddenness pressure loop — drives R, P, and stewardship work from implicit knowledge."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.core.articles import (
    HIDDENNESS_AMENDMENT_COMPLETE_INDEX,
    HIDDENNESS_PRESSURE_QUESTION,
    SUCCESSION_MIN_FITNESS,
)
from constitutional.hiddenness.hiddenness_amendment import (
    maybe_trigger_hiddenness_amendment,
    open_or_escalate_hiddenness_amendment,
)
from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF
from constitutional.hiddenness.hiddenness_runtime import HIDDENNESS_STATE_ID, HiddennessState
from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessStateV2
from constitutional.hiddenness.hiddenness_work_queue import (
    HiddennessWorkQueue,
    load_hiddenness_work_queue,
    sync_hiddenness_state_to_work_queue,
)
from constitutional.purpose.purpose_continuity_amendment import (
    maybe_trigger_purpose_continuity_amendment,
    open_or_escalate_purpose_amendment,
)
from constitutional.runtime.mission_fidelity_runtime import (
    MISSION_FIDELITY_STATE_ID,
    MissionFidelityState,
    build_mission_fidelity_receipt,
)
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.purpose_failures import PF_SURFACE_COUNT
from constitutional.runtime.reconstructability_dashboard import ReconstructabilityDashboardState
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import (
    FITNESS_STATE_ID,
    RF_SURFACE_COUNT,
    ReconstructabilityFitnessState,
    build_fitness_receipt,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.survivability_amendment import open_or_escalate_survivability_amendment


def _latest_hiddenness_receipt_id(csr: ConstitutionalStateRuntime) -> str | None:
    receipts = csr.observation_receipts_for(HIDDENNESS_STATE_ID)
    if not receipts:
        return None
    return receipts[-1].receipt_id


def _append_fitness_receipt(csr: ConstitutionalStateRuntime, state: ReconstructabilityFitnessState) -> None:
    receipts = csr.observation_receipts_for(FITNESS_STATE_ID)
    previous_id = receipts[-1].receipt_id if receipts else None
    previous_hash = receipts[-1].continuity.lineage_hash if receipts else None
    receipt = build_fitness_receipt(
        state,
        previous_receipt_id=previous_id,
        previous_lineage_hash=previous_hash,
    )
    notes = receipt.outputs.notes or ""
    hiddenness_id = _latest_hiddenness_receipt_id(csr)
    if hiddenness_id:
        receipt.outputs.notes = f"{notes}; hiddenness_receipt={hiddenness_id}".strip("; ")
    csr.append_observation_receipt(receipt)


def _append_mission_receipt(csr: ConstitutionalStateRuntime, state: MissionFidelityState) -> None:
    receipts = csr.observation_receipts_for(MISSION_FIDELITY_STATE_ID)
    previous_id = receipts[-1].receipt_id if receipts else None
    previous_hash = receipts[-1].continuity.lineage_hash if receipts else None
    receipt = build_mission_fidelity_receipt(
        state,
        previous_receipt_id=previous_id,
        previous_lineage_hash=previous_hash,
    )
    hiddenness_id = _latest_hiddenness_receipt_id(csr)
    if hiddenness_id:
        notes = receipt.outputs.notes or ""
        receipt.outputs.notes = f"{notes}; hiddenness_receipt={hiddenness_id}".strip("; ")
    csr.append_observation_receipt(receipt)


def _hiddenness_lineage_gaps(hiddenness: HiddennessState | HiddennessStateV2) -> list[str]:
    gaps = getattr(hiddenness, "lineage_gaps", None)
    return list(gaps) if gaps else []


def _hiddenness_invariant_drift(hiddenness: HiddennessState | HiddennessStateV2) -> list[str]:
    drift = getattr(hiddenness, "invariant_drift_candidates", None)
    return list(drift) if drift else []


def _hiddenness_semantic_mismatches(hiddenness: HiddennessState | HiddennessStateV2) -> list[str]:
    mismatches = getattr(hiddenness, "semantic_mismatches", None)
    return list(mismatches) if mismatches else []


def apply_hiddenness_to_fitness(
    csr: ConstitutionalStateRuntime,
    fitness: ReconstructabilityFitnessState,
    hiddenness: HiddennessState | HiddennessStateV2,
) -> ReconstructabilityFitnessState:
    """Fitness cannot report green while hidden invariants or lineage gaps remain."""
    failed = list(dict.fromkeys(fitness.failed_surfaces))
    missing_lineage = list(dict.fromkeys(fitness.missing_lineage_links))
    missing_artifacts = list(dict.fromkeys(fitness.missing_artifacts))

    hiddenness_blocked = bool(
        hiddenness.undocumented_invariants
        or _hiddenness_lineage_gaps(hiddenness)
        or _hiddenness_invariant_drift(hiddenness)
    )

    if hiddenness.undocumented_invariants or _hiddenness_invariant_drift(hiddenness):
        if RF.SEMANTIC_DRIFT not in failed:
            failed.append(RF.SEMANTIC_DRIFT)
        for item in hiddenness.undocumented_invariants[:5]:
            tag = f"hiddenness:undocumented_invariant:{item}"
            if tag not in missing_lineage:
                missing_lineage.append(tag)
        for item in _hiddenness_invariant_drift(hiddenness)[:3]:
            tag = f"hiddenness:invariant_drift:{item}"
            if tag not in missing_lineage:
                missing_lineage.append(tag)

    lineage_gaps = _hiddenness_lineage_gaps(hiddenness)
    if lineage_gaps:
        if RF.LINEAGE_BREAK not in failed:
            failed.append(RF.LINEAGE_BREAK)
        for gap in lineage_gaps[:5]:
            tag = f"hiddenness:lineage_gap:{gap}"
            if tag not in missing_lineage:
                missing_lineage.append(tag)

    fitness_score = max(0.0, min(1.0, 1.0 - len(failed) / float(RF_SURFACE_COUNT)))
    if hiddenness_blocked:
        fitness_score = min(fitness_score, SUCCESSION_MIN_FITNESS - 0.01)

    hiddenness_id = _latest_hiddenness_receipt_id(csr)
    if hiddenness_id:
        link = f"hiddenness_receipt:{hiddenness_id}"
        if link not in missing_artifacts:
            missing_artifacts.append(link)

    updated = fitness.model_copy(
        update={
            "failed_surfaces": failed,
            "missing_lineage_links": missing_lineage,
            "missing_artifacts": missing_artifacts,
            "fitness_score": fitness_score,
        }
    )
    csr.put_domain_doc(FITNESS_STATE_ID, "reconstructability_fitness", updated)
    _append_fitness_receipt(csr, updated)
    return updated


def apply_hiddenness_to_mission_fidelity(
    csr: ConstitutionalStateRuntime,
    mission: MissionFidelityState,
    hiddenness: HiddennessState | HiddennessStateV2,
) -> MissionFidelityState:
    """Mission fidelity cannot pass while hidden purpose fragments or semantic mismatches remain."""
    failed = list(dict.fromkeys(mission.failed_surfaces))
    missing = list(dict.fromkeys(mission.missing_purpose_artifacts))
    ambiguous = list(dict.fromkeys(mission.ambiguous_interpretations))

    if hiddenness.undocumented_purpose_fragments:
        if PF.PURPOSE_FRAGMENTATION not in failed:
            failed.append(PF.PURPOSE_FRAGMENTATION)
        for fragment in hiddenness.undocumented_purpose_fragments[:5]:
            tag = f"hiddenness:purpose_fragment:{fragment}"
            if tag not in missing:
                missing.append(tag)

    semantic_mismatches = _hiddenness_semantic_mismatches(hiddenness)
    if semantic_mismatches:
        if PF.PURPOSE_AMBIGUITY not in failed:
            failed.append(PF.PURPOSE_AMBIGUITY)
        for mismatch in semantic_mismatches[:5]:
            tag = f"hiddenness:semantic_mismatch:{mismatch}"
            if tag not in ambiguous:
                ambiguous.append(tag)
            if tag not in missing:
                missing.append(tag)

    purpose_fidelity_score = max(0.0, 1.0 - len(failed) / float(PF_SURFACE_COUNT))
    invariant_interpretation_score = max(0.0, 1.0 - (len(ambiguous) / 5.0))
    mission_legibility_score = 0.0 if PF.MISSION_AMNESIA in failed else 1.0
    purpose_continuity_index = min(
        purpose_fidelity_score,
        invariant_interpretation_score,
        mission_legibility_score,
    )

    updated = mission.model_copy(
        update={
            "failed_surfaces": failed,
            "missing_purpose_artifacts": missing,
            "ambiguous_interpretations": ambiguous,
            "purpose_fidelity_score": purpose_fidelity_score,
            "invariant_interpretation_score": invariant_interpretation_score,
            "mission_legibility_score": mission_legibility_score,
            "purpose_continuity_index": purpose_continuity_index,
        }
    )
    csr.put_domain_doc(MISSION_FIDELITY_STATE_ID, "mission_fidelity", updated)
    _append_mission_receipt(csr, updated)
    return updated


def _escalate_unresolved_work_items(
    csr: ConstitutionalStateRuntime,
    queue: HiddennessWorkQueue,
    hiddenness: HiddennessState | HiddennessStateV2,
    *,
    opened_at: datetime,
) -> None:
    """High/critical unresolved items force hiddenness amendments."""
    threats = list(hiddenness.failed_surfaces)
    for item in queue.unresolved():
        if item.severity not in ("high", "critical"):
            continue
        open_or_escalate_hiddenness_amendment(
            csr,
            scope="hiddenness",
            reason=f"Unresolved hiddenness item: {item.description}",
            threats=threats,
            opened_at=opened_at,
        )


def apply_hiddenness_pressure(
    csr: ConstitutionalStateRuntime,
    hiddenness: HiddennessState | HiddennessStateV2,
    fitness: ReconstructabilityFitnessState,
    mission: MissionFidelityState,
    dashboard: ReconstructabilityDashboardState,
    *,
    opened_at: datetime | None = None,
) -> HiddennessWorkQueue:
    """Drive amendments and constitutional evolution from the hiddenness work queue."""
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    queue = sync_hiddenness_state_to_work_queue(csr, hiddenness, source="HiddennessRuntimeV2", now=now)

    _escalate_unresolved_work_items(csr, queue, hiddenness, opened_at=now)

    if hiddenness.hiddenness_index < HIDDENNESS_AMENDMENT_COMPLETE_INDEX or hiddenness.failed_surfaces:
        open_or_escalate_hiddenness_amendment(
            csr,
            scope="hiddenness",
            reason=f"{HIDDENNESS_PRESSURE_QUESTION} Hiddenness above constitutional threshold.",
            threats=list(hiddenness.failed_surfaces),
            opened_at=now,
        )
        maybe_trigger_hiddenness_amendment(csr, hiddenness, opened_at=now)

    if hiddenness.undocumented_purpose_fragments or _hiddenness_semantic_mismatches(hiddenness):
        maybe_trigger_purpose_continuity_amendment(csr, mission, opened_at=now)
        if hiddenness.undocumented_purpose_fragments:
            open_or_escalate_purpose_amendment(
                csr,
                scope="hiddenness_purpose",
                reason="Undocumented purpose fragments detected by Hiddenness runtime.",
                threats=[PF.PURPOSE_FRAGMENTATION],
                opened_at=now,
            )

    if hiddenness.undocumented_authority or hiddenness.implicit_assumptions or hiddenness.founder_only_knowledge:
        open_or_escalate_hiddenness_amendment(
            csr,
            scope="stewardship",
            reason="Hidden authority or implicit stewardship knowledge detected.",
            threats=[HF.HIDDEN_AUTHORITY, HF.HIDDEN_ASSUMPTION, HF.HIDDEN_STEWARD_KNOWLEDGE],
            opened_at=now,
        )
        open_or_escalate_survivability_amendment(csr, dashboard, fitness=fitness, opened_at=now)

    return queue
