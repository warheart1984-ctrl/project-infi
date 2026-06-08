"""Narrative Continuity Organ — live posture from narrative continuity runtime."""

# Mythic: Narrative Continuity Organ
# Engineering: NarrativeContinuityEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.narrative_continuity import compare_continuity_treatment_vs_baseline


def build_narrative_continuity_status() -> dict[str, Any]:
    """Read-only continuity posture from live runtime + Nova store."""
    try:
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        posture = narrative_continuity_runtime.narrative_posture()
        snapshot = narrative_continuity_runtime.narrative_snapshot()
        nova = dict(snapshot.get("nova_summary") or {})
        narrative = {
            "active_story": nova.get("active_story"),
            "current_chapter": nova.get("current_chapter"),
            "open_threads": list(nova.get("open_threads") or []),
        }
        comparison = compare_continuity_treatment_vs_baseline(
            narrative,
            arc={"root_goal": nova.get("active_story"), "open_threads": nova.get("open_threads") or []},
            planning={"next_action": nova.get("current_chapter")},
        )
        continuity_score = float(posture.get("continuity_score") or 0.0)
        story_rate = 1.0 if nova.get("active_story") else 0.0
        return {
            "narrative_continuity_organ_version": "narrative_continuity_organ.v1",
            "continuity_score": continuity_score,
            "story_persistence_rate": round(story_rate, 3),
            "continuity_complete": continuity_score >= 1.0,
            "narrative_wins": bool(comparison.get("narrative_wins")),
            "adopted_beats": posture.get("adopted_beats", 0),
            "candidate_beats": posture.get("candidate_beats", 0),
            "identity_aligned": posture.get("identity_aligned", True),
            "cisiv_stage": "implementation",
            "claim_label": str(posture.get("claim_label") or "asserted"),
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "narrative_continuity_organ_version": "narrative_continuity_organ.v1",
            "continuity_score": 0.0,
            "story_persistence_rate": 0.0,
            "continuity_complete": False,
            "narrative_wins": False,
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
