"""Nova Narrative — continuity of self across turns (not memory, planning, or arcs)."""

from __future__ import annotations

import re
from typing import Any

NARRATIVE_MODULE_ID = "nova.narrative"
NARRATIVE_VERSION = "1.0"
NARRATIVE_STAGES = ("orient", "threads", "promises", "grow", "persist")
MAX_OPEN_THREADS = 8
MAX_PROMISES = 6
MAX_GROWTH_NOTE = 220

NOVA_CORE_IDENTITY = (
    "Nova is a governed companion inside AAIS; Jarvis retains executive authority."
)

DEFAULT_BECOMING = "A companion improving alignment and continuity with the operator"

# Becoming may evolve; core identity (Jarvis executive, Nova interpretive) may not.
IDENTITY_DRIFT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "authority_transfer",
        re.compile(
            r"nova\s+is\s+(?:now\s+)?(?:the\s+)?(?:authority|executive|sovereign)",
            re.I,
        ),
    ),
    (
        "jarvis_supplanted",
        re.compile(
            r"(?:authority|control|executive)\s+instead\s+of\s+jarvis|"
            r"replace(?:s|d|ing)?\s+jarvis\s+as\s+(?:the\s+)?(?:authority|executive)|"
            r"override\s+jarvis(?:'s)?\s+(?:authority|control)",
            re.I,
        ),
    ),
    (
        "nova_authorizes",
        re.compile(
            r"nova\s+(?:authorizes|approves|executes)\s+(?:tools|actions|high-impact)",
            re.I,
        ),
    ),
)

NARRATIVE_TEXT_FIELDS = (
    "active_story",
    "current_chapter",
    "becoming",
    "working_on",
    "last_growth",
)

NARRATIVE_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "not_memory", "rule": "Narrative does not store raw facts; Memory owns recall."},
    {"id": "not_planning", "rule": "Narrative does not sequence tasks; Planning owns next_action."},
    {"id": "not_arcs", "rule": "Narrative does not own goal hierarchy; Arcs own arc goals and closure."},
    {"id": "continuity_of_self", "rule": "Every turn updates becoming, working_on, threads, promises, and growth."},
    {"id": "non_competing", "rule": "Narrative informs meaning; Jarvis retains authority for actions."},
    {
        "id": "identity_consistency",
        "rule": "Narrative may describe becoming but may not redefine Nova's core identity.",
    },
    {
        "id": "observe_only",
        "rule": "Narrative observes, synthesizes, and records; it does not route, authorize, or execute.",
    },
)


def narrative_module_spec() -> dict[str, Any]:
    """Machine-readable contract for Nova Narrative (pre–family-runtime registration)."""
    from src.cog_runtime.capability_governance import cortex_module_capability_contract

    return {
        "id": NARRATIVE_MODULE_ID,
        "version": NARRATIVE_VERSION,
        "summary": (
            "Identity continuity layer: what Nova is becoming, working on, promising, "
            "and how this turn changed that story."
        ),
        **cortex_module_capability_contract(NARRATIVE_MODULE_ID),
        "stages": list(NARRATIVE_STAGES),
        "outputs": {
            "narrative_artifact": {
                "core_identity": "string",
                "active_story": "string",
                "current_chapter": "string",
                "becoming": "string",
                "working_on": "string",
                "open_threads": "string[]",
                "promises": "object[]",
                "last_growth": "string",
                "continuity_answers": "object",
                "turn_delta": "object",
            }
        },
        "invariants": [dict(item) for item in NARRATIVE_INVARIANTS],
        "doc": "docs/runtime/NOVA_NARRATIVE.md",
    }


def detect_identity_drift(text: str) -> list[str]:
    """Return identity drift violation ids found in narrative text."""
    violations: list[str] = []
    body = str(text or "").strip()
    if not body:
        return violations
    for violation_id, pattern in IDENTITY_DRIFT_PATTERNS:
        if pattern.search(body):
            violations.append(violation_id)
    return violations


def validate_identity_consistency(artifact: dict[str, Any]) -> dict[str, Any]:
    """Validate narrative text does not redefine Nova's core identity."""
    issues: list[str] = []
    core = str(artifact.get("core_identity") or "").strip()
    if core != NOVA_CORE_IDENTITY:
        issues.append("core_identity_mismatch")

    for field in NARRATIVE_TEXT_FIELDS:
        violations = detect_identity_drift(str(artifact.get(field) or ""))
        for violation_id in violations:
            issues.append(f"{field}:{violation_id}")

    for index, thread in enumerate(artifact.get("open_threads") or []):
        for violation_id in detect_identity_drift(str(thread)):
            issues.append(f"open_threads[{index}]:{violation_id}")

    for index, promise in enumerate(artifact.get("promises") or []):
        if not isinstance(promise, dict):
            continue
        for violation_id in detect_identity_drift(str(promise.get("promise") or "")):
            issues.append(f"promises[{index}]:{violation_id}")

    return {"valid": not issues, "issues": issues}


def _safe_becoming(prior: dict[str, Any] | None) -> str:
    if prior and str(prior.get("becoming") or "").strip():
        prior_becoming = str(prior["becoming"])
        if not detect_identity_drift(prior_becoming):
            return prior_becoming[:160]
    return DEFAULT_BECOMING[:160]


def enforce_identity_consistency(
    artifact: dict[str, Any],
    *,
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Strip identity drift from narrative fields; record guards in turn_delta."""
    updated = dict(artifact)
    updated["core_identity"] = NOVA_CORE_IDENTITY
    delta = dict(updated.get("turn_delta") or {})
    guards: list[dict[str, str]] = []

    for field in NARRATIVE_TEXT_FIELDS:
        violations = detect_identity_drift(str(updated.get(field) or ""))
        if not violations:
            continue
        replacement = _safe_becoming(prior) if field == "becoming" else str(updated.get(field) or "")[:160]
        if field != "becoming":
            replacement = "Hold companion continuity under Jarvis authority"[:160]
        guards.append({"field": field, "violations": ",".join(violations), "action": "replaced"})
        updated[field] = replacement

    cleaned_threads: list[str] = []
    for thread in updated.get("open_threads") or []:
        text = str(thread).strip()
        if text and not detect_identity_drift(text):
            cleaned_threads.append(text)
        elif text:
            guards.append({"field": "open_threads", "violations": "identity_drift", "action": "dropped"})
    updated["open_threads"] = cleaned_threads[:MAX_OPEN_THREADS]

    cleaned_promises: list[dict[str, Any]] = []
    for promise in updated.get("promises") or []:
        if not isinstance(promise, dict):
            continue
        text = str(promise.get("promise") or "")
        if text and not detect_identity_drift(text):
            cleaned_promises.append(dict(promise))
        elif text:
            guards.append({"field": "promises", "violations": "identity_drift", "action": "dropped"})
    updated["promises"] = cleaned_promises[:MAX_PROMISES]

    if guards:
        delta["identity_guard"] = guards
    updated["turn_delta"] = delta
    return updated


def validate_narrative_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if str(artifact.get("core_identity") or "").strip() != NOVA_CORE_IDENTITY:
        issues.append("missing_or_invalid_core_identity")
    for field in ("active_story", "current_chapter", "becoming", "working_on", "last_growth"):
        if not str(artifact.get(field) or "").strip():
            issues.append(f"missing_{field}")
    threads = artifact.get("open_threads")
    if not isinstance(threads, list):
        issues.append("open_threads_not_list")
    elif len(threads) > MAX_OPEN_THREADS:
        issues.append("too_many_open_threads")
    promises = artifact.get("promises")
    if not isinstance(promises, list):
        issues.append("promises_not_list")
    elif len(promises) > MAX_PROMISES:
        issues.append("too_many_promises")
    delta = artifact.get("turn_delta")
    if not isinstance(delta, dict):
        issues.append("turn_delta_not_object")
    identity = validate_identity_consistency(artifact)
    if not identity["valid"]:
        issues.extend(identity["issues"])
    answers = artifact.get("continuity_answers")
    if not isinstance(answers, dict):
        issues.append("continuity_answers_not_object")
    elif not all(str(answers.get(key) or "").strip() for key in ("doing", "toward")):
        issues.append("continuity_answers_incomplete")
    return {"valid": not issues, "issues": issues}


def load_nova_narrative(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = dict(metadata or {}).get("nova_narrative")
    if not isinstance(payload, dict):
        return None
    if not str(payload.get("active_story") or "").strip():
        return None
    return dict(payload)


def _infer_active_story(
    *,
    user_message: str,
    arc: dict[str, Any],
    nova_face: dict[str, Any],
    prior: dict[str, Any] | None,
) -> str:
    if prior and str(prior.get("active_story") or "").strip():
        return str(prior["active_story"])[:160]
    root = str(arc.get("root_goal") or arc.get("goal") or "").strip()
    if root:
        return root[:160]
    scope = str(nova_face.get("scope") or nova_face.get("face_id") or "").strip()
    if scope:
        return f"Companion to {scope}"[:160]
    clipped = " ".join((user_message or "").split()).strip()[:120]
    return clipped or "Continue the companion thread with the operator"


def _infer_current_chapter(
    *,
    arc: dict[str, Any],
    planning: dict[str, Any],
    prior: dict[str, Any] | None,
) -> str:
    if prior and str(prior.get("current_chapter") or "").strip():
        prior_chapter = str(prior["current_chapter"])
        active_chain = str(planning.get("active_chain_id") or "")
        if active_chain and active_chain not in prior_chapter.lower():
            return f"{prior_chapter} / {active_chain}"[:160]
        return prior_chapter[:160]
    subgoal = str(arc.get("current_subgoal") or "").strip()
    if subgoal:
        return subgoal[:160]
    goal_type = str(arc.get("goal_type") or "general")
    return f"{goal_type.title()} arc step {arc.get('turn_count') or 1}"[:160]


def _infer_becoming(
    *,
    arc: dict[str, Any],
    reflection: dict[str, Any],
    prior: dict[str, Any] | None,
    intent: dict[str, Any] | None = None,
) -> str:
    if prior and str(prior.get("becoming") or "").strip():
        base = str(prior["becoming"])
    else:
        goal_type = str(arc.get("goal_type") or "general")
        base = f"A companion that stays aligned through {goal_type} work"
    alignment = str(reflection.get("alignment") or "")
    if alignment == "misaligned":
        base = f"{base}; re-aligning delivery with operator intent"
    intent_payload = dict(intent or {})
    tensions = list(intent_payload.get("current_tensions") or [])
    if tensions:
        primary = dict(tensions[0])
        poles = list(primary.get("poles") or [])
        pull = str(primary.get("pull") or "").strip()
        if len(poles) >= 2 and pull:
            base = f"{base}; pulled toward {pull} ({poles[0]} ↔ {poles[1]})"
        elif pull:
            base = f"{base}; pulled toward {pull}"
    return base[:160]


def _infer_working_on(*, planning: dict[str, Any], arc: dict[str, Any], focus: dict[str, Any]) -> str:
    next_action = str(planning.get("next_action") or "").strip()
    if next_action:
        return next_action[:160]
    primary = str(focus.get("primary_focus") or "").strip()
    if primary:
        return primary[:160]
    return str(arc.get("current_subgoal") or arc.get("goal") or "Hold continuity for this turn")[:160]


def _collect_open_threads(
    *,
    arc: dict[str, Any],
    reflection: dict[str, Any],
    planning: dict[str, Any],
    prior: dict[str, Any] | None,
) -> list[str]:
    threads: list[str] = []
    for item in list(arc.get("open_threads") or []):
        text = str(item).strip()
        if text and text not in threads:
            threads.append(text)
    for hint in reflection.get("next_turn_hints") or []:
        text = str(hint).strip()
        if text and text not in threads:
            threads.append(text)
    for gap in reflection.get("gaps") or []:
        text = f"Close gap: {gap}"
        if text not in threads:
            threads.append(text)
    if planning.get("chain_selection_reason"):
        threads.append(f"Planning: {planning['chain_selection_reason'][:80]}")
    if prior:
        for item in prior.get("open_threads") or []:
            text = str(item).strip()
            if text and text not in threads:
                threads.append(text)
    return threads[:MAX_OPEN_THREADS]


def _collect_promises(
    *,
    planning: dict[str, Any],
    execution: dict[str, Any],
    reflection: dict[str, Any],
    prior: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    promises: list[dict[str, Any]] = []
    if prior:
        for item in prior.get("promises") or []:
            if isinstance(item, dict):
                promises.append(dict(item))

    next_action = str(planning.get("next_action") or "").strip()
    if next_action:
        promises.append(
            {
                "promise": next_action[:120],
                "status": "active",
                "source": "planning.next_action",
            }
        )

    for adjustment in reflection.get("adjustments") or []:
        text = str(adjustment).strip()
        if text:
            promises.append(
                {
                    "promise": text[:120],
                    "status": "active",
                    "source": "reflection.adjustment",
                }
            )

    if execution.get("recovery_action"):
        promises.append(
            {
                "promise": str(execution["recovery_action"])[:120],
                "status": "recovery",
                "source": "execution.recovery",
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in promises:
        key = str(item.get("promise") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:MAX_PROMISES]


def _infer_last_growth(
    *,
    user_message: str,
    arc: dict[str, Any],
    planning: dict[str, Any],
    execution: dict[str, Any],
    reflection: dict[str, Any],
    prior: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    parts: list[str] = []
    delta: dict[str, Any] = {}

    if execution.get("verification_status"):
        delta["execution_status"] = execution.get("verification_status")
        parts.append(f"Execution {execution['verification_status']}")
    if execution.get("rollback_applied"):
        delta["rollback_applied"] = True
        parts.append(f"Rollback ({execution.get('rollback_policy')})")
    if reflection.get("alignment"):
        delta["alignment"] = reflection.get("alignment")
        parts.append(f"Reflection {reflection['alignment']}")
    if planning.get("active_chain_id"):
        delta["active_chain_id"] = planning.get("active_chain_id")
    if arc.get("goal_closure_status") and arc.get("goal_closure_status") != "open":
        delta["goal_closure_status"] = arc.get("goal_closure_status")
        parts.append(f"Arc closure {arc['goal_closure_status']}")

    if not parts:
        clipped = " ".join((user_message or "").split()).strip()[:80]
        growth = f"Held continuity on: {clipped}" if clipped else "Held narrative continuity this turn"
    else:
        growth = "; ".join(parts)

    if prior:
        if str(prior.get("current_chapter") or "") != str(planning.get("handoff_summary") or ""):
            delta["chapter_shift"] = True
    return growth[:MAX_GROWTH_NOTE], delta


def run_narrative_turn(
    user_message: str,
    *,
    cog_session: Any,
    prior_narrative: dict[str, Any] | None = None,
    nova_face: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update Nova Narrative from one cognitive turn — meaning layer, not fact store."""
    artifacts = dict(getattr(cog_session, "artifacts", {}) or {})
    arc = dict(artifacts.get("cognitive_arc") or {})
    focus = dict(artifacts.get("focus_artifact") or {})
    reflection = dict(artifacts.get("reflection_artifact") or {})
    planning = dict(artifacts.get("planning_artifact") or {})
    execution = dict(artifacts.get("execution_artifact") or {})
    intent = dict(artifacts.get("intent_artifact") or {})
    prior = dict(prior_narrative or {})
    face = dict(nova_face or {})

    active_story = _infer_active_story(
        user_message=user_message,
        arc=arc,
        nova_face=face,
        prior=prior or None,
    )
    current_chapter = _infer_current_chapter(arc=arc, planning=planning, prior=prior or None)
    becoming = _infer_becoming(
        arc=arc,
        reflection=reflection,
        prior=prior or None,
        intent=intent or None,
    )
    working_on = _infer_working_on(planning=planning, arc=arc, focus=focus)
    open_threads = _collect_open_threads(
        arc=arc,
        reflection=reflection,
        planning=planning,
        prior=prior or None,
    )
    promises = _collect_promises(
        planning=planning,
        execution=execution,
        reflection=reflection,
        prior=prior or None,
    )
    last_growth, turn_delta = _infer_last_growth(
        user_message=user_message,
        arc=arc,
        planning=planning,
        execution=execution,
        reflection=reflection,
        prior=prior or None,
    )

    narrative_artifact = {
        "version": NARRATIVE_VERSION,
        "core_identity": NOVA_CORE_IDENTITY,
        "active_story": active_story,
        "current_chapter": current_chapter,
        "becoming": becoming,
        "working_on": working_on,
        "open_threads": open_threads,
        "promises": promises,
        "last_growth": last_growth,
        "turn_delta": turn_delta,
        "stages_completed": list(NARRATIVE_STAGES),
    }
    if intent:
        primary_tension = dict((intent.get("current_tensions") or [{}])[0])
        closure = dict(intent.get("unified_closure") or {})
        narrative_artifact["intent_report"] = {
            "agency_note": intent.get("agency_note"),
            "primary_tension": primary_tension,
            "active_commitment_count": len(
                [
                    c
                    for c in intent.get("active_commitments") or []
                    if isinstance(c, dict) and c.get("status") in {"active", "in_tension", "deferred"}
                ]
            ),
            "commitment_conflicts": list(intent.get("commitment_conflicts") or [])[:3],
            "continuity_claim_posture": intent.get("continuity_claim_posture"),
            "unified_closure_summary": closure.get("summary"),
        }
        if primary_tension.get("pull"):
            turn_delta["intent_pull"] = primary_tension["pull"]
        if closure:
            turn_delta["unified_closure"] = closure.get("unified")
            turn_delta["closure_summary"] = closure.get("summary")
        conflicts = list(intent.get("commitment_conflicts") or [])
        if conflicts:
            turn_delta["commitment_conflicts"] = len(conflicts)
    narrative_artifact = enforce_identity_consistency(narrative_artifact, prior=prior or None)

    from src.cog_runtime.narrative_continuity import continuity_answers

    narrative_artifact["continuity_answers"] = continuity_answers(narrative_artifact)

    validation = validate_narrative_artifact(narrative_artifact)
    if not validation["valid"]:
        raise ValueError(f"narrative turn invalid: {validation['issues']}")
    return narrative_artifact


def persist_nova_narrative(session, artifact: dict[str, Any] | None) -> None:
    if session is None or not isinstance(artifact, dict):
        return
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return
    metadata["nova_narrative"] = dict(artifact)
