"""CER-1 — Continuity Engine Runtime (lineage event processing loop)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.lineage_disambiguation import disambiguate_log
from src.continuity.stewardability.lineage_event_log import LineageEvent, LineageEventLog
from src.continuity.stewardability.register import StewardAbilityRegister
from src.continuity.css.ligp import LIGPAssessment, assess_ligp
from src.continuity.css.sec import SEC1Assessment, assess_sec1
from src.cos1.accumulation.ae_json_schema import AccumulationEventLog
from src.cos1.continuity_engine.ce_json_schema import (
    ContinuityEngineEventLog,
    build_ce_log_from_memory_logs,
)
from src.cos1.continuity_engine.engine import CE1Assessment, ContinuityEngine
from src.cos1.continuity_engine.state_model import ContinuityStateVector

CER1_REFERENCE = "Continuity Engine Runtime CER-1"


class CER1CycleResult(BaseModel):
    """Single CER-1 runtime loop iteration."""

    reference: str = CER1_REFERENCE
    ingested_count: int = 0
    classified_propagation: int = 0
    classified_convergence: int = 0
    classified_accumulation: int = 0
    ce1: CE1Assessment
    ligp: LIGPAssessment
    sec1: SEC1Assessment
    adm1: "ADM1Assessment"
    k4: "K4Assessment"
    lineage_log: LineageEventLog
    ce_log: ContinuityEngineEventLog
    notes: list[str] = Field(default_factory=list)


def ingest_lineage_event(
    lineage_log: LineageEventLog,
    event: LineageEvent,
    *,
    disambiguate: bool = True,
) -> LineageEvent:
    """Ingest → classify → append to lineage log."""
    if disambiguate and event.origin.type == "AMBIGUOUS":
        resolved, _ = disambiguate_log([event])
        event = resolved[0]
    lineage_log.append(event)
    return event


def run_cer_cycle(
    lineage_log: LineageEventLog,
    accumulation_log: AccumulationEventLog,
    steward_register: StewardAbilityRegister,
    *,
    prior_state: ContinuityStateVector | None = None,
    disambiguate: bool = True,
) -> CER1CycleResult:
    """
    CER-1 runtime loop:
    ingest → classify → update CE(t) → evaluate invariants → ADM-1 → K4 → governance → emit state.
    """
    working_log = LineageEventLog(events=list(lineage_log.events))
    if disambiguate:
        resolved, _ = disambiguate_log(working_log.events)
        working_log = LineageEventLog(events=resolved)

    ce_log = build_ce_log_from_memory_logs(working_log, accumulation_log)
    engine = ContinuityEngine(prior_state=prior_state)
    ce1 = engine.assess(ce_log, prior_state=prior_state)
    ligp = assess_ligp(ce_log.events)
    from src.continuity.css.adm1 import assess_adm1
    from src.continuity.css.k4 import assess_k4

    adm1 = assess_adm1(ce_log)
    k4 = assess_k4(ce_log)
    sec1 = assess_sec1(ce1.thresholds, steward_register)

    notes = [
        f"P={ce1.state.P}, C={ce1.state.C}, A={ce1.state.A}",
        f"Continuity Mode: {ce1.continuity_mode}",
        f"Identity preserved (LIGP K1–K3): {ligp.identity_preserved}",
        f"K4 reconstructability: {k4.satisfied}",
        f"ADM-1 drift score: {adm1.accumulation_drift_score}",
        f"SED-1: {sec1.steward_emergence_met}",
    ]

    return CER1CycleResult(
        ingested_count=len(working_log.events),
        classified_propagation=len(ce_log.propagation_events()),
        classified_convergence=len(ce_log.convergence_events()),
        classified_accumulation=len(ce_log.accumulation_events()),
        ce1=ce1,
        ligp=ligp,
        adm1=adm1,
        k4=k4,
        sec1=sec1,
        lineage_log=working_log,
        ce_log=ce_log,
        notes=notes,
    )
