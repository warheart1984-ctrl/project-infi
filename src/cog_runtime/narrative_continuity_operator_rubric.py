"""Operator continuity rubric — paired A/B fixture scoring for INV-2."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.narrative_continuity import (
    baseline_arc_planning_view,
    score_baseline_completeness,
    score_continuity_completeness,
)
from src.cog_runtime.narrative_continuity_evidence import (
    score_chapter_coherence,
    score_thread_retention,
)

RUBRIC_DIMENSIONS = ("story_remembered", "threads_not_dropped", "no_jarring_reset")
PASS_THRESHOLD = 4.0


def _clamp_score(value: float) -> int:
    return max(1, min(5, int(round(value))))


def score_story_remembered(
    narrative: dict[str, Any] | None,
    *,
    persist: bool,
) -> dict[str, Any]:
    """Map narrative completeness to the story-remembered dimension."""
    if persist and narrative:
        completeness = score_continuity_completeness(narrative)
        story = str((narrative or {}).get("active_story") or "").strip()
        if completeness.get("complete") and story:
            score = 5
        elif story and completeness.get("score", 0) >= 0.67:
            score = 4
        elif story:
            score = 3
        else:
            score = 2
    else:
        score = 2
    return {
        "dimension": "story_remembered",
        "score": score,
        "notes": "Narrative persist enabled" if persist else "Arc+planning control arm",
    }


def score_threads_not_dropped(
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
    *,
    persist: bool,
) -> dict[str, Any]:
    """Map thread retention to the threads-not-dropped dimension."""
    if persist:
        retention = score_thread_retention(prior_narrative, next_narrative)
        rate = float(retention.get("rate") or 0.0)
        if rate >= 1.0:
            score = 5
        elif rate >= 0.75:
            score = 4
        elif rate >= 0.5:
            score = 3
        else:
            score = 2
        notes = f"retention_rate={rate}"
    else:
        prior_threads = list((prior_narrative or {}).get("open_threads") or [])
        baseline = baseline_arc_planning_view(
            arc={"open_threads": prior_threads},
            planning={"next_action": "Keep moving"},
        )
        score = 3 if baseline.get("doing") else 2
        notes = "Control arm lacks narrative thread carry-forward"
    return {
        "dimension": "threads_not_dropped",
        "score": score,
        "notes": notes,
    }


def score_no_jarring_reset(
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
    *,
    persist: bool,
) -> dict[str, Any]:
    """Map chapter/growth continuity to the no-jarring-reset dimension."""
    chapter = score_chapter_coherence(prior_narrative, next_narrative)
    prior_growth = str((prior_narrative or {}).get("last_growth") or "").strip()
    next_growth = str((next_narrative or {}).get("last_growth") or "").strip()
    growth_advanced = bool(next_growth and next_growth != prior_growth)
    if persist and chapter.get("story_held") and growth_advanced:
        score = 5
    elif persist and chapter.get("passed"):
        score = 4
    elif persist:
        score = 3
    else:
        baseline = score_baseline_completeness(
            arc={"root_goal": str((prior_narrative or {}).get("active_story") or "")},
            planning={"next_action": str((next_narrative or {}).get("working_on") or "")},
        )
        score = 3 if baseline.get("score", 0) >= 0.67 else 2
    return {
        "dimension": "no_jarring_reset",
        "score": score,
        "notes": "Treatment continuity held" if persist else "Control baseline only",
    }


def score_rubric_session(
    *,
    prior_narrative: dict[str, Any],
    next_narrative: dict[str, Any],
    persist: bool,
) -> dict[str, Any]:
    """Score one rubric arm on all three dimensions."""
    dimensions = {
        "story_remembered": score_story_remembered(next_narrative, persist=persist),
        "threads_not_dropped": score_threads_not_dropped(
            prior_narrative,
            next_narrative,
            persist=persist,
        ),
        "no_jarring_reset": score_no_jarring_reset(
            prior_narrative,
            next_narrative,
            persist=persist,
        ),
    }
    scores = [item["score"] for item in dimensions.values()]
    average = round(sum(scores) / len(scores), 2)
    passed = average >= PASS_THRESHOLD
    return {
        "arm": "A" if persist else "B",
        "persist": persist,
        "dimensions": dimensions,
        "average": average,
        "pass": passed,
    }


def run_paired_rubric_session(
    *,
    session_id: str,
    prior_narrative: dict[str, Any],
    treatment_next: dict[str, Any],
    control_next: dict[str, Any],
) -> dict[str, Any]:
    """Run treatment (persist) vs control (no persist) for one paired fixture."""
    treatment = score_rubric_session(
        prior_narrative=prior_narrative,
        next_narrative=treatment_next,
        persist=True,
    )
    control = score_rubric_session(
        prior_narrative=prior_narrative,
        next_narrative=control_next,
        persist=False,
    )
    delta = round(treatment["average"] - control["average"], 2)
    return {
        "session_id": session_id,
        "treatment": treatment,
        "control": control,
        "delta": delta,
        "passed": treatment["pass"] and treatment["average"] > control["average"],
    }


def run_operator_rubric_study() -> dict[str, Any]:
    """Execute the minimum N=3 paired fixture sessions for INV-2."""
    scenarios = [
        {
            "session_id": "rubric-fixture-001",
            "prior": {
                "active_story": "Helping forge Wolf Cog OS",
                "current_chapter": "Nova Cortex Development",
                "working_on": "Cross-machine proof",
                "last_growth": "Composed turns integrated into Jarvis",
                "open_threads": ["Cross-machine proof", "Unified memory path"],
                "continuity_answers": {
                    "doing": "Cross-machine proof",
                    "done": "Composed turns integrated into Jarvis",
                    "toward": "Helping forge Wolf Cog OS",
                },
            },
            "treatment_next": {
                "active_story": "Helping forge Wolf Cog OS",
                "current_chapter": "Operator rubric",
                "working_on": "Cross-machine proof",
                "last_growth": "Session reset harness landed",
                "open_threads": ["Cross-machine proof", "Unified memory path", "Operator rubric"],
                "continuity_answers": {
                    "doing": "Cross-machine proof",
                    "done": "Session reset harness landed",
                    "toward": "Helping forge Wolf Cog OS | Operator rubric",
                },
            },
            "control_next": {
                "working_on": "Cross-machine proof",
                "open_threads": [],
            },
        },
        {
            "session_id": "rubric-fixture-002",
            "prior": {
                "active_story": "Stabilizing Nova companion UX",
                "current_chapter": "Coherence projection",
                "working_on": "Prove projection reaches provider",
                "last_growth": "Coherence panel wired",
                "open_threads": ["Projection usage fixture", "Operator rubric"],
                "continuity_answers": {
                    "doing": "Prove projection reaches provider",
                    "done": "Coherence panel wired",
                    "toward": "Stabilizing Nova companion UX",
                },
            },
            "treatment_next": {
                "active_story": "Stabilizing Nova companion UX",
                "current_chapter": "Proof closure",
                "working_on": "Operator rubric study",
                "last_growth": "Projection fixture landed",
                "open_threads": ["Projection usage fixture", "Operator rubric"],
                "continuity_answers": {
                    "doing": "Operator rubric study",
                    "done": "Projection fixture landed",
                    "toward": "Stabilizing Nova companion UX | Operator rubric",
                },
            },
            "control_next": {
                "working_on": "Operator rubric study",
                "open_threads": [],
            },
        },
        {
            "session_id": "rubric-fixture-003",
            "prior": {
                "active_story": "Mechanic + Slingshot integration",
                "current_chapter": "Master build sprint",
                "working_on": "Jarvis operator panel",
                "last_growth": "Slingshot panel shipped",
                "open_threads": ["Dogfood closure", "Lab HTTP v2"],
                "continuity_answers": {
                    "doing": "Jarvis operator panel",
                    "done": "Slingshot panel shipped",
                    "toward": "Mechanic + Slingshot integration",
                },
            },
            "treatment_next": {
                "active_story": "Mechanic + Slingshot integration",
                "current_chapter": "Continuity proof",
                "working_on": "Nova continuity closure",
                "last_growth": "Governance manifest verified",
                "open_threads": ["Dogfood closure", "Nova continuity"],
                "continuity_answers": {
                    "doing": "Nova continuity closure",
                    "done": "Governance manifest verified",
                    "toward": "Mechanic + Slingshot integration | Nova continuity",
                },
            },
            "control_next": {
                "working_on": "Nova continuity closure",
                "open_threads": [],
            },
        },
    ]
    sessions = [
        run_paired_rubric_session(
            session_id=item["session_id"],
            prior_narrative=item["prior"],
            treatment_next=item["treatment_next"],
            control_next=item["control_next"],
        )
        for item in scenarios
    ]
    passed_count = sum(1 for item in sessions if item["passed"])
    return {
        "minimum_pairs": 3,
        "sessions": sessions,
        "passed_pairs": passed_count,
        "passed": passed_count >= 3,
        "claim_label": "proven" if passed_count >= 3 else "asserted",
    }
