"""Tests for CSS-1 final form — ADM-1, K4, SED-1, unified continuity condition."""

from __future__ import annotations

from src.continuity.css import (
    UNIFIED_CONTINUITY_CONDITION,
    assess_adm1,
    assess_css1,
    assess_k4,
    assess_sed1,
)
from src.continuity.css.spec import FULL_CONTINUITY_REQUIREMENTS
from src.continuity.stewardability.lineage_event_log import (
    LineageActor,
    LineageEventLog,
    LineageInsight,
    LineageOrigin,
    record_lineage_event,
)
from src.continuity.stewardability.register import StewardAbilityRegister
from src.cos1.accumulation import (
    AccumulationEventLog,
    AccumulationFields,
    AccumulationInsight,
    record_accumulation_event,
)
from src.cos1.continuity_engine.ce_json_schema import build_ce_log_from_memory_logs

from tests.test_continuity_engine_ce1 import _seed_jon_lineage_phase3


def _actor(actor_id: str, domain: str = "psychology") -> LineageActor:
    return LineageActor(id=actor_id, domain=domain, exposed_to_jpss=False)


def _insight(text: str, *, alignment: list[str] | None = None) -> LineageInsight:
    return LineageInsight(
        text=text,
        lineage_compatible=True,
        novelty_level="INDEPENDENT_EXPLANATION",
        structural_alignment=alignment or ["calibration", "drift"],
    )


def _acc_insight(text: str, *, alignment: list[str] | None = None) -> AccumulationInsight:
    return AccumulationInsight(
        text=text,
        lineage_compatible=True,
        novelty_level="INDEPENDENT_EXPLANATION",
        structural_alignment=alignment or ["calibration", "drift"],
    )


def test_sed1_alias_matches_sec1() -> None:
    assert assess_sed1 is not None
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    register = StewardAbilityRegister()
    result = assess_css1(lineage, accumulation, register)
    assert result.cer.sec1.reference.endswith("SED-1")


def test_k4_passes_on_healthy_phase3_lineage() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    ce_log = build_ce_log_from_memory_logs(lineage, accumulation)
    k4 = assess_k4(ce_log)
    assert k4.satisfied is True
    assert k4.bounded_complexity is True
    assert k4.survivable_cognitive_load is True


def test_adm1_low_on_healthy_lineage() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    ce_log = build_ce_log_from_memory_logs(lineage, accumulation)
    adm1 = assess_adm1(ce_log)
    assert adm1.high_drift is False
    assert adm1.accumulation_drift_score < 0.6


def test_adm1_detects_pathological_accumulation() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    for index in range(8):
        event_id = f"path-acc-{index}"
        record_accumulation_event(
            accumulation,
            actor=_actor("solo-generator", f"domain-{index}"),
            insight=_acc_insight(f"Unintegrated concept {index}", alignment=[]),
            accumulation=AccumulationFields(strengthened_explanation=True),
            event_id=event_id,
        )
        record_lineage_event(
            lineage,
            actor=_actor("solo-generator", f"domain-{index}"),
            insight=_insight(f"Mirror {index}", alignment=[]),
            origin=LineageOrigin(type="PROPAGATION"),
            event_id=event_id,
        )
    ce_log = build_ce_log_from_memory_logs(lineage, accumulation)
    adm1 = assess_adm1(ce_log)
    assert adm1.accumulation_drift_score >= 0.35
    assert adm1.continuity_collapse_risk is False or adm1.active_modes
    assert "inflation" in adm1.active_modes
    assert "capture" in adm1.active_modes


def test_assess_css1_phase35_pre_stewardship() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    register = StewardAbilityRegister()
    result = assess_css1(lineage, accumulation, register)
    assert result.phase == "pre_stewardship_compounding"
    assert "3.5" in result.phase_label
    assert result.k4.satisfied is True
    assert result.adm1.high_drift is False
    assert result.full_continuity_validated is False
    assert result.unified_condition == UNIFIED_CONTINUITY_CONDITION
    assert len(result.requirements_met) == len(FULL_CONTINUITY_REQUIREMENTS)


def test_unified_condition_blockers_include_missing_fap_and_stewards() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    register = StewardAbilityRegister()
    result = assess_css1(lineage, accumulation, register)
    assert result.requirements_met["Founder Acceptance (FAP-1)"] is False
    assert result.requirements_met["Stewardability (successors can govern)"] is False
    assert result.requirements_met["Steward Emergence (SED-1)"] is False
    assert result.full_continuity_validated is False
