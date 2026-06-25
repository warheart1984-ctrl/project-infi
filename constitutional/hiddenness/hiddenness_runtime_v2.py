"""Hiddenness Runtime v2 — semantic diff, invariant drift, and lineage-linked receipts.

Hiddenness is not a sibling of Fitness or Mission Fidelity. It is constitutional
pressure — the meta-runtime that asks what required knowledge still exists outside
the system, making R-F, S-F, and P-F failures possible.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import List

from pydantic import Field

from constitutional.core.articles import (
    ARTICLE_H_REFERENCE,
    HIDDENNESS_AMENDMENT_TEMPLATE_ID,
    HIDDENNESS_RECEIPT_INVARIANT,
    PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID,
    PURPOSE_CONTINUITY_INVARIANT,
)
from constitutional.core.models import StateObject
from constitutional.hiddenness.hiddenness_amendment import maybe_trigger_hiddenness_amendment
from constitutional.hiddenness.hiddenness_work_queue import sync_hiddenness_state_to_work_queue
from constitutional.hiddenness.hiddenness_failures import (
    HF_SURFACE_COUNT,
    HiddennessFailureClass as HF,
    hf_surface_code,
)
from constitutional.hiddenness.hiddenness_runtime import (
    HIDDENNESS_STATE_ID,
    HiddennessRuntime,
    HiddennessState,
)
from constitutional.hiddenness.semantic_registries import (
    InvariantRegistryView,
    PolicyGraphView,
    PurposeRegistryView,
    get_invariant_registry,
    get_policy_graph,
    get_purpose_registry,
    normalize_invariant_text,
    purpose_protection_tokens,
    throughput_optimization_tokens,
)
from constitutional.runtime.mission_fidelity_runtime import (
    MISSION_FIDELITY_STATE_ID,
    MissionFidelityState,
)
from constitutional.runtime.reconstructability_dashboard import (
    DASHBOARD_STATE_ID,
    ReconstructabilityDashboardState,
)
from constitutional.runtime.reconstructability_fitness_runtime import (
    FITNESS_STATE_ID,
    ReconstructabilityFitnessState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    HiddennessLineageLinksV2,
    HiddennessPayloadV2,
    HiddennessReceiptV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    stable_json_hash,
)

HIDDENNESS_RUNTIME_V2_NAME = "HiddennessRuntimeV2"


class HiddennessStateV2(HiddennessState):
    """Article H state with semantic-diff and lineage surfaces."""

    invariant_drift_candidates: List[str] = Field(default_factory=list)
    semantic_mismatches: List[str] = Field(default_factory=list)
    lineage_gaps: List[str] = Field(default_factory=list)
    lineage_links: HiddennessLineageLinksV2 = Field(default_factory=HiddennessLineageLinksV2)


def load_hiddenness_state_v2(csr: ConstitutionalStateRuntime) -> HiddennessStateV2:
    doc = csr.get_domain_doc(HIDDENNESS_STATE_ID, HiddennessStateV2)
    assert isinstance(doc, HiddennessStateV2)
    return doc


def build_hiddenness_receipt_v2(
    state: HiddennessStateV2,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> HiddennessReceiptV2:
    payload = HiddennessPayloadV2(
        kind="HiddennessV2",
        invariant=HIDDENNESS_RECEIPT_INVARIANT,
        hiddenness_index=state.hiddenness_index,
        explicitness_score=state.hiddenness_index,
        version=state.version,
        failed_surfaces=[hf_surface_code(hf) for hf in state.failed_surfaces],
        missing_items=list(state.missing_items),
        implicit_assumptions=list(state.implicit_assumptions),
        undocumented_invariants=list(state.undocumented_invariants),
        undocumented_purpose_fragments=list(state.undocumented_purpose_fragments),
        undocumented_authority=list(state.undocumented_authority),
        undocumented_context=list(state.undocumented_context),
        undocumented_constraints=list(state.undocumented_constraints),
        founder_only_knowledge=list(state.founder_only_knowledge),
        invariant_drift_candidates=list(state.invariant_drift_candidates),
        semantic_mismatches=list(state.semantic_mismatches),
        lineage_gaps=list(state.lineage_gaps),
        lineage_links=state.lineage_links,
        hidden_items=[
            {
                "category": item.category.value,
                "description": item.description,
                "source": item.source,
                "hf_threat": hf_surface_code(item.hf_threat),
                "pf_threat": item.pf_threat.value,
                "amendment_required": item.amendment_required,
            }
            for item in state.hidden_items
        ],
        hf_threats=[hf_surface_code(hf) for hf in state.failed_surfaces],
        pf_threats=[pf.value for pf in state.pf_threats],
        missing_purpose_artifacts=list(state.missing_purpose_artifacts),
    )
    payload_hash = stable_json_hash(payload.model_dump())
    ts_slug = state.snapshot_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_id = f"hiddenness-v2-{ts_slug}-v{state.version}"
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return HiddennessReceiptV2(
        receipt_id=receipt_id,
        runtime=HIDDENNESS_RUNTIME_V2_NAME,
        timestamp=ts,
        action_type="hiddenness_audit",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="audit",
            result_hash=payload_hash,
            notes=(
                f"hiddenness_index={state.hiddenness_index:.2f} "
                f"drift={len(state.invariant_drift_candidates)} "
                f"mismatch={len(state.semantic_mismatches)}"
            ),
        ),
        invariant=InvariantBlockV2(
            name=HIDDENNESS_RECEIPT_INVARIANT,
            description="Nothing required for continuity, legitimacy, or meaning may remain hidden",
            satisfied=state.hiddenness_index >= 0.7 and len(state.failed_surfaces) == 0,
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
            source=HIDDENNESS_RUNTIME_V2_NAME,
            jurisdiction="hiddenness",
            legitimacy_basis=ARTICLE_H_REFERENCE,
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance", "mission_preconditions", "amendment_triggers", "lineage"],
            scope_out=["execution", "state_mutation"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="GovernanceStewards"),
        signatures=SignaturesBlockV2(runtime_signature="sig-hid-runtime-v2"),
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
            observer_jurisdiction="hiddenness",
            notes=f"semantic_diff surfaces={len(state.semantic_mismatches)}",
        ),
        threats=list(state.failed_surfaces),
        hiddenness=payload,
    )


class HiddennessRuntimeV2:
    """v2: compare what the system claims vs what it encodes and does (Article H)."""

    resists = list(HF)

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        invariant_registry: InvariantRegistryView | None = None,
        purpose_registry: PurposeRegistryView | None = None,
        policy_graph: PolicyGraphView | None = None,
    ) -> None:
        self.csr = csr
        self._v1 = HiddennessRuntime(csr)
        self.invariant_registry = invariant_registry or get_invariant_registry(csr)
        self.purpose_registry = purpose_registry or get_purpose_registry(csr)
        self.policy_graph = policy_graph or get_policy_graph(csr)
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def run_scan(
        self,
        snapshot_at: datetime | None = None,
        *,
        trigger_amendments: bool = True,
    ) -> HiddennessStateV2:
        return self.run_audit(snapshot_at=snapshot_at, trigger_amendments=trigger_amendments)

    def run_audit(
        self,
        snapshot_at: datetime | None = None,
        *,
        trigger_amendments: bool = True,
    ) -> HiddennessStateV2:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        base = self._v1.run_audit(snapshot_at=now, trigger_amendments=False)

        extra_failed: list[HF] = []
        invariant_drift = self._detect_invariant_drift()
        if invariant_drift:
            extra_failed.append(HF.HIDDEN_INVARIANT)

        semantic_mismatches = self._detect_semantic_mismatch()
        if semantic_mismatches:
            extra_failed.append(HF.HIDDEN_MEANING)

        lineage_gaps = self._find_lineage_gaps()
        if lineage_gaps:
            extra_failed.append(HF.HIDDEN_DEPENDENCY)

        failed_surfaces = list(dict.fromkeys(base.failed_surfaces + extra_failed))
        hiddenness_index = max(0.0, 1.0 - len(failed_surfaces) / float(HF_SURFACE_COUNT))

        lineage_links = self._build_lineage_links(base.version)

        state = HiddennessStateV2(
            snapshot_at=base.snapshot_at,
            version=base.version,
            hiddenness_index=hiddenness_index,
            failed_surfaces=failed_surfaces,
            missing_items=list(base.missing_items),
            implicit_assumptions=list(base.implicit_assumptions),
            undocumented_invariants=list(base.undocumented_invariants)
            + [item for item in invariant_drift if item not in base.undocumented_invariants],
            undocumented_purpose_fragments=list(base.undocumented_purpose_fragments),
            undocumented_authority=list(base.undocumented_authority),
            undocumented_context=list(base.undocumented_context),
            undocumented_constraints=list(base.undocumented_constraints),
            founder_only_knowledge=list(base.founder_only_knowledge),
            hidden_items=list(base.hidden_items),
            pf_threats=list(base.pf_threats),
            missing_purpose_artifacts=list(base.missing_purpose_artifacts),
            invariant_drift_candidates=invariant_drift,
            semantic_mismatches=semantic_mismatches,
            lineage_gaps=lineage_gaps,
            lineage_links=lineage_links,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=HIDDENNESS_STATE_ID,
                state_type="hiddenness",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(HIDDENNESS_STATE_ID, "hiddenness", state)
        self._emit_receipt_v2(state)
        sync_hiddenness_state_to_work_queue(
            self.csr,
            state,
            source="HiddennessRuntimeV2",
            now=now,
        )
        if trigger_amendments:
            maybe_trigger_hiddenness_amendment(self.csr, state, opened_at=now)
            self._maybe_trigger_purpose_amendment(state)
        return state

    def _maybe_trigger_purpose_amendment(self, state: HiddennessStateV2) -> None:
        if not state.hidden_items:
            return
        from constitutional.purpose.purpose_continuity_amendment import (
            maybe_trigger_purpose_continuity_amendment,
        )
        from constitutional.runtime.mission_fidelity_runtime import load_mission_fidelity_state

        try:
            mf_state = load_mission_fidelity_state(self.csr)
        except KeyError:
            return
        merged = mf_state.model_copy(
            update={
                "failed_surfaces": list(
                    dict.fromkeys(mf_state.failed_surfaces + state.pf_threats)
                ),
                "missing_purpose_artifacts": list(
                    dict.fromkeys(mf_state.missing_purpose_artifacts + state.missing_items)
                ),
            }
        )
        maybe_trigger_purpose_continuity_amendment(
            self.csr,
            merged,
            opened_at=state.snapshot_at,
        )

    def _detect_invariant_drift(self) -> list[str]:
        by_name: dict[str, list[str]] = {}
        for record in self.invariant_registry.invariants:
            by_name.setdefault(record.name, []).append(
                normalize_invariant_text(record.description)
            )

        drift: list[str] = []
        for name, descriptions in by_name.items():
            unique = {desc for desc in descriptions if desc}
            if len(unique) <= 1:
                continue
            ordered = sorted(unique)
            drift.append(f"{name}: registry vs receipt meaning divergence ({' | '.join(ordered[:2])})")

        registry_names = self.invariant_registry.names()
        receipt_only = {
            record.name
            for record in self.invariant_registry.invariants
            if record.source.startswith("receipt:")
            and record.name not in self.csr.invariant_registry
        }
        for name in sorted(receipt_only):
            drift.append(f"{name}: declared in receipts but absent from invariant registry")

        if PURPOSE_CONTINUITY_INVARIANT in registry_names:
            purpose_text = self.purpose_registry.combined_text()
            purpose_inv = next(
                (
                    record.description
                    for record in self.invariant_registry.invariants
                    if record.name == PURPOSE_CONTINUITY_INVARIANT
                ),
                "",
            )
            if purpose_text and purpose_inv:
                if "continuity" in purpose_text and "continuity" not in purpose_inv.lower():
                    drift.append(
                        f"{PURPOSE_CONTINUITY_INVARIANT}: purpose narrative mentions continuity "
                        "but registry wording diverges"
                    )
        return drift

    def _detect_semantic_mismatch(self) -> list[str]:
        purpose_text = self.purpose_registry.combined_text()
        if not purpose_text:
            return ["No purpose fragments available for semantic comparison"]

        policy_text = self.policy_graph.constraint_text()
        mismatches: list[str] = []

        purpose_tokens = {token for token in purpose_protection_tokens() if token in purpose_text}
        throughput_tokens = {
            token for token in throughput_optimization_tokens() if token in policy_text
        }
        if purpose_tokens and throughput_tokens:
            mismatches.append(
                "Purpose emphasizes protection/continuity while policy graph encodes "
                f"throughput-oriented constraints ({', '.join(sorted(throughput_tokens))})"
            )

        if "minority" in purpose_text and "batch" in policy_text:
            mismatches.append(
                "Purpose references minority protection but policy graph includes batch optimization"
            )

        mission_fragments = [
            fragment for fragment in self.purpose_registry.fragments if fragment.source == "mission_statement"
        ]
        charter_nodes = [
            node for node in self.policy_graph.nodes if node.kind == "runtime_charter"
        ]
        if mission_fragments and not charter_nodes:
            mismatches.append("Mission is declared but no runtime charter policies are encoded")

        receipt_policies = sum(1 for node in self.policy_graph.nodes if node.kind == "receipt_policy")
        charter_count = sum(1 for node in self.policy_graph.nodes if node.kind == "runtime_charter")
        if receipt_policies > charter_count + 5:
            mismatches.append(
                f"Receipt policy surface ({receipt_policies}) exceeds encoded runtime charter coverage"
            )
        return mismatches

    def _find_lineage_gaps(self) -> list[str]:
        gaps: list[str] = []
        observed_state_ids = {
            receipt.inputs.request_id
            for receipt in self.csr.get_all_receipts()
            if receipt.inputs.request_id
        }

        state_loaders: list[tuple[str, type]] = [
            (HIDDENNESS_STATE_ID, HiddennessStateV2),
            (MISSION_FIDELITY_STATE_ID, MissionFidelityState),
            (DASHBOARD_STATE_ID, ReconstructabilityDashboardState),
            (FITNESS_STATE_ID, ReconstructabilityFitnessState),
        ]
        for state_id, model in state_loaders:
            try:
                self.csr.get_domain_doc(state_id, model)
            except KeyError:
                continue
            if state_id not in observed_state_ids:
                gaps.append(f"{state_id} has state but no observation receipt lineage")

        for receipt in self.csr.get_all_receipts():
            if not receipt.continuity.previous_receipt_id and receipt.action_type != "bootstrap":
                gaps.append(f"Receipt {receipt.receipt_id} has no previous lineage link")
        return gaps[:20]

    def _build_lineage_links(self, version: int) -> HiddennessLineageLinksV2:
        related_states: list[str] = []
        state_loaders: list[tuple[str, type]] = [
            (MISSION_FIDELITY_STATE_ID, MissionFidelityState),
            (DASHBOARD_STATE_ID, ReconstructabilityDashboardState),
            (FITNESS_STATE_ID, ReconstructabilityFitnessState),
        ]
        for state_id, model in state_loaders:
            try:
                doc = self.csr.get_domain_doc(state_id, model)
                doc_version = getattr(doc, "version", None)
                if doc_version is not None:
                    related_states.append(f"{state_id}@v{doc_version}")
                else:
                    related_states.append(state_id)
            except KeyError:
                continue
        related_states.append(f"{HIDDENNESS_STATE_ID}@v{version}")

        related_receipts: list[str] = []
        for receipt in reversed(self.csr.get_all_receipts()):
            action = getattr(receipt, "action_type", "")
            if action in {
                "purpose_continuity",
                "mission_fidelity_test",
                "reconstructability_fitness",
                "hiddenness_audit",
            }:
                related_receipts.append(receipt.receipt_id)
            if len(related_receipts) >= 8:
                break

        amendment_candidates = [HIDDENNESS_AMENDMENT_TEMPLATE_ID]
        if self.purpose_registry.fragments:
            amendment_candidates.append(PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID)

        return HiddennessLineageLinksV2(
            related_states=related_states,
            related_receipts=list(related_receipts),
            amendment_candidates=amendment_candidates,
        )

    def _emit_receipt_v2(self, state: HiddennessStateV2) -> None:
        receipt = build_hiddenness_receipt_v2(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash
