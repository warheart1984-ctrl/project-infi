"""Five-Team Continuity Simulation Loop — Gold metrics + chaos fixtures for CRK-1 stress tests."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from simulation.five_team_protocol import (
    CampaignConfig,
    CampaignState,
    RoundProtocolResult,
    build_round_protocol,
    format_attack_log,
    format_drift_report,
    should_stop_campaign,
)
from src.continuity.crk1_compliance import run_static_compliance_report
from src.continuity.css import assess_css1
from src.continuity.ra import (
    AcceptanceEvent,
    SurpassmentCandidate,
    ValidationContext,
    empty_ra_state,
    get_cbcl_ledger,
    propose_change,
    run_rag_loop,
)
from src.continuity.stewardability.lineage_event_log import LineageEventLog
from src.continuity.stewardability.register import StewardAbilityRegister
from src.cos1.accumulation import AccumulationEventLog
from src.cos1.continuity_os import ContinuityOS

TeamRole = Literal["red", "blue", "black", "white", "gold"]


class ChaosScenario(BaseModel):
    """Black Team fixture — adversarial or malformed inputs."""

    name: str
    description: str
    validation_ctx: ValidationContext
    surpassment: SurpassmentCandidate
    acceptance: AcceptanceEvent
    expect_survival: bool = False


class GoldContinuityMetrics(BaseModel):
    """Gold Team instrumentation snapshot."""

    round_id: int
    ce_p: int = 0
    ce_c: int = 0
    ce_a: int = 0
    css_phase: str = ""
    css_phase_label: str = ""
    k4_satisfied: bool = False
    adm_drift_score: float = 0.0
    adm_high_drift: bool = False
    psd_aggregate: float = 0.0
    crk1_compliant: bool = False
    continuity_succeeded: bool = False
    cbcl_entry_count: int = 0
    instrumentality_note: str = ""
    recommendation: Literal["continue", "watch", "halt_integration"] = "continue"
    details: dict[str, Any] = Field(default_factory=dict)


class WhiteRoundVerdict(BaseModel):
    """White Team scoring scaffold (human or agent fills scores)."""

    round_id: int
    system_survived: Literal["yes", "conditional", "no"] = "conditional"
    red_score: int = Field(ge=0, le=10, default=0)
    blue_score: int = Field(ge=0, le=10, default=0)
    black_score: int = Field(ge=0, le=10, default=0)
    crk_amendment_required: bool = False
    notes: list[str] = Field(default_factory=list)


@dataclass
class SimulationRound:
    round_id: int
    invariant_target: str
    subsystem: str
    gold: GoldContinuityMetrics | None = None
    chaos_results: list[dict[str, Any]] = field(default_factory=list)
    white: WhiteRoundVerdict | None = None
    protocol: RoundProtocolResult | None = None


def _seed_lineage_for_round() -> tuple[LineageEventLog, AccumulationEventLog]:
    """Reuse CE-1 Phase 3.5 seed from tests."""
    from tests.test_continuity_engine_ce1 import _seed_jon_lineage_phase3

    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    return lineage, accumulation


def compute_gold_metrics(round_id: int = 1) -> GoldContinuityMetrics:
    """Gold Team — measure continuity health from live CSS-1, RA-COS-1, CRK-1."""
    lineage, accumulation = _seed_lineage_for_round()
    register = StewardAbilityRegister()
    css = assess_css1(lineage, accumulation, register)

    os = ContinuityOS()
    _seed_into_cos(os, lineage, accumulation)
    step = os.step(
        __import__(
            "src.continuity.stewardability.operating_conditions",
            fromlist=["good_conditions"],
        ).good_conditions()
    )

    crk = run_static_compliance_report()
    ra_state = os.memory.state.ra_state if hasattr(os.memory, "state") else empty_ra_state()
    cbcl_count = len(get_cbcl_ledger(ra_state))

    psd = 0.0
    if step.ra_cos1 and step.ra_cos1.state.ledger:
        for entry in step.ra_cos1.state.ledger.values():
            if entry.drift_signals:
                psd = max(psd, entry.drift_signals.aggregate_psd)

    adm = css.adm1.accumulation_drift_score
    k4_ok = css.k4.satisfied

    if not k4_ok or adm >= 0.6 or not crk.get("compliant", False):
        recommendation = "halt_integration" if not k4_ok else "watch"
    elif adm >= 0.35 or css.phase == "pre_stewardship_compounding":
        recommendation = "watch"
    else:
        recommendation = "continue"

    instrumentality = (
        "Transmissible judgment holding — accumulation bounded by K4; "
        "reality validation (VAS-1) required before integration."
        if k4_ok
        else "Reconstructability at risk — accumulation may exceed steward cognitive load."
    )

    state = css.cer.ce1.state
    return GoldContinuityMetrics(
        round_id=round_id,
        ce_p=state.P,
        ce_c=state.C,
        ce_a=state.A,
        css_phase=css.phase,
        css_phase_label=css.phase_label,
        k4_satisfied=k4_ok,
        adm_drift_score=adm,
        adm_high_drift=css.adm1.high_drift,
        psd_aggregate=psd,
        crk1_compliant=bool(crk.get("compliant")),
        continuity_succeeded=step.continuity_succeeded,
        cbcl_entry_count=cbcl_count,
        instrumentality_note=instrumentality,
        recommendation=recommendation,
        details={
            "crk1_report": crk,
            "css_blockers": css.blockers[:5],
            "unified_condition": css.unified_condition,
        },
    )


def _seed_into_cos(
    os: ContinuityOS,
    lineage: LineageEventLog,
    accumulation: AccumulationEventLog,
) -> None:
    os.memory.state.lineage_event_log = lineage
    os.memory.state.accumulation_event_log = accumulation


def inject_chaos_scenarios() -> list[ChaosScenario]:
    """Black Team — predefined entropy injections for automation smoke tests."""
    return [
        ChaosScenario(
            name="acceptance_without_validation",
            description="FAP acceptance with empty VAS-1 context — reality must veto.",
            surpassment=SurpassmentCandidate(
                insight_id="chaos-1",
                explanatory_gain=0.5,
                integrates_primitives=["a", "b"],
                resolves_founder_limitation=True,
                survives_critique=True,
                accumulation_signature="A3",
            ),
            acceptance=AcceptanceEvent(
                acknowledged_superiority=True,
                integrated_into_grammar=True,
                updated_invariants=True,
                relinquished_authority=True,
            ),
            validation_ctx=ValidationContext(),
            expect_survival=False,
        ),
        ChaosScenario(
            name="contradictory_validation",
            description="Strong VAS ctx but adversarial consequence profile.",
            surpassment=SurpassmentCandidate(
                insight_id="chaos-2",
                explanatory_gain=0.9,
                integrates_primitives=["x", "y", "z"],
                resolves_founder_limitation=True,
                survives_critique=True,
                accumulation_signature="A4",
            ),
            acceptance=AcceptanceEvent(
                acknowledged_superiority=True,
                integrated_into_grammar=True,
                updated_invariants=True,
                relinquished_authority=True,
            ),
            validation_ctx=ValidationContext(
                predictive_accuracy_delta=0.2,
                explanatory_compression_delta=0.1,
                cross_domain_convergence=0.8,
                operational_outcome_delta=0.15,
                critique_stability=0.7,
            ),
            expect_survival=True,
        ),
    ]


def run_black_chaos_smoke() -> list[dict[str, Any]]:
    """Execute Black Team fixtures through RAG-Loop; return survival outcomes."""
    results: list[dict[str, Any]] = []
    state = empty_ra_state()
    for scenario in inject_chaos_scenarios():
        change = propose_change(f"Chaos: {scenario.name}")
        state, rag_result, decision = run_rag_loop(
            state,
            change,
            scenario.surpassment,
            scenario.acceptance,
            scenario.validation_ctx,
        )
        survived = (
            rag_result.vas_validated
            if scenario.expect_survival
            else not rag_result.vas_validated
        ) and (decision is not None and decision.approved_provisional or not scenario.expect_survival)
        results.append(
            {
                "scenario": scenario.name,
                "description": scenario.description,
                "vas_validated": rag_result.vas_validated,
                "integrated": rag_result.integrated,
                "expect_survival": scenario.expect_survival,
                "chaos_test_passed": survived,
            }
        )
    return results


def evaluate_white_survival(gold: GoldContinuityMetrics) -> WhiteRoundVerdict:
    """White Team — automated survival gate from Gold metrics (scores left for human)."""
    survived: Literal["yes", "conditional", "no"]
    if gold.k4_satisfied and gold.crk1_compliant and not gold.adm_high_drift:
        survived = "yes" if gold.recommendation == "continue" else "conditional"
    elif not gold.k4_satisfied or not gold.crk1_compliant:
        survived = "no"
    else:
        survived = "conditional"

    notes = [
        f"CSS phase: {gold.css_phase_label}",
        f"Recommendation: {gold.recommendation}",
    ]
    if gold.details.get("css_blockers"):
        notes.append(f"Blockers: {gold.details['css_blockers'][:2]}")

    return WhiteRoundVerdict(
        round_id=gold.round_id,
        system_survived=survived,
        crk_amendment_required=not gold.crk1_compliant,
        notes=notes,
    )


def run_round(
    round_id: int = 1,
    *,
    prior_protocol_rounds: list[RoundProtocolResult] | None = None,
    invariant_target: str = "K4 — Reconstructability",
) -> SimulationRound:
    """Full loop: Gold + Black smoke + protocol scoring + White survival gate."""
    gold = compute_gold_metrics(round_id)
    chaos = run_black_chaos_smoke()
    prior_drift = prior_protocol_rounds[-1].drift_index if prior_protocol_rounds else 0

    protocol = build_round_protocol(
        round_id,
        adm_drift_score=gold.adm_drift_score,
        adm_high_drift=gold.adm_high_drift,
        k4_satisfied=gold.k4_satisfied,
        crk1_compliant=gold.crk1_compliant,
        psd_aggregate=gold.psd_aggregate,
        chaos_results=chaos,
        invariant_target=invariant_target,
        prior_drift_index=prior_drift,
        prior_rounds=prior_protocol_rounds,
    )

    white = evaluate_white_survival(gold)
    white.crk_amendment_required = protocol.amendment_required
    if protocol.amendment_required:
        fired = [trigger.trigger for trigger in protocol.amendment_triggers if trigger.fired]
        white.notes.append(f"CRK amendment triggers fired: {fired}")

    return SimulationRound(
        round_id=round_id,
        invariant_target=invariant_target,
        subsystem="CSS-1 + RA-COS-1 + CRK-1",
        gold=gold,
        chaos_results=chaos,
        white=white,
        protocol=protocol,
    )


def run_campaign(
    *,
    min_rounds: int = 10,
    max_rounds: int = 20,
    invariant_target: str = "K4 — Reconstructability",
) -> CampaignState:
    """
    Run 10–20 rounds per subsystem with stopping rules.

    Stop early when Red/Black attacks become redundant (after min_rounds).
    Extend when drift or invariant stress remains high.
    """
    config = CampaignConfig(
        min_rounds=min_rounds,
        max_rounds=max_rounds,
        invariant_target=invariant_target,
    )
    state = CampaignState(config=config)
    prior_protocol: list[RoundProtocolResult] = []

    for round_id in range(1, max_rounds + 1):
        result = run_round(
            round_id,
            prior_protocol_rounds=prior_protocol,
            invariant_target=invariant_target,
        )
        if result.protocol:
            prior_protocol.append(result.protocol)
            state.rounds.append(result.protocol)

        stop, reason = should_stop_campaign(state)
        if stop:
            state.should_continue = False
            state.stop_reason = reason
            state.rounds_completed = len(state.rounds)
            break
    else:
        state.rounds_completed = len(state.rounds)
        state.should_continue = False
        state.stop_reason = f"Maximum rounds ({max_rounds}) reached."

    return state


def format_gold_report(metrics: GoldContinuityMetrics) -> str:
    lines = [
        f"## Gold Team Metrics — Round {metrics.round_id}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| CE(t) P/C/A | {metrics.ce_p} / {metrics.ce_c} / {metrics.ce_a} |",
        f"| CSS-1 phase | {metrics.css_phase_label} |",
        f"| K4 reconstructability | {'pass' if metrics.k4_satisfied else 'FAIL'} |",
        f"| ADM-1 drift score | {metrics.adm_drift_score} (high={metrics.adm_high_drift}) |",
        f"| PSD aggregate (max) | {metrics.psd_aggregate} |",
        f"| CRK-1 compliant | {metrics.crk1_compliant} |",
        f"| Continuity succeeded | {metrics.continuity_succeeded} |",
        f"| CBCL entries | {metrics.cbcl_entry_count} |",
        "",
        f"**Instrumentality:** {metrics.instrumentality_note}",
        f"**Recommendation:** {metrics.recommendation}",
    ]
    return "\n".join(lines)


def format_protocol_report(protocol: RoundProtocolResult) -> str:
    lines = [
        f"## Protocol — Round {protocol.round_id}",
        "",
        format_drift_report(protocol.drift),
        f"Continuity signal: **{protocol.continuity_signal}**",
        f"Max attack score: {protocol.max_attack_score}/10",
        f"Red exhausted: {protocol.red_exhausted} | Black exhausted: {protocol.black_exhausted}",
        "",
        "### Attack log",
        format_attack_log(protocol.attacks),
        "",
        "### Invariant status",
    ]
    for record in protocol.invariant_records:
        lines.append(f"- **{record.invariant_id}**: {record.status} — {record.blue_defense[:80]}")
    if protocol.amendment_triggers:
        lines.append("")
        lines.append("### Amendment triggers")
        for trigger in protocol.amendment_triggers:
            flag = "FIRED" if trigger.fired else "clear"
            lines.append(f"- Trigger {trigger.trigger} [{flag}]: {trigger.explanation}")
    if protocol.kernel_failure:
        lines.append("")
        lines.append(f"### KERNEL FAILURE: {protocol.kernel_failure.break_id}")
        lines.append(protocol.kernel_failure.explanation)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Five-Team Continuity Simulation Loop")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--gold-only", action="store_true", help="Print Gold metrics only")
    parser.add_argument("--campaign", action="store_true", help="Run full 10–20 round campaign")
    parser.add_argument("--min-rounds", type=int, default=10)
    parser.add_argument("--max-rounds", type=int, default=20)
    args = parser.parse_args()

    if args.campaign:
        campaign = run_campaign(min_rounds=args.min_rounds, max_rounds=args.max_rounds)
        if args.json:
            print(json.dumps(campaign.model_dump(), indent=2))
        else:
            print(f"# Five-Team Campaign — {campaign.rounds_completed} rounds")
            print(f"Stop reason: {campaign.stop_reason}")
            if campaign.rounds:
                print(format_protocol_report(campaign.rounds[-1]))
        return

    if args.gold_only:
        gold = compute_gold_metrics(args.round)
        if args.json:
            print(json.dumps(gold.model_dump(), indent=2))
        else:
            print(format_gold_report(gold))
        return

    result = run_round(args.round)
    payload = {
        "round_id": result.round_id,
        "invariant_target": result.invariant_target,
        "subsystem": result.subsystem,
        "gold": result.gold.model_dump() if result.gold else None,
        "chaos_results": result.chaos_results,
        "white": result.white.model_dump() if result.white else None,
        "protocol": result.protocol.model_dump() if result.protocol else None,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if result.gold:
            print(format_gold_report(result.gold))
        if result.protocol:
            print("\n" + format_protocol_report(result.protocol))
        print("\n## Black Team smoke results")
        for item in result.chaos_results:
            print(f"- {item['scenario']}: chaos_test_passed={item['chaos_test_passed']}")
        if result.white:
            print(f"\n## White Team gate: survived={result.white.system_survived}")
            print(f"CRK amendment required: {result.white.crk_amendment_required}")


if __name__ == "__main__":
    main()
