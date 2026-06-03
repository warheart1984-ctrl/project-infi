"""Narrative Continuity Organ — read-only Nova continuity metrics snapshot."""

# Mythic: Narrative Continuity Organ
# Engineering: NarrativeContinuityEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.narrative import NOVA_CORE_IDENTITY
from src.cog_runtime.narrative_continuity import (
    compare_continuity_treatment_vs_baseline,
    score_continuity_completeness,
)
from src.cog_runtime.narrative_continuity_evidence import run_narrative_continuity_fixture


def _fixture_narrative() -> dict[str, Any]:
    return {
        "core_identity": NOVA_CORE_IDENTITY,
        "active_story": "Helping forge Wolf Cog OS",
        "current_chapter": "Nova Cortex Development",
        "becoming": "improving long-term continuity",
        "working_on": "Cross-machine proof",
        "open_threads": ["Unified memory path"],
        "promises": [{"promise": "Ship continuity evidence", "status": "active"}],
        "last_growth": "Composed turns integrated into Jarvis",
    }


def build_narrative_continuity_status() -> dict[str, Any]:
    """Read-only continuity posture from proven fixtures."""
    narrative = _fixture_narrative()
    prior = dict(narrative)
    next_narrative = dict(narrative)
    completeness = score_continuity_completeness(narrative)
    fixture = run_narrative_continuity_fixture(
        prior_narrative=prior,
        next_narrative=next_narrative,
    )
    comparison = compare_continuity_treatment_vs_baseline(
        narrative,
        arc={"root_goal": "Helping forge Wolf Cog OS", "open_threads": ["proof"]},
        planning={"next_action": "Cross-machine proof"},
    )
    chapter = fixture.get("chapter_coherence") or {}
    story_rate = 1.0 if chapter.get("story_held") else float(chapter.get("rate") or 0.0)
    claim = str(fixture.get("claim_label") or "asserted")
    return {
        "narrative_continuity_organ_version": "narrative_continuity_organ.v1",
        "continuity_score": float(completeness.get("score") or 0.0),
        "story_persistence_rate": round(story_rate, 3),
        "continuity_complete": bool(completeness.get("complete")),
        "narrative_wins": bool(comparison.get("narrative_wins")),
        "cisiv_stage": "implementation",
        "claim_label": claim if claim in {"asserted", "proven", "rejected"} else "asserted",
        "read_only": True,
    }
