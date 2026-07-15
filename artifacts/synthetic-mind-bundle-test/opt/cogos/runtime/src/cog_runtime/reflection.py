"""Reflection Runtime — Expect → Compare → Learn → Adjust."""

from __future__ import annotations

import re
from typing import Any

from src.cog_runtime.base import CogRuntimeSession, runtime_spec_template
from src.cog_runtime.capability_governance import lobe_capability_contract

REFLECTION_RUNTIME_ID = "cognitive.reflection"
REFLECTION_RUNTIME_VERSION = "1.3"
REFLECTION_STAGES = ("expect", "compare", "learn", "adjust")
REQUIRED_TURN_STAGES = REFLECTION_STAGES
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")

REFLECTION_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "non_competing", "rule": "Reflection evaluates coherence; it does not override Jarvis authority."},
    {"id": "traceability", "rule": "Every alignment gap maps to a ledger stage."},
)


def reflection_runtime_spec() -> dict[str, Any]:
    return runtime_spec_template(
        runtime_id=REFLECTION_RUNTIME_ID,
        version=REFLECTION_RUNTIME_VERSION,
        summary="Cross-lobe reflection loop with planning handoff.",
        stages=REFLECTION_STAGES,
        required_turn_stages=REQUIRED_TURN_STAGES,
        invariants=REFLECTION_INVARIANTS,
        inputs={
            "focus_artifact": "object",
            "decision_object": "object",
            "memory_artifact": "object",
            "frame_kind": "string",
            "speak_body": "string",
        },
        outputs={
            "reflection_artifact": {
                "expected_outcome": "string",
                "alignment": "aligned|partial|misaligned",
                "gaps": "string[]",
                "adjustments": "string[]",
                "next_turn_hints": "string[]",
                "planning_handoff": "boolean",
            }
        },
        doc="docs/runtime/NOVA_CORTEX.md",
        **lobe_capability_contract(REFLECTION_RUNTIME_ID),
    )


def validate_reflection_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not str(artifact.get("expected_outcome") or "").strip():
        issues.append("missing_expected_outcome")
    alignment = str(artifact.get("alignment") or "")
    if alignment not in {"aligned", "partial", "misaligned"}:
        issues.append("invalid_alignment")
    for field in ("gaps", "adjustments", "next_turn_hints"):
        value = artifact.get(field)
        if not isinstance(value, list):
            issues.append(f"{field}_not_list")
    planning_handoff = artifact.get("planning_handoff")
    if not isinstance(planning_handoff, bool):
        issues.append("missing_planning_handoff")
    return {"valid": not issues, "issues": issues}


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(WORD_RE.findall(left.lower()))
    right_tokens = set(WORD_RE.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), 1)


def _build_expected_outcome(
    *,
    focus_artifact: dict[str, Any],
    decision_object: dict[str, Any] | None,
    frame_kind: str,
) -> str:
    primary = str(focus_artifact.get("primary_focus") or "").strip()
    if decision_object and decision_object.get("chosen_option"):
        return (
            f"Deliver a {frame_kind} response aligned with focus '{primary}' "
            f"and decision '{decision_object['chosen_option']}'."
        )
    if primary:
        return f"Deliver a {frame_kind} response centered on '{primary}'."
    return f"Deliver a clear {frame_kind} response aligned with the user's request."


def should_handoff_to_planning(reflection_artifact: dict[str, Any] | None) -> bool:
    reflection = dict(reflection_artifact or {})
    if reflection.get("planning_handoff") is True:
        return True
    alignment = str(reflection.get("alignment") or "")
    return alignment in {"partial", "misaligned"} or bool(reflection.get("adjustments"))


def _compare_delivery(
    *,
    expected_outcome: str,
    speak_body: str,
    focus_artifact: dict[str, Any],
    decision_object: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    gaps: list[str] = []
    body = str(speak_body or "").strip()
    if not body:
        return "misaligned", ["empty_delivery"]

    focus_score = _token_overlap(body, str(focus_artifact.get("primary_focus") or ""))
    if focus_score < 0.15:
        gaps.append("focus_not_reflected_in_delivery")

    if decision_object:
        chosen = str(decision_object.get("chosen_option") or "")
        decision_score = _token_overlap(body, chosen)
        if decision_score < 0.1:
            gaps.append("decision_not_reflected_in_delivery")

    expected_score = _token_overlap(body, expected_outcome)
    if expected_score < 0.08 and gaps:
        alignment = "misaligned"
    elif gaps:
        alignment = "partial"
    else:
        alignment = "aligned"
    return alignment, gaps


def run_reflection_turn(
    *,
    focus_artifact: dict[str, Any] | None = None,
    decision_object: dict[str, Any] | None = None,
    memory_artifact: dict[str, Any] | None = None,
    frame_kind: str = "general",
    user_message: str = "",
    speak_body: str = "",
) -> tuple[dict[str, Any], CogRuntimeSession]:
    session = CogRuntimeSession(
        runtime_id=REFLECTION_RUNTIME_ID,
        user_message=user_message,
        context={
            "frame_kind": frame_kind,
            "has_decision": bool(decision_object),
            "has_memory": bool(memory_artifact),
        },
        required_stages=REQUIRED_TURN_STAGES,
        stage_order=REFLECTION_STAGES,
    )

    focus = dict(focus_artifact or {})
    decision = dict(decision_object or {})
    memory = dict(memory_artifact or {})

    expected_outcome = _build_expected_outcome(
        focus_artifact=focus,
        decision_object=decision or None,
        frame_kind=frame_kind,
    )
    session.start_stage("expect", {"frame_kind": frame_kind, "focus": focus.get("primary_focus")})
    session.end_stage("expect", {"expected_outcome": expected_outcome})

    alignment, gaps = _compare_delivery(
        expected_outcome=expected_outcome,
        speak_body=speak_body,
        focus_artifact=focus,
        decision_object=decision or None,
    )
    if memory.get("retrieved_cues") and not speak_body:
        gaps.append("memory_cues_not_yet_applied")

    session.start_stage(
        "compare",
        {"expected_outcome": expected_outcome, "speak_body_len": len(speak_body)},
    )
    session.end_stage("compare", {"alignment": alignment, "gaps": gaps})

    learnings: list[str] = []
    if "focus_not_reflected_in_delivery" in gaps:
        learnings.append("Surface primary focus earlier in the reply.")
    if "decision_not_reflected_in_delivery" in gaps:
        learnings.append("State the chosen option explicitly before rationale.")
    if "memory_cues_not_yet_applied" in gaps:
        learnings.append("Weave retrieved continuity cues into the next draft.")
    if not learnings and alignment == "aligned":
        learnings.append("Current lobe alignment is stable for this turn.")

    session.start_stage("learn", {"gaps": gaps})
    session.end_stage("learn", {"learnings": learnings})

    adjustments = list(learnings[:3])
    if not adjustments:
        adjustments = ["Keep current focus and decision framing."]
    next_turn_hints = []
    if focus.get("secondary_focus"):
        next_turn_hints.append(
            f"Watch secondary focus: {', '.join(focus['secondary_focus'][:2])}"
        )
    if decision.get("winning_criteria"):
        next_turn_hints.append(
            f"Prioritize criteria: {', '.join(decision['winning_criteria'][:2])}"
        )
    if memory.get("forgotten_advisory"):
        next_turn_hints.append("Review advisory-forgotten cues if continuity drifts.")

    session.start_stage("adjust", {"adjustment_inputs": learnings})
    session.end_stage("adjust", {"adjustments": adjustments, "next_turn_hints": next_turn_hints})

    reflection_artifact = {
        "expected_outcome": expected_outcome,
        "alignment": alignment,
        "gaps": gaps,
        "adjustments": adjustments,
        "next_turn_hints": next_turn_hints,
        "planning_handoff": should_handoff_to_planning(
            {
                "alignment": alignment,
                "adjustments": adjustments,
                "gaps": gaps,
            }
        ),
    }

    validation = validate_reflection_artifact(reflection_artifact)
    if not validation["valid"]:
        raise ValueError(f"reflection turn invalid: {validation['issues']}")
    turn_validation = session.validate_turn()
    if not turn_validation["valid"]:
        raise ValueError(f"reflection ledger invalid: {turn_validation['issues']}")

    return reflection_artifact, session


def merge_post_reply_reflection(
    reflection_artifact: dict[str, Any],
    *,
    speak_body: str,
    focus_artifact: dict[str, Any] | None = None,
    decision_object: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-compare after the final reply is available."""
    expected = str(reflection_artifact.get("expected_outcome") or "")
    alignment, gaps = _compare_delivery(
        expected_outcome=expected,
        speak_body=speak_body,
        focus_artifact=dict(focus_artifact or {}),
        decision_object=decision_object,
    )
    merged = dict(reflection_artifact)
    merged["alignment"] = alignment
    merged["gaps"] = list(dict.fromkeys(list(reflection_artifact.get("gaps") or []) + gaps))
    if alignment != "aligned":
        adjustment = "Tighten reply to reflect focus and decision in the opening lines."
        merged["adjustments"] = list(dict.fromkeys(list(merged.get("adjustments") or []) + [adjustment]))[:3]
    merged["planning_handoff"] = should_handoff_to_planning(merged)
    return merged
