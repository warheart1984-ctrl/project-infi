"""Nova Coherence Projection — read-only cortex state for provider generation."""

# Mythic: Coherence Projection Organ
# Engineering: CoherenceProjectionLayer
from __future__ import annotations

import json
from typing import Any

PROJECTION_VERSION = "1.0"
PROJECTION_DOC = "docs/runtime/NOVA_COHERENCE_PROJECTION.md"
MAX_COMMITMENTS = 4
MAX_TENSIONS = 3
MAX_FIELD_LEN = 220


def _clip(value: Any, limit: int = MAX_FIELD_LEN) -> str:
    return str(value or "").strip()[:limit]


def _summarize_commitments(items: list[Any] | None) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for item in list(items or [])[:MAX_COMMITMENTS]:
        if not isinstance(item, dict):
            continue
        summary.append(
            {
                "commitment": _clip(item.get("commitment"), 160),
                "status": _clip(item.get("status"), 32),
                "claim_posture": _clip(item.get("claim_posture"), 16),
            }
        )
    return summary


def _summarize_tensions(items: list[Any] | None) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for item in list(items or [])[:MAX_TENSIONS]:
        if not isinstance(item, dict):
            continue
        poles = list(item.get("poles") or [])
        summary.append(
            {
                "poles": " ↔ ".join(str(pole) for pole in poles[:2]),
                "pull": _clip(item.get("pull"), 32),
            }
        )
    return summary


