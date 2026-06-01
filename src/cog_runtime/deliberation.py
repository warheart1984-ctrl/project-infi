"""Deliberation Runtime — Options → Tradeoffs → Commit → Revisit."""

from __future__ import annotations

import re
from typing import Any, Callable

from src.cog_runtime.base import CogRuntimeSession, runtime_spec_template
from src.cog_runtime.capability_governance import lobe_capability_contract
from src.cog_runtime.deliberation_llm import build_deliberation_prompt, run_deliberation_llm
from src.cog_runtime.intent_consult import intent_influence_summary, score_option_intent_alignment
from src.speaking_runtime import infer_frame_kind

DELIBERATION_RUNTIME_ID = "cognitive.deliberation"
DELIBERATION_RUNTIME_VERSION = "1.2"
DELIBERATION_STAGES = ("options", "tradeoffs", "commit", "revisit")
REQUIRED_TURN_STAGES = ("options", "tradeoffs", "commit")

DELIBERATION_CRITERIA = (
    "focus_alignment",
    "risk",
    "policy_fit",
    "testability",
    "user_goal",
    "intent_alignment",
)

CRITERION_WEIGHTS: dict[str, float] = {
    "focus_alignment": 0.25,
    "risk": 0.18,
    "policy_fit": 0.12,
    "testability": 0.12,
    "user_goal": 0.18,
    "intent_alignment": 0.15,
}

DELIBERATION_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "options_before_commit", "rule": "Commit must follow enumerated options and tradeoffs."},
    {"id": "traceability", "rule": "Decision object must map to ledger stages."},
    {"id": "revisit_optional", "rule": "Revisit opens only when new information is present."},
    {"id": "multi_criteria", "rule": "Commit records explicit criteria_scores for every option."},
)

OPTION_SPLIT_RE = re.compile(r"\b(?:or|vs\.?|versus|/\s)\b", re.I)
NUMBERED_OPTION_RE = re.compile(r"(?:^\d+[.)]\s*|\n\d+[.)]\s*)", re.MULTILINE)
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")
TESTABILITY_HINTS = ("test", "verify", "quick", "fast", "pilot", "prototype", "check")


def deliberation_runtime_spec() -> dict[str, Any]:
    return runtime_spec_template(
        runtime_id=DELIBERATION_RUNTIME_ID,
        version=DELIBERATION_RUNTIME_VERSION,
        summary="Human-like decision loop with multi-criteria scoring and LLM fallback.",
        stages=DELIBERATION_STAGES,
        required_turn_stages=REQUIRED_TURN_STAGES,
        invariants=DELIBERATION_INVARIANTS,
        inputs={
            "user_message": "string",
            "frame_kind": "decision|general|...",
            "focus_artifact": "object",
            "context": "object",
            "deliberate_fn": "callable|optional",
        },
        outputs={
            "decision_object": {
                "chosen_option": "string",
                "alternatives": "string[]",
                "rationale": "string",
                "assumptions": "string[]",
                "tradeoffs": "object[]",
                "criteria_scores": "object",
                "winning_criteria": "string[]",
                "commit_source": "llm|deterministic",
                "intent_influence": "object",
            }
        },
        doc="docs/runtime/NOVA_CORTEX.md",
        **lobe_capability_contract(DELIBERATION_RUNTIME_ID),
    )


def should_activate_deliberation(user_message: str, *, frame_kind: str | None = None) -> bool:
    kind = frame_kind or infer_frame_kind(user_message)
    return kind == "decision"


def _extract_options(user_message: str) -> list[str]:
    text = " ".join((user_message or "").split()).strip()
    if not text:
        return ["Proceed with the default path", "Pause and gather more information"]

    numbered = [
        " ".join(chunk.split()).strip(" ?.")
        for chunk in NUMBERED_OPTION_RE.split(text)
        if chunk.strip()
    ]
    if len(numbered) >= 2:
        return numbered[:4]

    parts = OPTION_SPLIT_RE.split(text)
    options: list[str] = []
    for part in parts:
        cleaned = part.strip(" ?.")
        if cleaned and cleaned not in options:
            options.append(cleaned)
    if len(options) >= 2:
        return options[:4]

    return [
        "Take the most direct actionable path",
        "Compare alternatives before committing",
        "Defer until more constraints are known",
    ]


