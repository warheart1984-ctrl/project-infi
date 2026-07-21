"""Nova Narrative continuity scoring and A/B proof helpers."""

from __future__ import annotations

from typing import Any

CONTINUITY_QUESTIONS = ("doing", "done", "toward")


def continuity_answers(narrative: dict[str, Any] | None) -> dict[str, str]:
    """Map narrative artifact to the three continuity questions."""
    payload = dict(narrative or {})
    doing = str(payload.get("working_on") or "").strip()
    done = str(payload.get("last_growth") or "").strip()
    toward_parts = [
        str(payload.get("active_story") or "").strip(),
        str(payload.get("becoming") or "").strip(),
    ]
    threads = [str(item).strip() for item in (payload.get("open_threads") or []) if str(item).strip()]
    if threads:
        toward_parts.append(threads[0])
    toward = " | ".join(part for part in toward_parts if part)[:220]
    return {"doing": doing, "done": done, "toward": toward}


def score_continuity_completeness(narrative: dict[str, Any] | None) -> dict[str, Any]:
    """Score whether the three continuity questions are answered."""
    answers = continuity_answers(narrative)
    filled = {key: bool(str(answers.get(key) or "").strip()) for key in CONTINUITY_QUESTIONS}
    score = sum(1 for key in CONTINUITY_QUESTIONS if filled[key]) / len(CONTINUITY_QUESTIONS)
    return {
        "answers": answers,
        "filled": filled,
        "score": round(score, 3),
        "complete": all(filled.values()),
    }


def baseline_arc_planning_view(
    *,
    arc: dict[str, Any] | None,
    planning: dict[str, Any] | None,
) -> dict[str, str]:
    """Simpler substitute without narrative synthesis layer."""
    arc_payload = dict(arc or {})
    planning_payload = dict(planning or {})
    threads = list(arc_payload.get("open_threads") or [])
    return {
        "doing": str(planning_payload.get("next_action") or arc_payload.get("current_subgoal") or ""),
        "done": "",
        "toward": str(arc_payload.get("root_goal") or arc_payload.get("goal") or threads[0] if threads else ""),
    }


def score_baseline_completeness(
    *,
    arc: dict[str, Any] | None,
    planning: dict[str, Any] | None,
) -> dict[str, Any]:
    answers = baseline_arc_planning_view(arc=arc, planning=planning)
    filled = {key: bool(str(answers.get(key) or "").strip()) for key in CONTINUITY_QUESTIONS}
    score = sum(1 for key in CONTINUITY_QUESTIONS if filled[key]) / len(CONTINUITY_QUESTIONS)
    return {
        "answers": answers,
        "filled": filled,
        "score": round(score, 3),
        "complete": all(filled.values()),
    }


def compare_continuity_treatment_vs_baseline(
    narrative: dict[str, Any] | None,
    *,
    arc: dict[str, Any] | None,
    planning: dict[str, Any] | None,
) -> dict[str, Any]:
    """A/B comparison: narrative treatment vs arc+planning baseline."""
    treatment = score_continuity_completeness(narrative)
    baseline = score_baseline_completeness(arc=arc, planning=planning)
    delta = round(treatment["score"] - baseline["score"], 3)
    wins = treatment["score"] >= baseline["score"] and treatment["filled"]["done"] and not baseline["filled"]["done"]
    return {
        "treatment": treatment,
        "baseline": baseline,
        "delta": delta,
        "narrative_wins": wins,
        "passed": wins or (treatment["complete"] and not baseline["complete"]),
    }
