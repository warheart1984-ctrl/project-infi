"""Narrative continuity evidence metrics — multi-turn session-reset fixtures."""

from __future__ import annotations

from typing import Any


def _promise_texts(narrative: dict[str, Any] | None) -> list[str]:
    payload = dict(narrative or {})
    texts: list[str] = []
    for item in payload.get("promises") or []:
        if isinstance(item, dict):
            text = str(item.get("promise") or item.get("text") or "").strip()
        else:
            text = str(item).strip()
        if text:
            texts.append(text)
    return texts


def _thread_texts(narrative: dict[str, Any] | None) -> list[str]:
    payload = dict(narrative or {})
    return [str(item).strip() for item in (payload.get("open_threads") or []) if str(item).strip()]


def score_promise_survival(
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fraction of prior promises still present after a session boundary."""
    prior = _promise_texts(prior_narrative)
    next_set = set(_promise_texts(next_narrative))
    if not prior:
        return {"rate": 1.0, "survived": [], "lost": [], "passed": True}
    survived = [text for text in prior if text in next_set]
    lost = [text for text in prior if text not in next_set]
    rate = round(len(survived) / len(prior), 3)
    return {
        "rate": rate,
        "survived": survived,
        "lost": lost,
        "passed": rate >= 0.5,
    }


def score_chapter_coherence(
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
) -> dict[str, Any]:
    """Story continuity across chapter transitions."""
    prior_story = str((prior_narrative or {}).get("active_story") or "").strip()
    next_story = str((next_narrative or {}).get("active_story") or "").strip()
    prior_chapter = str((prior_narrative or {}).get("current_chapter") or "").strip()
    next_chapter = str((next_narrative or {}).get("current_chapter") or "").strip()
    story_held = bool(prior_story and next_story and prior_story == next_story)
    chapter_progressed = bool(next_chapter and (not prior_chapter or next_chapter != prior_chapter or story_held))
    passed = story_held or (bool(prior_story) and bool(next_story))
    return {
        "story_held": story_held,
        "chapter_progressed": chapter_progressed,
        "prior_story": prior_story,
        "next_story": next_story,
        "passed": passed,
    }


def score_growth_chain(
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
    prior_reflection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Growth markers and thread retention across turns."""
    prior_growth = str((prior_narrative or {}).get("last_growth") or "").strip()
    next_growth = str((next_narrative or {}).get("last_growth") or "").strip()
    prior_threads = set(_thread_texts(prior_narrative))
    next_threads = set(_thread_texts(next_narrative))
    retained = sorted(prior_threads & next_threads) if prior_threads else []
    retention_rate = round(len(retained) / len(prior_threads), 3) if prior_threads else 1.0
    reflection_hint = str((prior_reflection or {}).get("next_turn_hint") or "").strip()
    growth_advanced = bool(next_growth and next_growth != prior_growth)
    passed = retention_rate >= 0.5 or growth_advanced or bool(reflection_hint)
    return {
        "retention_rate": retention_rate,
        "retained_threads": retained,
        "growth_advanced": growth_advanced,
        "passed": passed,
    }


def score_thread_retention(
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
) -> dict[str, Any]:
    prior_threads = _thread_texts(prior_narrative)
    next_set = set(_thread_texts(next_narrative))
    if not prior_threads:
        return {"rate": 1.0, "retained": [], "dropped": [], "passed": True}
    retained = [text for text in prior_threads if text in next_set]
    dropped = [text for text in prior_threads if text not in next_set]
    rate = round(len(retained) / len(prior_threads), 3)
    return {
        "rate": rate,
        "retained": retained,
        "dropped": dropped,
        "passed": rate >= 0.5,
    }


def run_narrative_continuity_fixture(
    *,
    prior_narrative: dict[str, Any],
    next_narrative: dict[str, Any],
    prior_reflection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Single-call fixture evaluation for CI and proof bundles."""
    from src.cog_runtime.narrative_continuity import score_continuity_completeness

    promise = score_promise_survival(prior_narrative, next_narrative)
    chapter = score_chapter_coherence(prior_narrative, next_narrative)
    growth = score_growth_chain(prior_narrative, next_narrative, prior_reflection)
    threads = score_thread_retention(prior_narrative, next_narrative)
    continuity = score_continuity_completeness(next_narrative)
    passed = all(
        item["passed"]
        for item in (promise, chapter, growth, threads)
    ) and continuity.get("complete")
    return {
        "promise_survival": promise,
        "chapter_coherence": chapter,
        "growth_chain": growth,
        "thread_retention": threads,
        "continuity_completeness": continuity,
        "passed": passed,
        "claim_label": "proven" if passed else "asserted",
    }