def _build_tradeoffs(
    options: list[str],
    *,
    focus_artifact: dict[str, Any] | None = None,
    policy_posture: str = "",
) -> list[dict[str, str]]:
    primary = str((focus_artifact or {}).get("primary_focus") or "").lower()
    cautious = policy_posture in {"cautious", "degraded"}
    tradeoffs: list[dict[str, str]] = []
    for option in options:
        risk = "medium"
        if cautious:
            risk = "high"
        if primary and primary in option.lower():
            risk = "low" if not cautious else "medium"
        tradeoffs.append(
            {
                "option": option,
                "pros": "Aligns with current turn focus and is testable quickly.",
                "cons": "May miss hidden constraints or second-order effects.",
                "risk": risk,
            }
        )
    return tradeoffs


def _score_option_by_criteria(
    option: str,
    tradeoffs: list[dict[str, str]],
    *,
    user_message: str = "",
    focus_artifact: dict[str, Any] | None = None,
    policy_posture: str = "",
    intent_context: dict[str, Any] | None = None,
) -> dict[str, float]:
    primary = str((focus_artifact or {}).get("primary_focus") or "").lower()
    secondary = [
        str(item).lower() for item in (focus_artifact or {}).get("secondary_focus") or []
    ]
    salience = dict((focus_artifact or {}).get("salience") or {})
    weights = dict((focus_artifact or {}).get("weights") or {})
    lowered = option.lower()

    focus_alignment = 0.35
    if primary and primary in lowered:
        focus_alignment += 0.45
    elif any(item in lowered for item in secondary):
        focus_alignment += 0.25
    focus_alignment += min(0.2, float(salience.get(option, weights.get(option, 0.0))))

    tradeoff = next((item for item in tradeoffs if item.get("option") == option), None)
    risk_level = str((tradeoff or {}).get("risk") or "medium")
    risk = {"low": 0.85, "medium": 0.55, "high": 0.25}.get(risk_level, 0.55)

    policy_fit = 0.5
    if policy_posture in {"cautious", "degraded"}:
        policy_fit = 0.75 if "defer" in lowered else 0.35
    elif policy_posture in {"nominal", ""}:
        policy_fit = 0.65 if "direct" in lowered or "action" in lowered else 0.5

    testability = 0.45
    if any(hint in lowered for hint in TESTABILITY_HINTS):
        testability = 0.85
    elif "compare" in lowered:
        testability = 0.6

    message_tokens = set(WORD_RE.findall(user_message.lower()))
    option_tokens = set(WORD_RE.findall(lowered))
    overlap = message_tokens & option_tokens
    user_goal = min(0.9, 0.35 + 0.1 * len(overlap)) if overlap else 0.35

    intent_alignment = score_option_intent_alignment(option, intent_context)

    return {
        "focus_alignment": round(min(focus_alignment, 1.0), 3),
        "risk": round(risk, 3),
        "policy_fit": round(min(policy_fit, 1.0), 3),
        "testability": round(testability, 3),
        "user_goal": round(user_goal, 3),
        "intent_alignment": round(intent_alignment, 3),
    }


def _weighted_total(criteria_scores: dict[str, float]) -> float:
    return round(
        sum(criteria_scores.get(key, 0.0) * CRITERION_WEIGHTS.get(key, 0.0) for key in DELIBERATION_CRITERIA),
        3,
    )


def _score_option(
    option: str,
    tradeoffs: list[dict[str, str]],
    *,
    user_message: str = "",
    focus_artifact: dict[str, Any] | None = None,
    policy_posture: str = "",
    intent_context: dict[str, Any] | None = None,
) -> float:
    criteria = _score_option_by_criteria(
        option,
        tradeoffs,
        user_message=user_message,
        focus_artifact=focus_artifact,
        policy_posture=policy_posture,
        intent_context=intent_context,
    )
    return _weighted_total(criteria)


def _winning_criteria(
    winner_scores: dict[str, float],
    runner_up_scores: dict[str, float],
) -> list[str]:
    deltas: list[tuple[float, str]] = []
    for criterion in DELIBERATION_CRITERIA:
        delta = winner_scores.get(criterion, 0.0) - runner_up_scores.get(criterion, 0.0)
        deltas.append((delta, criterion))
    deltas.sort(key=lambda item: (-item[0], item[1]))
    winners = [criterion for delta, criterion in deltas[:2] if delta > 0.01]
    if winners:
        return winners
    return [criterion for _, criterion in deltas[:2]]


