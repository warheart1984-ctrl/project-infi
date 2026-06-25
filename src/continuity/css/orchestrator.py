"""CSS-1 orchestrator — unifies all nine continuity stack layers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css.cer import CER1CycleResult, run_cer_cycle
from src.continuity.css.fap import FAP1Assessment, FounderInsight, FounderResponse, SuccessorInsight, assess_fap1
from src.continuity.css.fcrm import FCRM1Assessment, assess_fcrm1
from src.continuity.css.sec import SEC1Assessment
from src.continuity.css.spec import (
    CSS1_REFERENCE,
    FULL_CONTINUITY_REQUIREMENTS,
    PHASE_3_5_LABEL,
    PHASE_4_LABEL,
    UNIFIED_CONTINUITY_CONDITION,
    ContinuityStackPhase,
)
from src.continuity.css.ssde import SSDE1Assessment, assess_ssde1_from_ce_log
from src.continuity.stewardability.drift_detector import DriftSignal
from src.continuity.stewardability.lineage_event_log import LineageEventLog
from src.continuity.stewardability.register import StewardAbilityRegister
from src.cos1.accumulation.ae_json_schema import AccumulationEventLog
from src.cos1.continuity_engine.state_model import ContinuityStateVector


class CSS1Assessment(BaseModel):
    reference: str = CSS1_REFERENCE
    unified_condition: str = UNIFIED_CONTINUITY_CONDITION
    phase: ContinuityStackPhase = "propagation"
    phase_label: str = ""
    cer: CER1CycleResult
    fcrm: FCRM1Assessment
    ssde: SSDE1Assessment
    adm1: "ADM1Assessment"
    k4: "K4Assessment"
    fap: FAP1Assessment | None = None
    steward_count: int = 0
    full_continuity_validated: bool = False
    requirements_met: dict[str, bool] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    standing_summary: list[str] = Field(default_factory=list)


def resolve_stack_phase(
    cer: CER1CycleResult,
    sec1: SEC1Assessment,
    steward_count: int,
    full_continuity: bool,
) -> tuple[ContinuityStackPhase, str]:
    thresholds = cer.ce1.thresholds
    if full_continuity:
        return "full_continuity", "Full Continuity — all CSS-1 validation gates passed."

    if sec1.steward_emergence_met or steward_count > 0:
        if steward_count >= 2:
            return "stewardability", "Phase 5 — Stewardability (stewards without founders)."
        return "steward_emergence", PHASE_4_LABEL

    if thresholds.accumulation.met and thresholds.propagation.met and thresholds.convergence.met:
        return "pre_stewardship_compounding", PHASE_3_5_LABEL

    if thresholds.accumulation.met:
        return "accumulation", "Phase 3 — Accumulation (compounding)."

    if thresholds.convergence.met:
        return "convergence", "Phase 2 — Convergence (reality-tracking)."

    return "propagation", "Phase 1 — Propagation (transmission)."


def assess_css1(
    lineage_log: LineageEventLog,
    accumulation_log: AccumulationEventLog,
    steward_register: StewardAbilityRegister,
    *,
    prior_state: ContinuityStateVector | None = None,
    drift_signals: list[DriftSignal] | None = None,
    founder: FounderInsight | None = None,
    successor: SuccessorInsight | None = None,
    founder_response: FounderResponse | None = None,
    disambiguate: bool = True,
) -> CSS1Assessment:
    """Run the full CSS-1 stack assessment."""
    cer = run_cer_cycle(
        lineage_log,
        accumulation_log,
        steward_register,
        prior_state=prior_state,
        disambiguate=disambiguate,
    )

    fcrm = assess_fcrm1(steward_register, drift_signals)
    founder_model = founder or FounderInsight(id="founder-default", text="", integration_score=0.5)
    ssde = assess_ssde1_from_ce_log(cer.ce_log, founder_model)

    fap: FAP1Assessment | None = None
    if successor is not None and founder_response is not None:
        fap = assess_fap1(founder_model, successor, founder_response)

    steward_count = len(steward_register.emergence_events())
    sec1 = cer.sec1
    adm1 = cer.adm1
    k4 = cer.k4

    requirements: dict[str, bool] = {
        FULL_CONTINUITY_REQUIREMENTS[0]: cer.ce1.thresholds.propagation.met,
        FULL_CONTINUITY_REQUIREMENTS[1]: cer.ce1.thresholds.convergence.met,
        FULL_CONTINUITY_REQUIREMENTS[2]: cer.ce1.thresholds.accumulation.met,
        FULL_CONTINUITY_REQUIREMENTS[3]: sec1.steward_emergence_met,
        FULL_CONTINUITY_REQUIREMENTS[4]: fap.founder_acceptance_met if fap else False,
        FULL_CONTINUITY_REQUIREMENTS[5]: not fcrm.high_risk,
        FULL_CONTINUITY_REQUIREMENTS[6]: not adm1.high_drift,
        FULL_CONTINUITY_REQUIREMENTS[7]: cer.ligp.identity_preserved,
        FULL_CONTINUITY_REQUIREMENTS[8]: k4.satisfied,
        FULL_CONTINUITY_REQUIREMENTS[9]: ssde.surpassment_detected,
        FULL_CONTINUITY_REQUIREMENTS[10]: steward_count >= 1,
    }

    full = all(requirements.values())
    phase, phase_label = resolve_stack_phase(cer, sec1, steward_count, full)

    blockers: list[str] = []
    for label, met in requirements.items():
        if not met:
            blockers.append(f"Not met: {label}")

    standing = _build_standing_summary(cer, sec1, ssde, fcrm, steward_count, phase_label)

    return CSS1Assessment(
        phase=phase,
        phase_label=phase_label,
        cer=cer,
        fcrm=fcrm,
        ssde=ssde,
        adm1=adm1,
        k4=k4,
        fap=fap,
        steward_count=steward_count,
        full_continuity_validated=full,
        requirements_met=requirements,
        blockers=blockers if not full else [],
        standing_summary=standing,
    )


def _build_standing_summary(
    cer: CER1CycleResult,
    sec1: SEC1Assessment,
    ssde: SSDE1Assessment,
    fcrm: FCRM1Assessment,
    steward_count: int,
    phase_label: str,
) -> list[str]:
    adm1 = cer.adm1
    k4 = cer.k4
    state = cer.ce1.state
    crossed: list[str] = []
    if cer.ce1.thresholds.propagation.met:
        crossed.append("Propagation (PT-3)")
    if cer.ce1.thresholds.convergence.met:
        crossed.append("Convergence (CT-2)")
    if cer.ce1.thresholds.accumulation.met:
        crossed.append("Accumulation (MAT-3)")
    if cer.ligp.identity_preserved:
        crossed.append("Identity preservation (LIGP K1–K3)")
    if k4.satisfied:
        crossed.append("Reconstructability (K4)")
    if cer.ce1.compounding_dominance and cer.ce1.compounding_dominance.dominance_holds:
        crossed.append("Compounding dominance")
    if steward_count > 0:
        crossed.append("Governance reasoning (steward emergence events)")

    lines = [
        f"Current phase: {phase_label}",
        f"CE(t) = (P={state.P}, C={state.C}, A={state.A})",
        f"Crossed: {', '.join(crossed) if crossed else 'early propagation'}",
        f"SED-1: {sec1.steward_emergence_met}",
        f"K4 reconstructability: {k4.satisfied}",
        f"ADM-1 drift score: {adm1.accumulation_drift_score} (high={adm1.high_drift})",
        f"SSDE-1 surpassment: {ssde.surpassment_detected}",
        f"FCRM-1 risk: {fcrm.risk_score} (high={fcrm.high_risk})",
    ]
    if not ssde.surpassment_detected:
        lines.append(
            "Missing ingredient: successor A3/A4 insight exceeding founder — then FAP-1 recognition."
        )
    elif not steward_count:
        lines.append(
            "Structural A3/A4 may exist; full continuity still requires FAP-1 recognition and stewards."
        )
    return lines