def _summarize_deliberation(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = dict(decision or {})
    if not payload.get("chosen_option"):
        return None
    return {
        "chosen_option": _clip(payload.get("chosen_option"), 160),
        "rationale": _clip(payload.get("rationale"), 160),
        "options": [ _clip(item, 80) for item in list(payload.get("options") or [])[:4] ],
        "commit_source": _clip(payload.get("commit_source"), 32),
    }


def build_coherence_projection_from_cortex(cortex_state: dict[str, Any] | None) -> dict[str, Any] | None:
    """Export bounded read-only cognitive state for the LLM renderer (Spark CPL)."""
    state = dict(cortex_state or {})
    artifacts = dict(state.get("artifacts") or {})
    focus = dict(artifacts.get("focus_artifact") or state.get("focus_artifact") or {})
    intent = dict(state.get("intent_summary") or artifacts.get("intent_artifact") or {})
    narrative = dict(state.get("narrative_frame") or artifacts.get("narrative_artifact") or {})
    memory_cues = list(state.get("memory_cues") or [])
    deliberation = _summarize_deliberation(
        dict(state.get("delib_summary") or artifacts.get("decision_object") or {})
    )

    if not any([focus, intent, narrative, memory_cues, deliberation]):
        return None

    return {
        "projection_version": PROJECTION_VERSION,
        "read_only": True,
        "instruction": (
            "Speak from this cognitive state. Jarvis retains executive authority. "
            "Do not expose module names, ledger stages, or chain-of-thought."
        ),
        "focus": {
            "primary_focus": _clip(focus.get("primary_focus")),
            "secondary_focus": _clip(focus.get("secondary_focus")),
            "focus_signals": list(focus.get("focus_signals") or [])[:6],
        }
        if focus
        else None,
        "intent": {
            "agency_note": _clip(intent.get("agency_note")),
            "active_tensions": _summarize_tensions(intent.get("current_tensions")),
            "active_commitments": _summarize_commitments(intent.get("active_commitments")),
            "continuity_claim_posture": _clip(intent.get("continuity_claim_posture"), 16),
        }
        if intent
        else None,
        "narrative": {
            "active_story": _clip(narrative.get("active_story")),
            "becoming": _clip(narrative.get("becoming")),
            "working_on": _clip(narrative.get("working_on")),
            "current_chapter": _clip(narrative.get("current_chapter")),
        }
        if narrative
        else None,
        "memory_cues": [
            _clip(_memory_cue_text(cue), 160)
            for cue in memory_cues[:5]
        ],
        "deliberation": deliberation,
        "cognition": {
            "primary_focus": _clip(focus.get("primary_focus")),
            "decision": deliberation,
            "next_action": _clip(dict(artifacts.get("planning_artifact") or {}).get("next_action"), 160) or None,
        }
        if any([focus, deliberation, artifacts.get("planning_artifact")])
        else None,
    }


def _memory_cue_text(cue: Any) -> str:
    if isinstance(cue, dict):
        for key in ("text", "content", "summary", "insight", "excerpt"):
            value = str(cue.get(key) or "").strip()
            if value:
                return value
    return str(cue or "").strip()


def build_coherence_projection(session_metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build bounded read-only projection from session metadata after Nova Cortex runs."""
    metadata = dict(session_metadata or {})
    if not metadata.get("cognitive_runtime_enabled"):
        return None

    stored = dict(metadata.get("coherence_projection") or {})
    if stored.get("projection_version"):
        return stored

    from_cortex = build_coherence_projection_from_cortex(_cortex_state_from_metadata(metadata))
    if from_cortex is not None:
        return from_cortex

    intent = dict(metadata.get("nova_intent") or {})
    narrative = dict(metadata.get("nova_narrative") or {})
    arc = dict(metadata.get("cortex_arc") or {})
    artifacts = dict(metadata.get("cognitive_runtime_artifacts") or {})
    if not artifacts:
        stored = dict(metadata.get("nova_cognitive_session") or {})
        artifacts = dict(stored.get("artifacts") or {})

    decision = dict(artifacts.get("decision_object") or {})
    planning = dict(artifacts.get("planning_artifact") or {})
    focus = dict(artifacts.get("focus_artifact") or {})
    execution = dict(artifacts.get("execution_artifact") or {})

    if not any([intent, narrative, arc, decision, planning, focus]):
        return None

    projection = {
        "projection_version": PROJECTION_VERSION,
        "read_only": True,
        "instruction": (
            "Speak from this cognitive state. Jarvis retains executive authority. "
            "Do not expose module names, ledger stages, or chain-of-thought."
        ),
        "intent": {
            "agency_note": _clip(intent.get("agency_note")),
            "active_tensions": _summarize_tensions(intent.get("current_tensions")),
            "active_commitments": _summarize_commitments(intent.get("active_commitments")),
            "continuity_claim_posture": _clip(intent.get("continuity_claim_posture"), 16),
            "long_horizon_goal": _clip(
                (intent.get("long_horizon_goals") or [{}])[0].get("goal")
                if isinstance((intent.get("long_horizon_goals") or [None])[0], dict)
                else (intent.get("long_horizon_goals") or [""])[0]
            ),
        },
        "narrative": {
            "active_story": _clip(narrative.get("active_story")),
            "becoming": _clip(narrative.get("becoming")),
            "working_on": _clip(narrative.get("working_on")),
            "current_chapter": _clip(narrative.get("current_chapter")),
        },
        "cognition": {
            "primary_focus": _clip(focus.get("primary_focus")),
            "decision": {
                "chosen_option": _clip(decision.get("chosen_option"), 160),
                "rationale": _clip(decision.get("rationale"), 160),
            }
            if decision.get("chosen_option")
            else None,
            "next_action": _clip(planning.get("next_action"), 160),
            "arc": {
                "root_goal": _clip(arc.get("root_goal") or arc.get("goal")),
                "goal_type": _clip(arc.get("goal_type"), 32),
                "turn_count": arc.get("turn_count"),
            },
            "execution_status": _clip(
                execution.get("verification_status") or execution.get("status"), 32
            )
            if execution
            else None,
        },
    }
    return projection


def _cortex_state_from_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    stored = dict(metadata.get("nova_cognitive_session") or {})
    artifacts = dict(metadata.get("cognitive_runtime_artifacts") or stored.get("artifacts") or {})
    return {
        "artifacts": artifacts,
        "memory_cues": metadata.get("cortex_memory_cues") or [],
        "intent_summary": dict(metadata.get("nova_intent") or artifacts.get("intent_artifact") or {}),
        "narrative_frame": dict(metadata.get("nova_narrative") or artifacts.get("narrative_artifact") or {}),
        "focus_artifact": artifacts.get("focus_artifact"),
        "delib_summary": artifacts.get("decision_object"),
    }


def format_coherence_projection_block(projection: dict[str, Any] | None) -> str:
    """Render projection as compact JSON for one provider system module."""
    if not isinstance(projection, dict):
        return ""
    payload = dict(projection)
    instruction = str(payload.pop("instruction", "") or "").strip()
    body = json.dumps(payload, indent=2, sort_keys=True)
    if instruction:
        return f"{instruction}\n\n{body}"
    return body


def coherence_projection_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Alias for modular pipeline metadata dicts."""
    return build_coherence_projection(metadata)