def _build_criteria_scores(
    options: list[str],
    tradeoffs: list[dict[str, str]],
    *,
    user_message: str = "",
    focus_artifact: dict[str, Any] | None = None,
    policy_posture: str = "",
    intent_context: dict[str, Any] | None = None,
) -> dict[str, dict[str, float]]:
    return {
        option: _score_option_by_criteria(
            option,
            tradeoffs,
            user_message=user_message,
            focus_artifact=focus_artifact,
            policy_posture=policy_posture,
            intent_context=intent_context,
        )
        for option in options
    }


def _attach_criteria_to_decision(
    decision: dict[str, Any],
    *,
    options: list[str],
    tradeoffs: list[dict[str, str]],
    user_message: str = "",
    focus_artifact: dict[str, Any] | None = None,
    policy_posture: str = "",
    intent_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    criteria_scores = decision.get("criteria_scores")
    if not isinstance(criteria_scores, dict) or not criteria_scores:
        criteria_scores = _build_criteria_scores(
            options,
            tradeoffs,
            user_message=user_message,
            focus_artifact=focus_artifact,
            policy_posture=policy_posture,
            intent_context=intent_context,
        )
        decision["criteria_scores"] = criteria_scores

    ranked = sorted(
        options,
        key=lambda option: _weighted_total(dict(criteria_scores.get(option) or {})),
        reverse=True,
    )
    chosen = str(decision.get("chosen_option") or ranked[0])
    runner_up = next((item for item in ranked if item != chosen), ranked[0])
    winner_scores = dict(criteria_scores.get(chosen) or {})
    runner_scores = dict(criteria_scores.get(runner_up) or {})
    decision["winning_criteria"] = _winning_criteria(winner_scores, runner_scores)
    influence = intent_influence_summary(
        intent_context=intent_context,
        applied_to="deliberation.commit",
        detail=f"Weighted options by intent pull for '{chosen[:60]}'.",
    )
    if influence:
        decision["intent_influence"] = influence
    return decision


def _deterministic_commit(
    options: list[str],
    tradeoffs: list[dict[str, str]],
    *,
    user_message: str = "",
    focus_artifact: dict[str, Any] | None = None,
    policy_posture: str = "",
    intent_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    criteria_scores = _build_criteria_scores(
        options,
        tradeoffs,
        user_message=user_message,
        focus_artifact=focus_artifact,
        policy_posture=policy_posture,
        intent_context=intent_context,
    )
    ranked = sorted(
        options,
        key=lambda option: _weighted_total(criteria_scores[option]),
        reverse=True,
    )
    chosen = ranked[0]
    alternatives = [item for item in ranked[1:] if item != chosen]
    assumptions = [
        "User goal is stable for this turn.",
        "Available options cover the main viable paths.",
    ]
    if focus_artifact and focus_artifact.get("primary_focus"):
        assumptions.append(
            f"Attention primary focus '{focus_artifact['primary_focus']}' informs the commit."
        )
    winning = _winning_criteria(
        criteria_scores[chosen],
        criteria_scores[alternatives[0]] if alternatives else criteria_scores[chosen],
    )
    rationale = (
        f"Selected '{chosen}' because it best matches turn focus and acceptable risk "
        f"under a {policy_posture or 'nominal'} policy posture "
        f"(top criteria: {', '.join(winning)})."
    )
    return {
        "chosen_option": chosen,
        "alternatives": alternatives,
        "rationale": rationale,
        "assumptions": assumptions,
        "tradeoffs": tradeoffs,
        "criteria_scores": criteria_scores,
        "winning_criteria": winning,
        "commit_source": "deterministic",
    }


def run_deliberation_turn(
    user_message: str,
    *,
    context: dict[str, Any] | None = None,
    frame_kind: str | None = None,
    focus_artifact: dict[str, Any] | None = None,
    revisit_note: str = "",
    deliberate_fn: Callable[[dict[str, str]], dict[str, Any] | None] | None = None,
    use_llm: bool = False,
) -> tuple[dict[str, Any], CogRuntimeSession]:
    """Execute a full deliberation turn and return decision object + session."""
    ctx = dict(context or {})
    kind = frame_kind or infer_frame_kind(user_message)
    focus = dict(focus_artifact or ctx.get("focus_artifact") or {})
    policy_posture = str(
        ctx.get("policy_posture")
        or (ctx.get("policy_status") or {}).get("posture")
        or ""
    )
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
        runtime_id=DELIBERATION_RUNTIME_ID,
        user_message=user_message,
        context=ctx,
        required_stages=REQUIRED_TURN_STAGES,
        stage_order=DELIBERATION_STAGES,
    )

    llm_payload: dict[str, Any] | None = None
    if use_llm or deliberate_fn is not None or ctx.get("deliberation_llm"):
        prompt = build_deliberation_prompt(
            user_message,
            focus_artifact=focus,
            frame_kind=kind,
        )
        llm_payload = run_deliberation_llm(prompt, deliberate_fn=deliberate_fn)

    if llm_payload:
        options = list(llm_payload.get("options") or [])
        tradeoffs = list(
            llm_payload.get("tradeoffs") or _build_tradeoffs(options, focus_artifact=focus)
        )
        decision_object = {
            "chosen_option": llm_payload["chosen_option"],
            "alternatives": [
                item for item in options if item != llm_payload["chosen_option"]
            ],
            "rationale": llm_payload["rationale"],
            "assumptions": list(llm_payload.get("assumptions") or []),
            "tradeoffs": tradeoffs,
            "commit_source": llm_payload.get("commit_source") or "llm",
        }
        if isinstance(llm_payload.get("criteria_scores"), dict):
            decision_object["criteria_scores"] = llm_payload["criteria_scores"]
    else:
        options = _extract_options(user_message)
        tradeoffs = _build_tradeoffs(
            options,
            focus_artifact=focus,
            policy_posture=policy_posture,
        )
        decision_object = _deterministic_commit(
            options,
            tradeoffs,
            user_message=user_message,
            focus_artifact=focus,
            policy_posture=policy_posture,
            intent_context=intent_context or None,
        )

    decision_object = _attach_criteria_to_decision(
        decision_object,
        options=options,
        tradeoffs=tradeoffs,
        user_message=user_message,
        focus_artifact=focus,
        policy_posture=policy_posture,
        intent_context=intent_context or None,
    )

    session.start_stage("options", {"user_message": user_message, "focus": focus.get("primary_focus")})
    session.end_stage("options", {"options": options})

    session.start_stage("tradeoffs", {"options": options})
    session.end_stage("tradeoffs", {"tradeoffs": decision_object.get("tradeoffs", tradeoffs)})

    session.start_stage("commit", {"tradeoffs": decision_object.get("tradeoffs", [])})
    session.end_stage(
        "commit",
        {
            "decision_object": decision_object,
            "criteria_scores": decision_object.get("criteria_scores"),
            "winning_criteria": decision_object.get("winning_criteria"),
        },
    )

    revisit = revisit_note.strip() or str(ctx.get("revisit_note") or "").strip()
    if ctx.get("user_correction") or revisit:
        note = revisit or "User correction received; decision may need revision."
        session.start_stage("revisit", {"note": note})
        session.end_stage("revisit", {"reopened": True, "note": note})

    validation = validate_decision_object(decision_object)
    if not validation["valid"]:
        raise ValueError(f"deliberation turn invalid: {validation['issues']}")
    turn_validation = session.validate_turn()
    if not turn_validation["valid"]:
        raise ValueError(f"deliberation ledger invalid: {turn_validation['issues']}")

    return decision_object, session


def validate_decision_object(decision: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not str(decision.get("chosen_option") or "").strip():
        issues.append("missing_chosen_option")
    alternatives = decision.get("alternatives")
    if not isinstance(alternatives, list):
        issues.append("alternatives_not_list")
    if not str(decision.get("rationale") or "").strip():
        issues.append("missing_rationale")
    assumptions = decision.get("assumptions")
    if not isinstance(assumptions, list):
        issues.append("assumptions_not_list")
    tradeoffs = decision.get("tradeoffs")
    if tradeoffs is not None and not isinstance(tradeoffs, list):
        issues.append("tradeoffs_not_list")
    criteria_scores = decision.get("criteria_scores")
    if not isinstance(criteria_scores, dict) or not criteria_scores:
        issues.append("missing_criteria_scores")
    winning = decision.get("winning_criteria")
    if not isinstance(winning, list) or not winning:
        issues.append("missing_winning_criteria")
    commit_source = decision.get("commit_source")
    if commit_source is not None and commit_source not in {"llm", "deterministic"}:
        issues.append("invalid_commit_source")
    return {"valid": not issues, "issues": issues}
