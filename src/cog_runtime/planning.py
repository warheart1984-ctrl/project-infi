"""Planning Runtime — Orient → Sequence → Checkpoint → Handoff."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.base import CogRuntimeSession, runtime_spec_template
from src.cog_runtime.capability_governance import lobe_capability_contract
from src.cog_runtime.intent_consult import intent_influence_summary, score_chain_intent_alignment

PLANNING_RUNTIME_ID = "cognitive.planning"
PLANNING_RUNTIME_VERSION = "1.3"
PLANNING_STAGES = ("orient", "sequence", "checkpoint", "handoff")
REQUIRED_TURN_STAGES = PLANNING_STAGES
MAX_STEPS = 5
MAX_CHAINS = 3

PLANNING_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "bounded_plan", "rule": "Plans contain at most five sequenced steps per chain."},
    {"id": "reflection_handoff", "rule": "Planning follows reflection; it does not bypass Jarvis authority."},
    {"id": "multi_step_chains", "rule": "At least one active step chain is bound per planning turn."},
    {"id": "adaptive_chain_selection", "rule": "Active chain is scored from arc and tuning evidence."},
)


def planning_runtime_spec() -> dict[str, Any]:
    return runtime_spec_template(
        runtime_id=PLANNING_RUNTIME_ID,
        version=PLANNING_RUNTIME_VERSION,
        summary="Adaptive multi-step planning chains for reflection handoff and execution binding.",
        stages=PLANNING_STAGES,
        required_turn_stages=REQUIRED_TURN_STAGES,
        invariants=PLANNING_INVARIANTS,
        inputs={
            "reflection_artifact": "object",
            "focus_artifact": "object",
            "decision_object": "object",
            "cognitive_arc": "object",
            "frame_kind": "string",
            "tuned_thresholds": "object",
        },
        outputs={
            "planning_artifact": {
                "arc_step": "number",
                "steps": "string[]",
                "step_chains": "object[]",
                "active_chain_id": "string",
                "active_chain": "object",
                "chain_step_index": "number",
                "chain_scores": "object",
                "chain_selection_reason": "string",
                "checkpoints": "string[]",
                "handoff_summary": "string",
                "next_action": "string",
                "execution_handoff": "boolean",
                "intent_influence": "object",
            }
        },
        doc="docs/runtime/NOVA_CORTEX.md",
        **lobe_capability_contract(PLANNING_RUNTIME_ID),
    )


def validate_planning_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    steps = artifact.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append("missing_steps")
    elif len(steps) > MAX_STEPS:
        issues.append("too_many_steps")
    chains = artifact.get("step_chains")
    if not isinstance(chains, list) or not chains:
        issues.append("missing_step_chains")
    elif len(chains) > MAX_CHAINS:
        issues.append("too_many_chains")
    if not str(artifact.get("active_chain_id") or "").strip():
        issues.append("missing_active_chain_id")
    active_chain = artifact.get("active_chain")
    if not isinstance(active_chain, dict):
        issues.append("missing_active_chain")
    chain_index = artifact.get("chain_step_index")
    if not isinstance(chain_index, int) or chain_index < 0:
        issues.append("invalid_chain_step_index")
    scores = artifact.get("chain_scores")
    if not isinstance(scores, dict):
        issues.append("missing_chain_scores")
    if not str(artifact.get("chain_selection_reason") or "").strip():
        issues.append("missing_chain_selection_reason")
    checkpoints = artifact.get("checkpoints")
    if not isinstance(checkpoints, list):
        issues.append("checkpoints_not_list")
    if not str(artifact.get("handoff_summary") or "").strip():
        issues.append("missing_handoff_summary")
    if not str(artifact.get("next_action") or "").strip():
        issues.append("missing_next_action")
    arc_step = artifact.get("arc_step")
    if not isinstance(arc_step, int) or arc_step < 1:
        issues.append("invalid_arc_step")
    if not isinstance(artifact.get("execution_handoff"), bool):
        issues.append("missing_execution_handoff")
    return {"valid": not issues, "issues": issues}


def should_activate_planning(
    reflection_artifact: dict[str, Any] | None,
    *,
    companion_turn: bool = False,
) -> bool:
    reflection = dict(reflection_artifact or {})
    if companion_turn:
        return True
    alignment = str(reflection.get("alignment") or "")
    return alignment in {"partial", "misaligned"} or bool(reflection.get("adjustments"))


def _build_steps(
    *,
    reflection: dict[str, Any],
    focus: dict[str, Any],
    decision: dict[str, Any],
    arc_context: dict[str, Any],
    intent_context: dict[str, Any] | None = None,
) -> list[str]:
    steps: list[str] = []
    for item in (intent_context or {}).get("intent_commitments") or []:
        if not isinstance(item, dict):
            continue
        if item.get("status") not in {"active", "in_tension"}:
            continue
        text = str(item.get("commitment") or "").strip()
        if text and text not in steps:
            steps.append(f"Honor commitment: {text[:120]}")
    primary = str(focus.get("primary_focus") or "").strip()
    if primary:
        steps.append(f"Keep primary focus on: {primary}")
    for adjustment in reflection.get("adjustments") or []:
        text = str(adjustment).strip()
        if text and text not in steps:
            steps.append(text)
    if decision.get("chosen_option"):
        steps.append(f"Execute decision path: {decision['chosen_option']}")
    for hint in reflection.get("next_turn_hints") or []:
        text = str(hint).strip()
        if text and text not in steps:
            steps.append(text)
    prior_action = str(arc_context.get("prior_next_action") or "").strip()
    if prior_action and prior_action not in steps:
        steps.append(f"Continue prior action: {prior_action}")
    current_subgoal = str(arc_context.get("arc_current_subgoal") or "").strip()
    if current_subgoal and current_subgoal not in steps:
        steps.append(f"Advance subgoal: {current_subgoal}")
    if not steps:
        steps.append("Deliver a clear, focus-aligned reply.")
    return steps[:MAX_STEPS]


def _build_step_chains(
    steps: list[str],
    *,
    arc_context: dict[str, Any],
) -> list[dict[str, Any]]:
    chains: list[dict[str, Any]] = []
    if not steps:
        return chains

    primary_steps = steps[:3]
    chains.append(
        {
            "chain_id": "primary",
            "label": "Primary chain",
            "steps": primary_steps,
            "status": "pending",
        }
    )

    if len(steps) > 3:
        chains.append(
            {
                "chain_id": "continuation",
                "label": "Continuation chain",
                "steps": steps[3:],
                "status": "pending",
            }
        )

    subgoals = list(arc_context.get("arc_subgoals") or [])
    if subgoals:
        chains.append(
            {
                "chain_id": "subgoal",
                "label": "Subgoal chain",
                "steps": [f"Advance subgoal: {item}" for item in subgoals[:2]],
                "status": "pending",
            }
        )

    return chains[:MAX_CHAINS]


def _score_chain(
    chain: dict[str, Any],
    *,
    arc_context: dict[str, Any],
    tuned_thresholds: dict[str, float] | None,
    intent_context: dict[str, Any] | None = None,
) -> float:
    thresholds = dict(tuned_thresholds or {})
    chain_id = str(chain.get("chain_id") or "")
    score = 0.0

    if chain_id == str(arc_context.get("prior_active_chain_id") or ""):
        score += 1.0

    prior_status = str(arc_context.get("prior_execution_status") or "")
    if prior_status == "failed" and chain_id != "primary":
        score += 3.0
    if prior_status == "partial" and float(thresholds.get("chain_advance_on_partial", 0.0)) >= 1.0:
        score += 2.5
    if prior_status == "passed" and chain_id == "primary":
        score += 2.0

    if chain_id == "subgoal" and arc_context.get("arc_current_subgoal"):
        score += 1.5

    if str(arc_context.get("arc_goal_closure_status") or "") == "subgoals_closed" and chain_id == "continuation":
        score += 2.0

    steps = list(chain.get("steps") or [])
    score += min(len(steps), 3) * 0.25
    score += score_chain_intent_alignment(chain, intent_context)
    return round(score, 3)


def _select_active_chain_adaptive(
    chains: list[dict[str, Any]],
    *,
    arc_context: dict[str, Any],
    tuned_thresholds: dict[str, float] | None,
    intent_context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int, dict[str, float], str]:
    if not chains:
        raise ValueError("planning requires at least one chain")

    scores = {
        str(chain.get("chain_id") or f"chain-{index}"): _score_chain(
            chain,
            arc_context=arc_context,
            tuned_thresholds=tuned_thresholds,
            intent_context=intent_context,
        )
        for index, chain in enumerate(chains)
    }
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    active_id, top_score = ranked[0]
    active = next(item for item in chains if str(item.get("chain_id")) == active_id)

    for chain in chains:
        chain["status"] = "active" if chain.get("chain_id") == active_id else "pending"

    chain_index = int(arc_context.get("prior_chain_step_index") or 0)
    thresholds = dict(tuned_thresholds or {})
    if (
        str(arc_context.get("prior_execution_status") or "") == "partial"
        and float(thresholds.get("chain_advance_on_partial", 0.0)) >= 1.0
    ):
        chain_index += 1

    active_steps = list(active.get("steps") or [])
    if chain_index >= len(active_steps):
        chain_index = 0

    reason_parts = [f"selected {active_id} score={top_score}"]
    if len(ranked) > 1:
        reason_parts.append(f"runner_up={ranked[1][0]}({ranked[1][1]})")
    prior_status = str(arc_context.get("prior_execution_status") or "")
    if prior_status:
        reason_parts.append(f"prior_execution={prior_status}")
    return active, chain_index, scores, "; ".join(reason_parts)


def run_planning_turn(
    *,
    reflection_artifact: dict[str, Any],
    focus_artifact: dict[str, Any] | None = None,
    decision_object: dict[str, Any] | None = None,
    cognitive_arc: dict[str, Any] | None = None,
    frame_kind: str = "general",
    user_message: str = "",
    tuned_thresholds: dict[str, float] | None = None,
    context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], CogRuntimeSession]:
    ctx = dict(context or {})
    intent_context = {
        key: ctx[key]
        for key in (
            "intent_commitments",
            "intent_tensions",
            "intent_horizon_goals",
            "intent_protected_values",
            "intent_agency_note",
        )
        if key in ctx
    }

    session = CogRuntimeSession(
        runtime_id=PLANNING_RUNTIME_ID,
        user_message=user_message,
        context={"frame_kind": frame_kind},
        required_stages=REQUIRED_TURN_STAGES,
        stage_order=PLANNING_STAGES,
    )

    reflection = dict(reflection_artifact or {})
    focus = dict(focus_artifact or {})
    decision = dict(decision_object or {})
    arc = dict(cognitive_arc or {})
    arc_step = int(arc.get("arc_turn_count") or arc.get("turn_count") or 0) + 1

    session.start_stage(
        "orient",
        {
            "alignment": reflection.get("alignment"),
            "arc_goal": arc.get("arc_goal") or arc.get("goal"),
            "root_goal": arc.get("arc_root_goal") or arc.get("root_goal"),
            "goal_closure_status": arc.get("arc_goal_closure_status") or arc.get("goal_closure_status"),
        },
    )
    session.end_stage(
        "orient",
        {
            "gaps": reflection.get("gaps"),
            "open_threads": arc.get("arc_open_threads") or arc.get("open_threads"),
            "subgoals": arc.get("arc_subgoals") or arc.get("subgoals"),
        },
    )

    steps = _build_steps(
        reflection=reflection,
        focus=focus,
        decision=decision,
        arc_context=arc,
        intent_context=intent_context or None,
    )
    step_chains = _build_step_chains(steps, arc_context=arc)
    active_chain, chain_step_index, chain_scores, chain_selection_reason = _select_active_chain_adaptive(
        step_chains,
        arc_context=arc,
        tuned_thresholds=tuned_thresholds,
        intent_context=intent_context or None,
    )
    active_steps = list(active_chain.get("steps") or steps)
    next_action = active_steps[chain_step_index] if active_steps else steps[0]

    session.start_stage("sequence", {"candidate_steps": steps, "chains": len(step_chains)})
    session.end_stage(
        "sequence",
        {
            "steps": steps,
            "step_chains": step_chains,
            "active_chain_id": active_chain.get("chain_id"),
            "chain_scores": chain_scores,
        },
    )

    checkpoints = [
        "Focus visible in opening lines",
        "Decision or arc next action stated when applicable",
        "Alignment check before send",
    ]
    if reflection.get("alignment") != "aligned":
        checkpoints.insert(0, "Close reflection gaps before expanding scope")
    if len(step_chains) > 1:
        checkpoints.append("Respect active planning chain before switching chains")

    session.start_stage("checkpoint", {"steps": steps, "active_chain_id": active_chain.get("chain_id")})
    session.end_stage("checkpoint", {"checkpoints": checkpoints})

    handoff_summary = (
        f"Arc step {arc_step} chain '{active_chain.get('chain_id')}': {next_action} "
        f"under {frame_kind} frame with {reflection.get('alignment', 'unknown')} alignment."
    )
    session.start_stage("handoff", {"next_action": next_action})
    session.end_stage("handoff", {"handoff_summary": handoff_summary})

    planning_artifact = {
        "arc_step": arc_step,
        "steps": steps,
        "step_chains": step_chains,
        "active_chain_id": str(active_chain.get("chain_id") or "primary"),
        "active_chain": active_chain,
        "chain_step_index": chain_step_index,
        "chain_scores": chain_scores,
        "chain_selection_reason": chain_selection_reason,
        "checkpoints": checkpoints,
        "handoff_summary": handoff_summary,
        "next_action": next_action,
        "execution_handoff": bool(next_action),
    }
    influence = intent_influence_summary(
        intent_context=intent_context or None,
        applied_to="planning.chain_selection",
        detail=f"Selected chain '{active_chain.get('chain_id')}' with intent-aware scoring.",
    )
    if influence:
        planning_artifact["intent_influence"] = influence

    validation = validate_planning_artifact(planning_artifact)
    if not validation["valid"]:
        raise ValueError(f"planning turn invalid: {validation['issues']}")
    turn_validation = session.validate_turn()
    if not turn_validation["valid"]:
        raise ValueError(f"planning ledger invalid: {turn_validation['issues']}")

    return planning_artifact, session
