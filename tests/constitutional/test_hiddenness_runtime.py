"""Hiddenness runtime, interactive mission fidelity, and purpose governance tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from constitutional.core.articles import (
    HIDDENNESS_AMENDMENT_TEMPLATE_ID,
    HIDDENNESS_RECEIPT_INVARIANT,
    INVARIANT_INTERPRETATION_SUCCESS_SCORE,
    MISSION_LEGIBILITY_MIN_SCORE,
    PURPOSE_CONTINUITY_INDEX_THRESHOLD,
    PURPOSE_CONTINUITY_INVARIANT,
    RED_ZONE_PF_THREAT_COUNT,
)
from constitutional.runtime.dashboard_governance import apply_dashboard_to_governance_gate
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.hiddenness_runtime import (
    HIDDENNESS_STATE_ID,
    HiddennessCategory,
    HiddennessRuntime,
    load_hiddenness_state,
)
from constitutional.runtime.mission_fidelity_interactive import (
    MISSION_FIDELITY_QUESTIONS,
    emit_purpose_continuity_receipt,
    load_mission_fidelity_interactive,
    submit_mission_fidelity_answers,
)
from constitutional.runtime.mission_fidelity_runtime import (
    MISSION_STATEMENT_STATE_ID,
    MissionFidelityRuntime,
    MissionStatementState,
)
from constitutional.runtime.purpose_governance import (
    evaluate_article_p_compliance,
    purpose_in_red_zone,
    succession_purpose_ready,
)
from constitutional.runtime.receipts_v2 import is_receipt_v2_complete
from constitutional.runtime.reconstructability_dashboard import (
    ReconstructabilityDashboardState,
    build_reconstructability_dashboard,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from operator_kernel.succession import succession_blocked, succession_ready


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    clear_domain_memory_index()
    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def _seed_mission(csr: ConstitutionalStateRuntime) -> None:
    csr.put_domain_doc(
        MISSION_STATEMENT_STATE_ID,
        "mission_statement",
        MissionStatementState(
            text=(
                "Enable independent stewards to reconstruct and operate governed systems "
                "without founder assistance while preserving constitutional meaning."
            ),
            invariant_rationale="Purpose must survive steward discontinuity.",
            founding_context=(
                "Born from observer-reproducible proof requirements and constitutional substrate design."
            ),
        ),
    )


def _seed_salience_ledger_for_succession(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.priors.drift_detector import PriorDriftDetector, StewardPriorMap
    from constitutional.priors.judgment_runtime import seed_passing_prior_judgment
    from constitutional.priors.ledger import PriorEntry, load_prior_ledger, save_prior_ledger
    from constitutional.salience.continuity_runtime import (
        SalienceContinuityRuntime,
        StewardKnowledgeIndex,
        append_salience_entry,
    )
    from constitutional.salience.ledger import SalienceEntry
    from constitutional.salience.perceptual_drift import PerceptualDriftDetector, StewardSalienceMap
    from constitutional.significance.decision_environment_runtime import (
        DecisionEnvironmentRuntime,
        iter_decision_ids,
    )
    from constitutional.significance.stewardship_context_ledger import (
        StewardshipContextEntry,
        append_stewardship_context,
    )
    from constitutional.stewardship.artifact_index import default_artifact_index

    now = datetime.now(UTC).replace(microsecond=0)
    artifact_ids: list[str] = []
    for artifact in default_artifact_index().tier_0_and_1():
        artifact_ids.append(artifact.id)
        append_salience_entry(
            csr,
            SalienceEntry(
                timestamp=now,
                decision_id="succession_seed",
                artifact_id=artifact.id,
                primary_signals=["constitutional_continuity"],
                steward_id="steward",
            ),
        )

    SalienceContinuityRuntime(
        csr,
        steward_knowledge_index=StewardKnowledgeIndex(set(artifact_ids)),
    ).run()
    PerceptualDriftDetector(
        csr,
        steward_salience_map=StewardSalienceMap(primary_signals=["constitutional_continuity"]),
    ).run()

    prior_ledger = load_prior_ledger(csr)
    prior_ledger.append(
        PriorEntry(
            timestamp=now,
            decision_id="succession_seed",
            artifact_id=artifact_ids[0] if artifact_ids else None,
            expected_signals=["constitutional_continuity"],
            expected_risks=["constitutional capture"],
            assumed_stabilities=["tier 0 invariants"],
            assumed_volatilities=["operational urgency"],
            feared_failures=["constitutional_continuity"],
            steward_id="steward",
        )
    )
    save_prior_ledger(csr, prior_ledger)
    PriorDriftDetector(
        csr,
        steward_priors=StewardPriorMap(
            expected_signals=["constitutional_continuity"],
            expected_risks=["constitutional capture"],
            assumed_stabilities=["tier 0 invariants"],
            assumed_volatilities=["operational urgency"],
            feared_failures=["constitutional_continuity"],
        ),
    ).run()
    seed_passing_prior_judgment(csr)
    for decision_id in iter_decision_ids(csr):
        append_stewardship_context(
            csr,
            StewardshipContextEntry(
                timestamp=now,
                decision_id=decision_id,
                signals_considered=["constitutional_continuity"],
                risks_salient=["constitutional capture"],
                constraints_active=["tier 0 invariants"],
                environmental_factors=["stable governance"],
                steward_id="steward",
            ),
        )
    DecisionEnvironmentRuntime(csr).run()


def _all_answers() -> dict[str, str]:
    return {
        q.question_id: (
            f"Steward articulation for {q.prompt} — sufficient detail for cold-start continuity."
        )
        for q in MISSION_FIDELITY_QUESTIONS
    }


def test_hiddenness_detects_missing_mission_and_interactive(csr: ConstitutionalStateRuntime) -> None:
    state = HiddennessRuntime(csr).run_audit()
    assert state.hidden_items
    categories = {item.category for item in state.hidden_items}
    assert HiddennessCategory.MISSING_PURPOSE_RECEIPT in categories
    receipts = csr.observation_receipts_for(HIDDENNESS_STATE_ID)
    assert len(receipts) == 1
    assert is_receipt_v2_complete(receipts[0])
    loaded = load_hiddenness_state(csr)
    assert loaded.version == 1


def test_interactive_mission_fidelity_unanswered_is_pf_threat(csr: ConstitutionalStateRuntime) -> None:
    state = submit_mission_fidelity_answers(csr, {"why_exist": "too short"})
    assert not state.interactive_passed
    assert state.unanswered_pf_threats
    assert len(state.unanswered_question_ids()) == len(MISSION_FIDELITY_QUESTIONS)


def test_interactive_mission_fidelity_pass_and_receipt(csr: ConstitutionalStateRuntime) -> None:
    state = submit_mission_fidelity_answers(csr, _all_answers())
    assert state.interactive_passed
    assert load_mission_fidelity_interactive(csr) is not None
    receipt = emit_purpose_continuity_receipt(csr, state)
    assert receipt.purpose_continuity.kind == "PurposeContinuity"
    assert receipt.purpose_continuity.invariant == PURPOSE_CONTINUITY_INVARIANT
    assert is_receipt_v2_complete(receipt)


def test_hiddenness_fewer_gaps_after_externalization(csr: ConstitutionalStateRuntime) -> None:
    _seed_mission(csr)
    submit_mission_fidelity_answers(csr, _all_answers())
    MissionFidelityRuntime(csr).run_test()
    state = HiddennessRuntime(csr).run_audit()
    assert state.hiddenness_index > 0.5
    assert len(state.hidden_items) < len(MISSION_FIDELITY_QUESTIONS)


def test_hiddenness_receipt_v1_shape(csr: ConstitutionalStateRuntime) -> None:
    state = HiddennessRuntime(csr).run_audit()
    receipts = csr.observation_receipts_for(HIDDENNESS_STATE_ID)
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt.receipt_id.startswith("hiddenness-")
    assert receipt.hiddenness.kind == "Hiddenness"
    assert receipt.hiddenness.invariant == HIDDENNESS_RECEIPT_INVARIANT
    assert receipt.runtime == "HiddennessRuntime"
    if state.failed_surfaces:
        assert all(code.startswith("H-F") for code in receipt.hiddenness.failed_surfaces)
        assert receipt.hiddenness.failed_surfaces[0] == "H-F4"


def test_hiddenness_amendment_triggers_on_breach(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_amendment import (
        HIDDENNESS_AMENDMENT_TRIGGERS_STATE_ID,
        load_hiddenness_amendment_triggers,
    )

    HiddennessRuntime(csr).run_audit()
    triggers = load_hiddenness_amendment_triggers(csr)
    assert triggers.triggers
    assert triggers.triggers[0].template_id == HIDDENNESS_AMENDMENT_TEMPLATE_ID


def test_cold_start_hiddenness_section_fails_with_hidden_items(
    csr: ConstitutionalStateRuntime,
) -> None:
    from constitutional.hiddenness.cold_start_hiddenness import (
        cold_start_hiddenness_passes,
        load_cold_start_hiddenness_state,
    )

    HiddennessRuntime(csr).run_audit()
    ok, reasons = cold_start_hiddenness_passes(csr)
    assert not ok
    assert reasons
    section = load_cold_start_hiddenness_state(csr)
    assert section is not None
    assert not section.section_passed
    assert section.failed_hf_surfaces


def test_cold_start_hiddenness_section_passes_when_clean(
    csr: ConstitutionalStateRuntime,
) -> None:
    from constitutional.hiddenness.cold_start_hiddenness import cold_start_hiddenness_passes
    from constitutional.runtime.survivability_amendment import cold_start_steward_passes

    _seed_mission(csr)
    submit_mission_fidelity_answers(csr, _all_answers())
    MissionFidelityRuntime(csr).run_test()
    emit_purpose_continuity_receipt(csr, load_mission_fidelity_interactive(csr))
    HiddennessRuntime(csr).run_audit()
    ok, reasons = cold_start_hiddenness_passes(csr)
    assert ok, reasons
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    assert cold_start_steward_passes(dashboard, csr=csr)


def test_succession_blocked_by_hiddenness(csr: ConstitutionalStateRuntime) -> None:
    hiddenness = HiddennessRuntime(csr).run_audit()
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    dashboard = dashboard.model_copy(
        update={
            "steward_independence_score": 0.85,
            "system_survivability_score": 0.85,
            "founder_dependency_index": 0.15,
            "reconstructability_fitness_score": 0.85,
            "implicit_assumptions_required": 0,
            "active_threats": [],
        }
    )
    blocked, reasons = succession_blocked(
        dashboard,
        interactive_passed=True,
        csr=csr,
        hiddenness=hiddenness,
    )
    assert blocked
    assert any("hiddenness" in reason for reason in reasons)


def test_governance_blocks_on_purpose_breach(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    decision = apply_dashboard_to_governance_gate(dashboard)
    assert not decision.allow
    assert decision.article_h is not None
    assert decision.article_h.constitutional_breach
    assert decision.article_p is not None
    assert decision.article_p.constitutional_breach


def test_article_h_hiddenness_index_and_hf_surfaces(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF

    state = HiddennessRuntime(csr).run_scan()
    assert state.hiddenness_index < 1.0
    assert HF.HIDDEN_PURPOSE_FRAGMENT in state.failed_surfaces
    assert state.undocumented_purpose_fragments
    loaded = load_hiddenness_state(csr)
    assert loaded.hiddenness_index == state.hiddenness_index
    assert loaded.explicitness_score == state.hiddenness_index


def test_governance_blocks_on_hiddenness_breach(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.runtime.hiddenness_governance import evaluate_article_h_compliance

    HiddennessRuntime(csr).run_scan()
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    article_h = evaluate_article_h_compliance(dashboard)
    assert article_h.constitutional_breach
    assert article_h.undocumented_purpose_fragment_count > 0
    decision = apply_dashboard_to_governance_gate(dashboard, article_h=article_h)
    assert not decision.allow
    assert decision.article_h is not None


def test_succession_blocked_without_interactive_purpose(csr: ConstitutionalStateRuntime) -> None:
    _seed_mission(csr)
    MissionFidelityRuntime(csr).run_test()
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    blocked, reasons = succession_blocked(dashboard)
    assert blocked
    assert "mission_fidelity_interactive_not_passed" in reasons


def test_succession_unblocked_with_full_purpose_stack(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
    from constitutional.significance.significance_judgment_runtime import (
        seed_passing_significance_judgment,
    )

    _seed_mission(csr)
    submit_mission_fidelity_answers(csr, _all_answers())
    MissionFidelityRuntime(csr).run_test()
    HiddennessRuntime(csr).run_audit()
    seed_passing_significance_judgment(csr)
    seed_passing_salience_judgment(csr)
    _seed_salience_ledger_for_succession(csr)
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    dashboard = dashboard.model_copy(
        update={
            "steward_independence_score": 0.85,
            "system_survivability_score": 0.85,
            "founder_dependency_index": 0.15,
            "reconstructability_fitness_score": 0.85,
            "implicit_assumptions_required": 0,
            "active_threats": [],
        }
    )
    purpose_ok, reasons = succession_purpose_ready(dashboard, interactive_passed=True)
    assert purpose_ok, reasons
    hiddenness = load_hiddenness_state(csr)
    blocked, block_reasons = succession_blocked(dashboard, csr=csr, hiddenness=hiddenness)
    assert not blocked, block_reasons
    assert succession_ready(
        dashboard,
        interactive_passed=True,
        csr=csr,
        hiddenness=hiddenness,
    )


def test_purpose_red_zone_threshold() -> None:
    from constitutional.runtime.purpose_failures import PurposeFailureClass as PF

    assert not purpose_in_red_zone([PF.MISSION_AMNESIA])
    assert purpose_in_red_zone([PF.MISSION_AMNESIA, PF.PURPOSE_DRIFT, PF.TELOS_INVERSION])
    assert RED_ZONE_PF_THREAT_COUNT == 3


def test_hiddenness_runtime_v2_semantic_receipt(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_runtime_v2 import (
        HiddennessRuntimeV2,
        load_hiddenness_state_v2,
    )
    from constitutional.runtime.hiddenness_governance import apply_hiddenness_to_governance_gate

    state = HiddennessRuntimeV2(csr).run_scan()
    assert isinstance(state.invariant_drift_candidates, list)
    assert isinstance(state.semantic_mismatches, list)
    assert isinstance(state.lineage_gaps, list)
    assert state.lineage_links.related_states
    assert HIDDENNESS_AMENDMENT_TEMPLATE_ID in state.lineage_links.amendment_candidates

    loaded = load_hiddenness_state_v2(csr)
    assert loaded.version == state.version
    assert loaded.semantic_mismatches == state.semantic_mismatches

    receipts = csr.observation_receipts_for(HIDDENNESS_STATE_ID)
    v2_receipts = [r for r in receipts if r.receipt_id.startswith("hiddenness-v2-")]
    assert v2_receipts
    receipt = v2_receipts[-1]
    assert receipt.hiddenness.kind == "HiddennessV2"
    assert receipt.runtime == "HiddennessRuntimeV2"
    assert receipt.hiddenness.lineage_links is not None
    assert is_receipt_v2_complete(receipt)

    gate = apply_hiddenness_to_governance_gate(state)
    assert gate is not None
    if state.hiddenness_index < 0.70:
        assert not gate.allow
    elif any(
        surface.value.startswith("H-F2")
        or surface.value.startswith("H-F4")
        or surface.value.startswith("H-F5")
        for surface in state.failed_surfaces
    ):
        assert not gate.allow


def test_hiddenness_v2_detects_invariant_drift(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessRuntimeV2

    csr.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Purpose must survive steward change.")
    _seed_mission(csr)
    state = HiddennessRuntimeV2(csr).run_scan()
    assert state.semantic_mismatches or state.invariant_drift_candidates or state.hidden_items


def test_hiddenness_panel_surfaces_findings(csr: ConstitutionalStateRuntime) -> None:
    from io import StringIO

    from constitutional.hiddenness.hiddenness_panel import format_hiddenness_panel, hiddenness_panel
    from constitutional.hiddenness.hiddenness_precursors import (
        downstream_pf_threats,
        downstream_rf_threats,
    )
    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessRuntimeV2

    state = HiddennessRuntimeV2(csr).run_scan()
    text = format_hiddenness_panel(state)
    assert "HIDDENNESS PANEL" in text
    assert "Hiddenness Index:" in text
    assert "meta-runtime" in text

    buf = StringIO()
    hiddenness_panel(state, stream=buf)
    assert buf.getvalue() == text

    if state.failed_surfaces:
        assert downstream_rf_threats(state.failed_surfaces)
        assert downstream_pf_threats(state.failed_surfaces)


def test_render_constitutional_dashboard(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.dashboard.constitutional_dashboard import format_constitutional_dashboard
    from operator_kernel.heartbeat import run_constitutional_pressure_cycle

    _seed_mission(csr)
    now = datetime.now(UTC).replace(microsecond=0)
    run_constitutional_pressure_cycle(now, csr)

    text = format_constitutional_dashboard(csr)
    assert "CONSTITUTIONAL DASHBOARD" in text
    assert "System Survivability:" in text
    assert "Reconstructability Fitness:" in text
    assert "Purpose Continuity Index:" in text
    assert "HIDDENNESS PANEL" in text
    assert "HIDDENNESS WORK QUEUE" in text
    assert "R-F Threats:" in text
    assert "P-F Threats:" in text
    assert "H-F Threats:" in text


def test_hiddenness_work_queue_sync_and_dedup(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessRuntimeV2
    from constitutional.hiddenness.hiddenness_work_queue import (
        load_hiddenness_work_queue,
        resolve_hiddenness_work_item,
        stable_work_item_id,
        sync_hiddenness_state_to_work_queue,
    )

    _seed_mission(csr)
    now = datetime.now(UTC).replace(microsecond=0)
    state = HiddennessRuntimeV2(csr).run_scan(snapshot_at=now, trigger_amendments=False)

    queue = load_hiddenness_work_queue(csr)
    if state.implicit_assumptions or state.undocumented_invariants or state.hidden_items:
        assert queue.unresolved_count() > 0

    first_count = queue.unresolved_count()
    later = now.replace(second=min(now.second + 1, 59))
    sync_hiddenness_state_to_work_queue(csr, state, source="HiddennessRuntimeV2", now=later)
    queue = load_hiddenness_work_queue(csr)
    assert queue.unresolved_count() == first_count

    if queue.unresolved():
        item = queue.unresolved()[0]
        resolve_hiddenness_work_item(csr, item.item_id, receipt_id="purpose-continuity-2026-06-23T14:00Z")
        queue = load_hiddenness_work_queue(csr)
        resolved = queue.items[item.item_id]
        assert resolved.status == "resolved"
        assert resolved.resolution_receipt == "purpose-continuity-2026-06-23T14:00Z"
        assert stable_work_item_id(resolved.kind, resolved.description) == item.item_id


def test_hiddenness_pressure_escalates_work_queue(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_amendment import load_hiddenness_amendment_triggers
    from constitutional.hiddenness.hiddenness_pressure import apply_hiddenness_pressure
    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessRuntimeV2
    from constitutional.hiddenness.hiddenness_work_queue import load_hiddenness_work_queue
    from constitutional.runtime.mission_fidelity_runtime import MissionFidelityRuntime
    from constitutional.runtime.reconstructability_dashboard_runtime import (
        ReconstructabilityDashboardRuntime,
    )
    from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessRuntime

    _seed_mission(csr)
    now = datetime.now(UTC).replace(microsecond=0)
    hiddenness = HiddennessRuntimeV2(csr).run_scan(snapshot_at=now, trigger_amendments=False)
    fitness = ReconstructabilityFitnessRuntime(csr).run_audit(snapshot_at=now)
    mission = MissionFidelityRuntime(csr).run_test(snapshot_at=now)
    dashboard = ReconstructabilityDashboardRuntime(csr).update_snapshot(now)

    apply_hiddenness_pressure(csr, hiddenness, fitness, mission, dashboard, opened_at=now)

    queue = load_hiddenness_work_queue(csr)
    if queue.unresolved():
        triggers = load_hiddenness_amendment_triggers(csr)
        assert triggers.triggers

def test_hiddenness_work_queue_panel(csr: ConstitutionalStateRuntime) -> None:
    from io import StringIO

    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessRuntimeV2
    from constitutional.hiddenness.hiddenness_work_queue import (
        format_hiddenness_work_queue_panel,
        hiddenness_work_queue_panel,
        load_hiddenness_work_queue,
    )

    HiddennessRuntimeV2(csr).run_scan(trigger_amendments=False)
    queue = load_hiddenness_work_queue(csr)
    text = format_hiddenness_work_queue_panel(queue)
    assert "HIDDENNESS WORK QUEUE" in text
    assert "Unresolved items:" in text

    buf = StringIO()
    hiddenness_work_queue_panel(queue, stream=buf)
    assert buf.getvalue() == text


def test_fitness_cannot_be_green_with_hiddenness_gaps(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.core.articles import SUCCESSION_MIN_FITNESS
    from constitutional.hiddenness.hiddenness_pressure import apply_hiddenness_to_fitness
    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessStateV2
    from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
    from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState

    now = datetime.now(UTC).replace(microsecond=0)
    fitness = ReconstructabilityFitnessState(
        snapshot_at=now,
        version=1,
        fitness_score=0.95,
        stewardship_readiness_score=0.9,
    )
    hiddenness = HiddennessStateV2(
        snapshot_at=now,
        version=1,
        hiddenness_index=0.5,
        undocumented_invariants=["INV-UNDOCUMENTED"],
        lineage_gaps=["gap:mission_statement"],
    )

    updated = apply_hiddenness_to_fitness(csr, fitness, hiddenness)
    assert updated.fitness_score < SUCCESSION_MIN_FITNESS
    assert RF.LINEAGE_BREAK in updated.failed_surfaces or RF.SEMANTIC_DRIFT in updated.failed_surfaces
    assert any("hiddenness:" in item for item in updated.missing_lineage_links)


def test_mission_fidelity_consumes_hiddenness(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.hiddenness.hiddenness_pressure import apply_hiddenness_to_mission_fidelity
    from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessStateV2
    from constitutional.runtime.mission_fidelity_runtime import MissionFidelityState
    from constitutional.runtime.purpose_failures import PurposeFailureClass as PF

    now = datetime.now(UTC).replace(microsecond=0)
    mission = MissionFidelityState(
        snapshot_at=now,
        version=1,
        purpose_fidelity_score=1.0,
        invariant_interpretation_score=1.0,
        mission_legibility_score=1.0,
        purpose_continuity_index=1.0,
    )
    hiddenness = HiddennessStateV2(
        snapshot_at=now,
        version=1,
        hiddenness_index=0.4,
        undocumented_purpose_fragments=["founding telos fragment"],
        semantic_mismatches=["purpose vs throughput policy"],
    )

    updated = apply_hiddenness_to_mission_fidelity(csr, mission, hiddenness)
    assert PF.PURPOSE_FRAGMENTATION in updated.failed_surfaces
    assert PF.PURPOSE_AMBIGUITY in updated.failed_surfaces
    assert updated.purpose_continuity_index < 1.0
